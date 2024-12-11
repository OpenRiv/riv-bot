# record/file.py

import discord
from discord.sinks import Sink
from io import BytesIO
import logging
from stt.transcription import TranscriptionService
import os
import asyncio

logger = logging.getLogger('discord')

class MySink(Sink):
    def __init__(self):
        super().__init__()
        self.audio_data = {}  # user_id: BytesIO

    def write_to_user(self, user, data):
        if user.id not in self.audio_data:
            self.audio_data[user.id] = BytesIO()
        logger.debug(f"write_to_user called with data type: {type(data)}")
        logger.debug(f"AudioData attributes: {dir(data)}")  # AudioData 객체의 속성 로그

        # AudioData 객체에서 raw PCM 데이터 추출
        if hasattr(data, 'frame_data') and isinstance(data.frame_data, bytes):
            raw_data = data.frame_data
            logger.debug(f"Extracted raw_data of length {len(raw_data)} bytes from data.frame_data")
        elif hasattr(data, 'pcm') and isinstance(data.pcm, bytes):
            raw_data = data.pcm
            logger.debug(f"Extracted raw_data of length {len(raw_data)} bytes from data.pcm")
        elif hasattr(data, 'read') and callable(data.read):
            try:
                raw_data = data.read()
                if isinstance(raw_data, bytes):
                    logger.debug(f"Extracted raw_data of length {len(raw_data)} bytes from data.read()")
                else:
                    logger.error(f"data.read() did not return bytes, got {type(raw_data)}")
                    return
            except Exception as e:
                logger.error(f"Error reading from data: {e}")
                return
        else:
            logger.error(f"Unexpected data format in write_to_user: {type(data)}")
            return

        self.audio_data[user.id].write(raw_data)
        logger.debug(f"Wrote {len(raw_data)} bytes to BytesIO for user_id: {user.id}")

    def get_transcripts(self):
        return self.audio_data

async def filing(sink: Sink, channel: discord.TextChannel, filename, *args):
    try:
        recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
        logger.info(f"회의 참여자: {recorded_users}")

        audio_data = sink.get_transcripts()
        logger.info(f"녹음된 사용자 수: {len(audio_data)}")

        if not audio_data:
            await channel.send("❗ 녹음된 음성이 없습니다.")
            return

        # TranscriptionService 초기화
        transcriber = TranscriptionService(api_key=os.getenv('OPENAI_API_KEY'))

        for user_id, audio_buffer in audio_data.items():
            logger.debug(f"Processing audio for user_id: {user_id}, type: {type(audio_buffer)}")
            if not isinstance(audio_buffer, BytesIO):
                logger.error(f"audio_buffer for user_id {user_id} is not BytesIO, but {type(audio_buffer)}")
                await channel.send(f"❗ 녹음된 음성 데이터 형식 오류 (user: <@{user_id}>).")
                continue

            audio_buffer.seek(0)
            audio_bytes = audio_buffer.read()
            logger.debug(f"Read {len(audio_bytes)} bytes from BytesIO for user_id: {user_id}")

            # Whisper API의 데이터 처리 한도를 고려해 오디오 분할
            transcripts = []
            for chunk in transcriber.split_audio(audio_bytes):
                logger.debug(f"Transcribing chunk of size {len(chunk)} bytes")
                transcript = await transcriber.transcribe_audio(chunk)
                if transcript:
                    transcripts.append(transcript)
                else:
                    transcripts.append("❗ 음성 텍스트 변환에 실패했습니다.")

            # 전체 텍스트 합치기
            full_transcript = "\n".join(transcripts)
            logger.debug(f"Full transcript length for user_id {user_id}: {len(full_transcript)} characters")

            # 텍스트 파일 생성
            text_filename = f"{filename}_{user_id}.txt"
            text_file = discord.File(BytesIO(full_transcript.encode()), filename=text_filename)

            # Discord 채널에 텍스트 파일 전송
            await channel.send(f"**<@{user_id}>의 녹음 텍스트:**", file=text_file)
            logger.info(f"{user_id}의 녹음 텍스트가 전송되었습니다: {text_filename}")

    except Exception as e:
        logger.error(f"filing 함수에서 오류 발생: {e}")
        await channel.send("❗ 녹음 파일 처리 중 오류가 발생했습니다. 관리자에게 문의해주세요.")
