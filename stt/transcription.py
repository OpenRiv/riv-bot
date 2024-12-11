# stt/transcription.py

import openai
import logging
from io import BytesIO

logger = logging.getLogger('discord')

class TranscriptionService:
    def __init__(self, api_key):
        openai.api_key = api_key

    async def transcribe_audio(self, audio_bytes):
        try:
            audio_file = BytesIO(audio_bytes)
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            return response['text']
        except Exception as e:
            logger.error(f"Whisper API 호출 중 오류 발생: {e}")
            return None

    def split_audio(self, audio_bytes, max_length=60000):
        """
        오디오 데이터를 Whisper API의 한도에 맞게 분할합니다.
        max_length는 바이트 단위로 설정됩니다. (예: 60,000 바이트)
        """
        for i in range(0, len(audio_bytes), max_length):
            yield audio_bytes[i:i + max_length]
