from datetime import datetime
import discord

# 녹음 파일명
def fileName(title, custom=False):
    today = datetime.now().strftime("%Y-%m-%d")
    if custom:
        return f"{today}_{title}"
    else:
        return f"{today}_{title} n차 회의"

# 녹음 파일 추출
async def filing(sink: discord.sinks.Sink, channel: discord.TextChannel, filename, *args):
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]

    filename_with_extension = f"{filename}.wav" if not filename.endswith(".wav") else filename

    files = [discord.File(audio.file, filename_with_extension) for user_id, audio in sink.audio_data.items()]

    await sink.vc.disconnect()

    await channel.send(f"녹음이 완료되었습니다. 회의 참여자: {', '.join(recorded_users)}", files=files)