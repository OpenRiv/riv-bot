import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# .env 파일에서 환경 변수 로드
load_dotenv()

# .env 파일에서 토큰 가져오기
TOKEN = os.getenv('DISCORD_TOKEN')

# 인텐트 설정
intents = discord.Intents.default()

intents.message_content = True  # 메시지 내용을 읽기 위한 인텐트
intents.members = True  # 서버 멤버 관련 인텐트

# 봇 객체 생성
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인되었습니다!')

# 봇 실행
bot.run(TOKEN)
