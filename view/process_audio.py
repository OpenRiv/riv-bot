import openai
from pydub import AudioSegment
import os
import math
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

async def process_audio(file_path, markdown_file, participants):
    """STT로 오디오 파일을 처리하고 마크다운 회의록을 생성합니다."""
    audio = AudioSegment.from_file(file_path)
    chunk_size = 20 * 1024 * 1024  # 20MB
    duration_per_chunk = math.floor(chunk_size / (audio.frame_rate * audio.frame_width))

    chunks = [
        audio[i * duration_per_chunk * 1000 : (i + 1) * duration_per_chunk * 1000]
        for i in range(math.ceil(len(audio) / (duration_per_chunk * 1000)))
    ]

    transcribed_text = ""

    for i, chunk in enumerate(chunks):
        chunk_path = f"chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")

        # Whisper API를 이용해 STT 처리
        with open(chunk_path, "rb") as audio_file:
            response = openai.Audio.transcribe("whisper-1", audio_file)
            transcribed_text += response["text"] + "\n"

        os.remove(chunk_path)

    # STT 결과를 마크다운 파일로 저장
    save_as_markdown(transcribed_text, markdown_file, participants)

    # 저장된 마크다운 파일을 요약
    summarized_markdown_file = summarize_to_markdown(markdown_file)

    return summarized_markdown_file


def save_as_markdown(text, markdown_file, participants):
    """STT 결과를 마크다운 형식으로 저장합니다."""
    participant_list = "\n".join([f"- {p}" for p in participants])
    content = f"""
# 회의록 원문

생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 회의 참여자
{participant_list}

## 원문 내용
{text}
"""

    with open(markdown_file, "w", encoding="utf-8") as file:
        file.write(content)


def summarize_to_markdown(markdown_file):
    """저장된 마크다운 파일을 요약합니다."""
    try:
        with open(markdown_file, 'r', encoding='utf-8') as file:
            text = file.read()
        
        content = """
        1. Formal Conditions: Please write this text in the form of minutes in Korean.
        Please write it in detail to contain the decision-making process as much as possible.

        2. Result condition: Please write the final version in a markdown format.
        Markdown file should be .md.

        3. Speakers multi-indication condition: If you have multiple speakers, 
        please indicate the speaker in the same format as "A:", "B:", regardless of gender.
        However, if there is only one speaker, please omit it.

        4. Date of meeting : Please write based on the date of creation of the text file.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": content},
                {"role": "user", "content": text}
            ]
        )

        summary = response['choices'][0]['message']['content']
        summarized_markdown_file = markdown_file.replace('.md', '_요약본.md')
        
        with open(summarized_markdown_file, "w", encoding="utf-8") as md_file:
            md_file.write(summary)
        
        return summarized_markdown_file
    except Exception as e:
        raise RuntimeError(f"Summary error: {e}")
