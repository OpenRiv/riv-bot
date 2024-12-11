import discord

def get_intents():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True       # 서버 멤버 정보를 얻기 위해 활성화
    intents.voice_states = True  # 음성 상태 정보를 얻기 위해 활성화
    intents.message_content = True  # 메시지 내용을 읽기 위해 활성화
    return intents
