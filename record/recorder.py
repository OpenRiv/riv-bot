from discord.ext.audiorec import AudioRecorder

audio_recorder = AudioRecorder()

def start_recording(vc):
    audio_recorder.start(vc)

def stop_and_save_recording():
    audio_recorder.stop()
    recording_file = "recording.wav"
    audio_recorder.save(recording_file)
    return recording_file
