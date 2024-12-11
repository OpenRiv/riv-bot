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
        # 바이트 배열을 사용하여 데이터 저장
        self.audio_data = {}
    
    def write_to_user(self, user, data):
        try:
            if user.id not in self.audio_data:
                self.audio_data[user.id] = bytearray()
            
            # 프레임 데이터 추출 및 저장
            if hasattr(data, 'frames'):
                self.audio_data[user.id].extend(data.frames)
            elif hasattr(data, 'data'):
                self.audio_data[user.id].extend(data.data)
            elif isinstance(data, (bytes, bytearray)):
                self.audio_data[user.id].extend(data)
                
            logger.debug(f"Added audio data for user {user.id}: {len(self.audio_data[user.id])} bytes total")
            
        except Exception as e:
            logger.error(f"Error in write_to_user: {e}", exc_info=True)
            
    def get_transcripts(self):
        result = {}
        for user_id, audio_data in self.audio_data.items():
            try:
                # 단일 AudioData 객체에서 bytes 추출
                if isinstance(audio_data, discord.sinks.AudioData):
                    if hasattr(audio_data, 'file'):
                        audio_data.file.seek(0)
                        audio_bytes = audio_data.file.read()
                    elif hasattr(audio_data, 'frame_data'):
                        audio_bytes = audio_data.frame_data
                    elif hasattr(audio_data, 'data'):
                        audio_bytes = audio_data.data
                    else:
                        logger.error(f"Cannot extract audio data from AudioData object for user {user_id}")
                        continue

                    result[user_id] = BytesIO(audio_bytes)
                    logger.debug(f"Processed audio data for user {user_id}: {len(audio_bytes)} bytes")
            except Exception as e:
                logger.error(f"Error processing audio for user {user_id}: {e}", exc_info=True)

        return result

    def cleanup(self):
        """
        녹음 종료 시 정리 작업
        """
        try:
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}", exc_info=True)

async def filing(sink: Sink, channel: discord.TextChannel, filename, *args):
    try:
        recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
        logger.info(f"회의 참여자: {recorded_users}")

        audio_data = sink.get_transcripts()
        logger.info(f"녹음된 사용자 수: {len(audio_data)}")

        if not audio_data:
            await channel.send("❗ 녹음된 음성이 없습니다.")
            return

        transcriber = TranscriptionService(api_key=os.getenv('OPENAI_API_KEY'))

        for user_id, audio_buffer in audio_data.items():
            logger.debug(f"Processing audio for user_id: {user_id}")
            
            # 오디오 바이트 읽기
            audio_bytes = audio_buffer.read()
            logger.debug(f"Read {len(audio_bytes)} bytes for user_id: {user_id}")

            # 음성 파일 저장 및 전송
            audio_filename = f"{filename}_{user_id}.wav"
            audio_file = discord.File(BytesIO(audio_bytes), filename=audio_filename)
            await channel.send(f"**<@{user_id}>의 음성 파일:**", file=audio_file)

            # Whisper API의 데이터 처리 한도를 고려해 오디오 분할
            transcripts = []
            for chunk in transcriber.split_audio(audio_bytes):
                logger.debug(f"Transcribing chunk of size {len(chunk)} bytes")
                transcript = await transcriber.transcribe_audio(chunk)
                if transcript:
                    transcripts.append(transcript)
                else:
                    transcripts.append("❗ 음성 텍스트 변환에 실패했습니다.")

            # 전체 텍스트 합치기 및 전송
            full_transcript = "\n".join(transcripts)
            logger.debug(f"Full transcript length for user_id {user_id}: {len(full_transcript)} characters")

            text_filename = f"{filename}_{user_id}.txt"
            text_file = discord.File(BytesIO(full_transcript.encode()), filename=text_filename)
            await channel.send(f"**<@{user_id}>의 텍스트:**", file=text_file)
            
            logger.info(f"{user_id}의 녹음 파일과 텍스트가 전송되었습니다: {text_filename}")

    except Exception as e:
        logger.error(f"filing 함수에서 오류 발생: {e}", exc_info=True)
        await channel.send("❗ 녹음 파일 처리 중 오류가 발생했습니다. 관리자에게 문의해주세요.")