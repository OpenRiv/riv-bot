# Riv-Bot 🚀

Discord 음성 채널의 대화를 실시간으로 녹음하고, OpenAI의 Whisper API와 GPT-3.5를 활용하여 회의록을 자동으로 생성하는 Discord 봇입니다.


![GitHub Repo stars](https://img.shields.io/github/stars/OpenRiv/riv-bot?style=social)
![GitHub issues](https://img.shields.io/github/issues/OpenRiv/riv-bot)
![GitHub license](https://img.shields.io/github/license/OpenRiv/riv-bot)

Riv-Bot은 Discord 기반의 회의록 자동 작성 및 요약 프로젝트입니다. 이 봇은 음성 채널에서의 대화를 녹음하고, 녹음된 내용을 자동으로 텍스트로 변환한 후, 중요한 내용을 요약하여 제공합니다. 이를 통해 회의의 효율성을 높이고, 회의 후 정리 시간을 절약할 수 있습니다.

## 주요 기능 ✨

- **🎤 음성 녹음 및 전송**
  - Discord 음성 채널에서의 대화를 녹음하고, 자동으로 텍스트로 변환하여 지정된 텍스트 채널에 전송합니다.
  
- **📝 회의명 자동 생성 및 사용자 정의**
  - 날짜와 역할을 기반으로 자동으로 파일명을 생성하거나, 사용자가 직접 회의명을 입력하여 파일명을 설정할 수 있습니다.
  
- **📊 로깅 시스템 강화**
  -  Python의 `logging` 모듈을 도입하여 봇의 동작을 상세히 기록하고, 문제 발생 시 신속하게 원인을 파악할 수 있습니다.
    
- **💬 출력 형태 개선**
  - 메시지의 중복 출력을 방지하고, 하나의 메시지를 단계적으로 수정하여 깔끔하고 직관적인 사용자 인터페이스를 제공합니다.
   
# Riv-Bot Manual 📖

## 목차
1. [설치 가이드](#1-설치-가이드)
2. [개발 환경 설정](#2-개발-환경-설정)
3. [봇 설정 가이드](#3-봇-설정-가이드)
4. [사용자 가이드](#4-사용자-가이드)
5. [개발자 가이드](#5-개발자-가이드)
6. [문제 해결](#6-문제-해결)
7. [기여 가이드](#7-기여-가이드)

## 1. 설치 가이드

### 시스템 요구사항
- Python 3.8 ~ 3.11
- 디스크 여유 공간: 최소 500MB
- RAM: 최소 512MB
- 안정적인 인터넷 연결

### 설치 단계
1. **리포지토리 클론**
   ```bash
   git clone https://github.com/OpenRiv/riv-bot.git
   cd riv-bot
   ```

2. **가상환경 생성**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

## 2. 개발 환경 설정

### 환경 변수 설정
1. `.env` 파일 생성:
   ```env
   DISCORD_BOT_TOKEN=your_token_here
   OPENAI_API_KEY=your_api_key_here
   ```

2. 로깅 설정:
   ```python
   # logging level 조정
   level=logging.DEBUG  # 개발 시
   level=logging.INFO   # 프로덕션 시
   ```

### IDE 설정 (VS Code 기준)
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
```

## 3. 봇 설정 가이드

### Discord Developer Portal 설정
1. [Discord Developer Portal](https://discord.com/developers/applications) 접속
2. "New Application" 클릭
3. Bot 섹션에서:
   - Privileged Gateway Intents 모두 활성화
   - TOKEN 생성 및 복사
4. OAuth2 URL 생성:
   - `bot` scope 선택
   - 필요한 권한 선택:
     - Send Messages
     - Read Message History
     - Connect
     - Speak
     - Use Voice Activity

### 봇 권한 설정
```python
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True
```

## 4. 사용자 가이드

### 기본 명령어
1. **회의 시작**
   ```
   !회의
   ```
   - 음성 채널 접속 필요
   - 카테고리 선택 또는 직접 입력

2. **회의 종료**
   - UI 버튼 클릭
   - 회의록 자동 생성

### 회의록 형식 커스터마이징
`process_recording` 함수의 `markdown_content` 템플릿 수정:
```python
markdown_content = f"""
# 커스텀 제목
## 커스텀 섹션
{custom_content}
"""
```

## 5. 개발자 가이드

### 코드 구조
```
riv-bot/
├── bot/
│   ├── __init__.py
│   └── commands/
├── utils/
│   ├── audio.py
│   └── logger.py
├── services/
│   ├── transcription.py
│   └── summary.py
└── main.py
```

### 주요 클래스 및 함수
1. **CustomSink**
   - 음성 데이터 캡처
   - 타임스탬프 관리
   - 사용자별 데이터 관리

2. **AudioProcessor**
   ```python
   async def process_recording(sink, channel, meeting_title, members, start_time, end_time):
       # 오디오 처리 로직
   ```

3. **발화자 매칭 시스템**
   ```python
   def match_speaker(segment_start, segment_end, speaking_times, threshold=1.0):
       # 발화자 매칭 로직
   ```

## 6. 문제 해결

### 일반적인 문제
1. **봇 응답 없음**
   - 인텐트 설정 확인
   - 토큰 유효성 확인
   - 로그 파일 확인

2. **음성 인식 실패**
   ```python
   # 디버깅을 위한 로그 추가
   logger.debug(f"Audio data size: {len(merged_audio)}")
   logger.debug(f"API response: {response}")
   ```

3. **메모리 문제**
   - 오디오 데이터 청크 크기 조정
   - 불필요한 데이터 정리

### 로그 분석
```python
# 로그 파일 위치: bot.log
# 로그 레벨별 확인
DEBUG: 상세 디버깅 정보
INFO: 일반 정보
ERROR: 오류 정보
```

## 7. 기여 가이드

### 코드 스타일
- PEP 8 준수
- Docstring 필수
- Type Hints 사용
```python
def function_name(param: str) -> bool:
    """
    Function description.
    Args:
        param: Parameter description
    Returns:
        Return value description
    """
```

### Pull Request 프로세스
1. Fork 저장소
2. Feature 브랜치 생성
3. 코드 작성 및 테스트
4. PR 생성
5. 코드 리뷰 진행

### 테스트
```bash
# 테스트 실행
python -m pytest tests/
# 커버리지 리포트
pytest --cov=.
```

---

이 메뉴얼은 지속적으로 업데이트됩니다. 개선사항이나 제안사항이 있다면 Issue를 생성해주세요.

---
## 리브
생각은 회의에, 기록은 RIV에 맡기세요!

Riv는 AI 기술을 통해 어렵고, 복잡하고, 귀찮았던 우리의 회의를 쉽고, 간편하고, 즐거운 회의로 바꿔줍니다. Riv와 함께 우리의 세상을 바꿔나가고 싶지 않나요?
Riv는 오픈소스 프로젝트입니다. 우리 함께 열려있는 협업 세상을 만들어봐요!

**편유나** Chatbot&AI

**문세종** Frontend 

**김혜령** Backend
