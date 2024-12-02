from discord.ext.audiorec import AudioRecorder
from datetime import datetime
from view.process_audio import process_audio

audio_recorder = AudioRecorder()

async def record_audio(ctx):
    """음성 채널에 연결하고 녹음을 시작합니다."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        audio_recorder.start(vc)
        await ctx.send("녹음을 시작했습니다.")
    else:
        await ctx.send("음성 채널에 접속한 상태여야 녹음을 시작할 수 있습니다.")

async def stop_recording(ctx):
    """녹음을 종료하고 파일을 저장하고, STT로 회의록을 생성합니다."""
    if ctx.voice_client:
        audio_recorder.stop()

        # 현재 날짜와 시간으로 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        recording_file = f"recording_{timestamp}.wav"
        markdown_file = f"meeting_notes_{timestamp}.md"

        audio_recorder.save(recording_file)
        await ctx.voice_client.disconnect()
        await ctx.send(f"녹음을 종료했습니다. 파일이 저장되었습니다: {recording_file}")

        # STT 처리 및 회의록 생성
        await process_audio(recording_file, markdown_file)
        await ctx.send(f"회의록이 생성되었습니다: {markdown_file}")
    else:
        await ctx.send("현재 녹음 중이 아닙니다.")
