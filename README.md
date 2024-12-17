# Riv-Bot 🚀

Discord 음성 채널의 대화를 실시간으로 녹음하고, OpenAI의 Whisper API와 GPT-3.5를 활용하여 회의록을 자동으로 생성하는 Discord 봇입니다.

![GitHub Repo stars](https://img.shields.io/github/stars/OpenRiv/riv-bot?style=social)

![GitHub issues](https://img.shields.io/github/issues/OpenRiv/riv-bot)

![GitHub license](https://img.shields.io/github/license/OpenRiv/riv-bot)

Riv-Bot은 Discord 기반의 회의록 자동 작성 및 요약 프로젝트입니다. 이 봇은 음성 채널에서의 대화를 녹음하고, 녹음된 내용을 자동으로 텍스트로 변환한 후, 중요한 내용을 요약하여 제공합니다. 이를 통해 회의의 효율성을 높이고, 회의 후 정리 시간을 절약할 수 있습니다.

## ✨ 주요 기능

- **실시간 음성 녹음 및 전사**
  - Discord 음성 채널의 대화를 실시간으로 녹음
  - OpenAI Whisper API를 통한 고품질 음성-텍스트 변환
  - 다중 화자 음성 처리 지원

- **스마트 회의록 생성**
  - GPT를 활용한 회의 내용 자동 요약
  - 주요 결정사항 추출
  - 마크다운 형식의 구조화된 회의록 생성

- **유연한 카테고리 관리**
  - 서버 역할 기반 자동 카테고리 생성
  - 사용자 정의 카테고리 지원
  - 직관적인 버튼 인터페이스

- **안정적인 운영 환경**
  - 상세한 로깅 시스템
  - 에러 처리 및 복구 매커니즘
  - SSL 보안 통신 지원

## 🛠️ 기술 스택

- **Backend**: Python 3.8+, discord.py
- **AI/ML**: OpenAI Whisper API, GPT-3.5
- **음성처리**: discord.sinks, wave
- **데이터 저장**: RESTful API 연동

## 📦 설치 방법

1. **저장소 클론**
```bash
git clone https://github.com/OpenRiv/riv-bot.git
cd riv-bot
```

2. **가상환경 설정**
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

4. **환경 변수 설정**
`.env` 파일 생성:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
```

## 🚀 사용 방법

1. **회의 시작**
```
!회의
```
- 음성 채널에 접속한 상태에서 명령어 입력
- 카테고리 선택 버튼이 표시됨
- 기존 역할 또는 사용자 정의 카테고리 선택 가능

2. **회의 진행**
- 봇이 자동으로 음성 채널에 참여하여 녹음 시작
- 실시간 진행 상태 확인 가능

3. **회의 종료**
- UI의 '회의 종료' 버튼 클릭
- 자동으로 회의록 생성 및 업로드
- 마크다운 파일로 채널에 전송

## ⚙️ 주요 설정

### Discord 봇 권한
- Send Messages
- Read Message History
- Connect
- Speak
- Use Voice Activity
- Server Members Intent

### 로깅 레벨
```python
# 개발 환경
level=logging.DEBUG
# 운영 환경
level=logging.INFO
```

## 📋 회의록 형식

```markdown
# 회의록

## 기본 정보
- 시작 시간: YYYY-MM-DD HH:MM:SS
- 종료 시간: YYYY-MM-DD HH:MM:SS
- 회의 카테고리: [카테고리명]

## 참석자
- 참석자1
- 참석자2
...

## 회의 내용 요약
[AI가 생성한 주요 내용 요약]

## 전체 회의 내용
[상세 회의 내용]
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이센스

MIT License를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🧑‍💻 개발팀

- **편유나** - *Chatbot & AI & Web Design*
- **문세종** - *Web Frontend*
- **김혜령** - *Web/Chatbot Backend*

## 💬 문의하기

문제점이나 제안사항이 있다면 GitHub Issues를 통해 알려주세요.

---

> **Riv**: 생각은 회의에, 기록은 RIV에 맡기세요!
