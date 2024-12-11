# record/file.py
import discord
import logging
import os
from datetime import datetime
import re
from transcribe.processor import TranscriptionProcessor

logger = logging.getLogger('discord')
processor = TranscriptionProcessor()

def fileName(title, custom=False):
    """
    회의명을 파일명으로 변환
    format: YYYY-MM-DD_category
    """
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}_{title}"
    
    # 소문자로 변환
    filename = filename.lower()
    # 불법적인 파일명 문자 제거
    filename = re.sub(r'[<>:"\\|?*]', '', filename)
    
    logger.info(f"생성된 파일명: {filename}")
    return filename
async def filing(sink: discord.sinks.Sink, channel: discord.TextChannel, filename, *args):
    temp_wav = f"{filename}.wav"
    minutes_filename = f"{filename}_minutes.md"

    try:
        # 참가자 정보 수집
        participants = {str(uid): channel.guild.get_member(uid).name for uid in sink.audio_data.keys()}
        logger.info(f"회의 참여자: {participants}")

        # 통합 녹음 파일 생성
        with open(temp_wav, 'wb') as f:
            first_audio = next(iter(sink.audio_data.values()))
            f.write(first_audio.file.read())

        # 음성을 텍스트로 변환
        transcription = processor.transcribe_audio(temp_wav)
        logger.info(f"Transcription 결과: {transcription}")

        # 회의록 생성
        meeting_info = {'title': filename, 'participants': participants}
        markdown_content = processor.generate_meeting_minutes(transcription, meeting_info)
        with open(minutes_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Discord 채널로 파일 전송
        files = [discord.File(temp_wav), discord.File(minutes_filename)]
        await channel.send(
            f"회의록 생성 완료. 참여자: {', '.join(participants.values())}",
            files=files
        )

    except Exception as e:
        logger.error(f"filing 함수에서 오류 발생: {e}")
        await channel.send("❗ 파일 처리 중 오류가 발생했습니다. 관리자에게 문의하세요.")
    finally:
        # 임시 파일 삭제
        for temp_file in [temp_wav, minutes_filename]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.info(f"임시 파일 {temp_file}이 삭제되었습니다.")
