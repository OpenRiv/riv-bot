# bot.py

import os
from dotenv import load_dotenv
from discord.ext import commands
from intents.intents import get_intents
from view.button import MeetingView
import asyncio
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('discord')

# 환경 변수 로드
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # OpenAI API 키 로드

# 인텐트 설정
intents = get_intents()

# 봇 초기화
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name="회의", help="음성 채널에서 녹음 가능한 회의를 시작합니다.")
async def 회의(ctx):
    try:
        roles = ctx.author.roles
        view = MeetingView(roles, ctx)

        # 메시지 전송 및 view.message 할당
        initial_message = await ctx.send("🔄 음성 채널 상태 확인 중...")
        view.message = initial_message
        logger.info("!회의 명령어가 호출되었습니다.")

        # 비동기 초기화 로직 실행
        asyncio.create_task(view.checkAndInit(roles))
    except Exception as e:
        logger.error(f"!회의 명령어 실행 중 오류 발생: {e}")
        await ctx.send("❗ 회의 시작 중 오류가 발생했습니다. 관리자에게 문의해주세요.")

@bot.command(name="ping", help="봇의 응답 시간을 확인합니다.")
async def ping(ctx):
    await ctx.send("Pong!")
    logger.info("!ping 명령어가 호출되었습니다.")

@bot.event
async def on_ready():
    logger.info(f'{bot.user}로 로그인되었습니다!')

# 토큰이 설정되지 않은 경우 에러 메시지 출력 후 종료
if not TOKEN:
    logger.error("❗ DISCORD_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")
    exit(1)

# 봇 실행
bot.run(TOKEN)
