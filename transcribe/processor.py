# transcribe/processor.py
from openai import OpenAI
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger('discord')

class TranscriptionProcessor:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        logger.info("OpenAI Whisper API configuration loaded successfully")

    def transcribe_audio(self, audio_file_path):
        """Whisper API를 사용하여 오디오 파일을 텍스트로 변환"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ko"  # 한국어 설정
                )
            
            logger.info(f"Successfully transcribed audio file: {audio_file_path}")
            return transcript.text
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise

    def generate_meeting_minutes(self, transcription, meeting_info):
        """마크다운 형식의 회의록 생성"""
        try:
            date = datetime.now().strftime("%Y-%m-%d")
            
            # 참가자 목록 생성
            participants_list = "\n".join([f"- {username}" for username in meeting_info['participants'].values()])
            
            markdown_content = f"""# 회의록

## 기본 정보
- 일시: {date}
- 회의 제목: {meeting_info['title']}

## 참석자
{participants_list}

## 회의 내용
{transcription}

---
*이 회의록은 OpenAI Whisper API를 통해 자동으로 생성되었습니다.*
"""
            logger.info("Successfully generated meeting minutes")
            return markdown_content
        except Exception as e:
            logger.error(f"Error generating meeting minutes: {e}")
            raise