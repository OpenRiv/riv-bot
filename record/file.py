import re
from datetime import datetime
import logging

logger = logging.getLogger('discord')

# 녹음 파일명
def fileName(title, custom=False):
    """
    회의명을 파일명으로 변환합니다.
    - 불법적인 파일명 문자를 제거
    - 한글과 영어, 숫자, 언더스코어(_)를 허용
    """
    today = datetime.now().strftime("%Y-%m-%d")
    if custom:
        filename = f"{today}_{title}"
    else:
        filename = f"{today}_{title}"
    
    # 소문자로 변환
    filename = filename.lower()
    # 불법적인 파일명 문자 제거 (<, >, :, ", \, |, ?, *)
    filename = re.sub(r'[<>:"\\|?*]', '', filename)
    
    logger.info(f"생성된 파일명: {filename}")
    return filename

import discord
import logging

logger = logging.getLogger('discord')

# 녹음 파일 추출
async def filing(sink: discord.sinks.Sink, channel: discord.TextChannel, filename, *args):
    try:
        recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
        logger.info(f"회의 참여자: {recorded_users}")

        # 녹음 파일 생성
        files = []
        for user_id, audio in sink.audio_data.items():
            try:
                # 사용자 ID를 포함한 파일명으로 생성
                user_filename = f"{filename}.wav"
                file = discord.File(audio.file, user_filename)
                files.append(file)
                logger.info(f"{user_id}의 녹음 파일이 생성되었습니다: {user_filename}")
            except Exception as e:
                logger.error(f"파일 생성 중 오류 발생 for user {user_id}: {e}")

        # 음성 채널에서 봇 연결 해제
        await sink.vc.disconnect()
        logger.info("봇이 음성 채널에서 연결을 해제했습니다.")

        # 녹음 파일 전송
        await channel.send(f"녹음이 완료되었습니다. 회의 참여자: {', '.join(recorded_users)}", files=files)
        logger.info("녹음 파일이 채널에 전송되었습니다.")
    except Exception as e:
        logger.error(f"filing 함수에서 오류 발생: {e}")
        await channel.send("❗ 녹음 파일 생성 중 오류가 발생했습니다. 관리자에게 문의해주세요.")
