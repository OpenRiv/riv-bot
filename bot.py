from intents.bot_setup import bot
from record.handler import record_audio, stop_recording
from view.meeting_view import MeetingView

@bot.event
async def on_ready():
    print(f"봇이 준비되었습니다: {bot.user}")

@bot.command()
async def 녹음시작(ctx):
    """음성 채널에서 녹음을 시작합니다."""
    await record_audio(ctx)

@bot.command()
async def 녹음종료(ctx):
    """음성 채널에서 녹음을 종료하고 파일을 저장합니다."""
    await stop_recording(ctx)

@bot.command()
async def 회의(ctx):
    """회의 관리를 위한 버튼 UI를 제공합니다."""
    roles = ctx.guild.roles
    view = MeetingView(roles, ctx)
    await ctx.send("회의 인터페이스를 준비합니다...", view=view)

if __name__ == "__main__":
    bot.run()
