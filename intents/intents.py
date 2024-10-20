# intents 설정

import discord

def get_intents():
    intents = discord.Intents.default()
    intents.message_content = True  
    intents.members = True  
    return intents
