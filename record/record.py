# record/record.py
import discord
from record.file import filing
from record.utils import validate_audio_file  # 변경: utils에서 가져오기
import logging
import os

logger = logging.getLogger('discord')

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
        lambda sink, *args: validate_and_filing(sink, ctx.channel, filename),
        ctx.channel
    )
    return vc

async def validate_and_filing(sink, channel, filename):
    """
    녹음된 오디오를 검증하고 파일로 저장
    """
    valid_audio = True
    audio_data = {}

    for user_id, audio in sink.audio_data.items():
        # 오디오 데이터를 임시 파일에 저장
        temp_file = f"temp_{user_id}.wav"
        audio.file.seek(0)  # 파일 포인터 초기화
        
        try:
            with open(temp_file, "wb") as f:
                f.write(audio.file.read())
            
            if validate_audio_file(temp_file):
                # 유효한 오디오 파일인 경우 저장
                audio.file.seek(0)  # 다시 파일 포인터 초기화
                audio_data[user_id] = audio
            else:
                valid_audio = False
                await channel.send(f"❗ 사용자 {user_id}의 오디오 파일이 손상되었습니다.")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    if valid_audio and audio_data:
        # 모든 오디오가 유효한 경우에만 파일링 진행
        new_sink = discord.sinks.WaveSink()
        new_sink.audio_data = audio_data
        await filing(new_sink, channel, filename)
    else:
        await channel.send("❗ 오디오 파일 처리 중 문제가 발생했습니다.")
async def end_meeting(ctx, filename):
    try:
        guild_id = ctx.guild.id
        if guild_id in connections:
            vc = connections[guild_id]
            vc.stop_recording()
            await vc.disconnect()
            del connections[guild_id]
            await ctx.send(f"🛑 회의가 종료되었습니다. 파일명: {filename}")
            logger.info(f"회의 종료: {filename}")
        else:
            await ctx.send("현재 녹음 중이 아닙니다.")
    except Exception as e:
        logger.error(f"end_meeting 함수에서 오류 발생: {e}")
        await ctx.send("❗ 회의 종료 중 오류가 발생했습니다. 관리자에게 문의하세요.")
