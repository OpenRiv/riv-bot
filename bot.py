import os
from dotenv import load_dotenv
from discord.ext import commands
from intents.intents import get_intents
from view.button import MeetingView

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = get_intents()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def 회의(ctx):
    roles = ctx.author.roles 
    view = MeetingView(roles, ctx)  
    await ctx.send("---회의---", view=view)

@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인되었습니다!')

bot.run(TOKEN)

#초기 세팅
# python 3.10.4
# pip install -r requirements.txt