#record/utils.py
import wave
import logging

logger = logging.getLogger('discord')

def validate_audio_file(file_path):
    """
    오디오 파일이 유효한지 확인
    """
    try:
        with wave.open(file_path, 'rb') as wav_file:
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            logger.info(f"Validating audio file: {file_path} - Channels: {channels}, Sample Rate: {sample_rate}")
            return channels > 0 and sample_rate in [16000, 44100, 48000]  # Discord의 48000Hz 추가
    except wave.Error as e:
        logger.error(f"Invalid WAV file: {file_path} - {e}")
        return False
