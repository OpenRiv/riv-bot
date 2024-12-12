import discord
import logging
import os
from datetime import datetime
from transcribe.processor import TranscriptionProcessor

logger = logging.getLogger('discord')
processor = TranscriptionProcessor()

def fileName(title):
    """
    회의명을 파일명으로 변환
    format: YYYY-MM-DD_category
    """
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}_{title}".lower()
    # 불법적인 파일명 문자 제거
    filename = "".join(c for c in filename if c not in '<>:"\\|?*')
    logger.info(f"생성된 파일명: {filename}")
    return filename

async def filing(sink: discord.sinks.Sink, channel: discord.TextChannel, filename):
    """
    사용자별 음성 데이터를 처리하고 회의록 생성
    """
    temp_files = []
    try:
        # 전체 녹음 파일 저장
        combined_file = f"{filename}_full.wav"
        with open(combined_file, "wb") as f:
            sink.write_combined_file(f)
        temp_files.append(combined_file)
        
        # 각 사용자별 녹음 파일 저장
        participants = {
            str(uid): channel.guild.get_member(uid).name 
            for uid in sink.audio_data.keys()
        }
        
        individual_files = {}
        for user_id, audio in sink.audio_data.items():
            user_file = f"{filename}_{participants[str(user_id)]}.wav"
            audio.file.seek(0)  # 파일 포인터 초기화
            with open(user_file, "wb") as f:
                f.write(audio.file.read())
            temp_files.append(user_file)
            individual_files[user_id] = user_file

        # Whisper API로 음성 변환 및 회의록 생성
        transcriptions = []
        for user_id, file_path in individual_files.items():
            try:
                text = processor.transcribe_audio(file_path)
                transcriptions.append({
                    "name": participants[str(user_id)],
                    "id": user_id,
                    "text": text
                })
            except Exception as e:
                logger.error(f"Transcription error for user {user_id}: {e}")
                continue

        if transcriptions:
            meeting_minutes = processor.generate_meeting_minutes(
                transcriptions, 
                {"title": filename, "participants": participants}
            )
            
            minutes_file = f"{filename}_minutes.md"
            with open(minutes_file, "w", encoding="utf-8") as f:
                f.write(meeting_minutes)
            temp_files.append(minutes_file)

        # 모든 파일 전송
        if temp_files:
            await channel.send(
                "📝 회의 자료가 생성되었습니다:", 
                files=[discord.File(f) for f in temp_files]
            )
        else:
            await channel.send("❗ 처리할 수 있는 녹음 파일이 없습니다.")
            
    except Exception as e:
        logger.error(f"Filing error: {e}")
        await channel.send("❗ 파일 처리 중 오류가 발생했습니다.")
    finally:
        # 임시 파일 정리
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"임시 파일 삭제됨: {file_path}")
            except Exception as e:
                logger.error(f"임시 파일 삭제 실패: {file_path} - {e}")