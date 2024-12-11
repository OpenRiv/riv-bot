import asyncio
import time
from openai import OpenAI, RateLimitError
import logging
from io import BytesIO

logger = logging.getLogger('discord')

class TranscriptionService:
   def __init__(self, api_key):
       self.client = OpenAI(api_key=api_key)
       self.last_request_time = 0
       self.min_request_interval = 120  # 2분으로 증가

   async def transcribe_with_retry(self, audio_bytes, max_retries=3):
       for attempt in range(max_retries):
           try:
               # 요청 간격 확인
               current_time = time.time()
               if current_time - self.last_request_time < self.min_request_interval:
                   wait_time = self.min_request_interval - (current_time - self.last_request_time)
                   logger.info(f"대기 중... {wait_time:.1f}초")
                   await asyncio.sleep(wait_time)

               # 오디오 파일 준비
               audio_file = BytesIO(audio_bytes)
               audio_file.name = "audio.wav"
               
               logger.debug(f"Transcribing audio of size: {len(audio_bytes)} bytes (Attempt {attempt + 1})")

               response = await self.client.audio.transcriptions.create(
                   model="whisper-1",
                   file=audio_file,
                   language="ko"
               )
               
               self.last_request_time = time.time()
               logger.debug(f"Transcription response received: {response}")
               
               if isinstance(response, str):
                   return response
               elif hasattr(response, 'text'):
                   return response.text
               else:
                   logger.error(f"Unexpected response format: {type(response)}")
                   return "❗ 음성 텍스트 변환에 실패했습니다."

           except RateLimitError as e:
               if attempt == max_retries - 1:
                   logger.error(f"Rate limit exceeded after {max_retries} attempts")
                   return "❗ API 할당량 초과로 텍스트 변환에 실패했습니다."
               wait_time = (attempt + 1) * 120  # 2분씩 증가
               logger.info(f"Rate limit hit, waiting {wait_time} seconds...")
               await asyncio.sleep(wait_time)
           except Exception as e:
               logger.error(f"Transcription error: {str(e)}", exc_info=True)
               return "❗ 음성 텍스트 변환에 실패했습니다."

   @staticmethod
   def split_audio(audio_bytes, max_length=5 * 1024 * 1024):  # 5MB로 감소
       """
       오디오 데이터를 더 작은 청크로 분할합니다.
       """
       try:
           total_length = len(audio_bytes)
           logger.debug(f"Total audio size: {total_length / (1024*1024):.2f} MB")
           
           if total_length <= max_length:
               yield audio_bytes
               return
               
           # 청크 개수 계산
           num_chunks = (total_length + max_length - 1) // max_length
           for i in range(num_chunks):
               start = i * max_length
               end = min((i + 1) * max_length, total_length)
               chunk = audio_bytes[start:end]
               logger.debug(f"Created chunk {i+1}/{num_chunks} of size: {len(chunk)} bytes")
               yield chunk
               
       except Exception as e:
           logger.error(f"Error in split_audio: {str(e)}", exc_info=True)
           yield audio_bytes

   async def transcribe_audio(self, audio_bytes):
       try:
           total_length = len(audio_bytes)
           if total_length > 25 * 1024 * 1024:  # 25MB 이상인 경우
               logger.info(f"Audio size ({total_length/(1024*1024):.1f}MB) exceeds limit, splitting...")
               transcripts = []
               for chunk in self.split_audio(audio_bytes):
                   transcript = await self.transcribe_with_retry(chunk)
                   if transcript:
                       transcripts.append(transcript)
               return " ".join(transcripts)
           else:
               return await self.transcribe_with_retry(audio_bytes)
       except Exception as e:
           logger.error(f"Error in transcribe_audio: {str(e)}", exc_info=True)
           return "❗ 음성 텍스트 변환에 실패했습니다."