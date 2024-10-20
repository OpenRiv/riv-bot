import discord
from record.file import filing

connections = {}


async def start_meeting(ctx, filename):
    voice = ctx.author.voice
    if not voice:
        await ctx.send("음성 채널에 접속해 주세요.")
        return None, None
    
    if len(voice.channel.members) == 0:
        await ctx.send("음성 채널에 사용자가 없습니다.")
        return None, None
    
    vc = await voice.channel.connect()
    connections[ctx.guild.id] = vc
    
    vc.start_recording(
        discord.sinks.WaveSink(), 
        lambda sink, *args: filing(sink, ctx.channel, filename), 
        ctx.channel
    )
    return vc

async def end_meeting(ctx, filename):
    if ctx.guild.id in connections:
        vc = connections[ctx.guild.id]
        vc.stop_recording()
        del connections[ctx.guild.id]
    else:
        await ctx.send("현재 녹음 중이 아닙니다.")
