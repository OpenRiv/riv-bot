from openai import OpenAI
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import time
from record.utils import validate_audio_file  # 변경: utils에서 가져오기

logger = logging.getLogger('discord')

class TranscriptionProcessor:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("OpenAI Whisper API configuration loaded successfully")

    def transcribe_audio(self, audio_file_path):
        try:
            if not validate_audio_file(audio_file_path):
                raise ValueError(f"Invalid audio file: {audio_file_path}")
            
            logger.info("Starting audio transcription...")

            retry_count = 0
            max_retries = 5
            while retry_count < max_retries:
                try:
                    with open(audio_file_path, "rb") as audio_file:
                        transcript = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="ko"
                        )
                    logger.info(f"Successfully transcribed audio file: {audio_file_path}")
                    return transcript.get('text', '')
                except Exception as e:
                    if "429" in str(e):
                        retry_count += 1
                        wait_time = 2 ** retry_count
                        logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        raise
            raise Exception("Max retries reached for transcription API.")
        except ValueError as ve:
            logger.error(f"Transcription skipped due to invalid file: {ve}")
            raise
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise

    def generate_meeting_minutes(self, transcriptions, meeting_info):
        """
        마크다운 형식의 회의록 생성
        """
        try:
            date = datetime.now().strftime("%Y-%m-%d")

            # 참가자 목록 생성
            participants_list = "\n".join([
                f"- {username} ({user_id})" for user_id, username in meeting_info['participants'].items()
            ])

            # 발화 내용 생성
            transcription_list = "\n".join([
                f"{index + 1} {entry['name']} ({entry['id']}): {entry['text']}"
                for index, entry in enumerate(transcriptions)
            ])

            markdown_content = f"""# 회의록

## 기본 정보
- 일시: {date}
- 회의 제목: {meeting_info['title']}

## 참석자
{participants_list}

## 회의 내용
{transcription_list}

---
*이 회의록은 OpenAI Whisper API를 통해 자동으로 생성되었습니다.*
"""

            logger.info("Successfully generated meeting minutes")
            return markdown_content
        except Exception as e:
            logger.error(f"Error generating meeting minutes: {e}")
            raise

    def process_all_audio(self, audio_data, meeting_info):
        """
        모든 사용자 음성을 처리하고 회의록 생성
        """
        transcriptions = []
        for user_id, audio_stream in audio_data.items():
            temp_audio_file = f"temp_{user_id}.wav"
            with open(temp_audio_file, "wb") as temp_file:
                temp_file.write(audio_stream.file.read())

            try:
                text = self.transcribe_audio(temp_audio_file)
                transcriptions.append({
                    "name": meeting_info["participants"].get(user_id, "Unknown"),
                    "id": user_id,
                    "text": text
                })
            finally:
                if os.path.exists(temp_audio_file):
                    os.remove(temp_audio_file)

        return transcriptions
