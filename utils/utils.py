# utils/utils.py

import re
from datetime import datetime
import logging

logger = logging.getLogger('discord')

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
