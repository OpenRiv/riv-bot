import discord
from discord.ext import commands
import asyncio
import os
import wave
import logging
from datetime import datetime
from discord import sinks
import io
import openai
from dotenv import load_dotenv
import time
import requests
from requests.exceptions import RequestException, Timeout
import requests
import json
from datetime import datetime, timedelta


# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,  # DEBUG로 변경하여 더 상세한 로그를 볼 수 있습니다.
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RecordingBot')

# 환경 변수에서 봇 토큰과 OpenAI API 키 가져오기
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if TOKEN is None:
    raise ValueError("DISCORD_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

# 필요한 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True  # 반드시 Discord Developer Portal에서 Server Members Intent 활성화 필요

# 봇 초기화
bot = commands.Bot(command_prefix='!', intents=intents)

# 녹음 세션을 추적하기 위한 딕셔너리
recording_sessions = {}

class CustomSink(sinks.WaveSink):
    def __init__(self):
        super().__init__()
        self.audio_data = {}
        self.speaking_times = {}  # 사용자별 발화 시간 리스트
        self.start_time = time.time()  # 녹음 시작 시간 기록
        logger.info("CustomSink 초기화됨")

    def write(self, data, user):
        # user가 discord.User 또는 discord.Member 객체인지 확인하고 user_id 추출
        user_id = user.id if isinstance(user, (discord.User, discord.Member)) else user
        if user_id not in self.audio_data:
            self.audio_data[user_id] = []
            self.speaking_times[user_id] = []
            logger.debug(f"새로운 사용자의 오디오 데이터 시작: {user_id}")
        # 현재 시간을 상대 타임스탬프로 계산
        current_time = time.time()
        relative_timestamp = current_time - self.start_time
        # Store tuple of (relative_timestamp, data)
        self.audio_data[user_id].append((relative_timestamp, data))
        # 발화 시간 기록
        self.speaking_times[user_id].append(relative_timestamp)
        logger.debug(f"오디오 데이터 추가됨 - 사용자: {user_id}, 데이터 크기: {len(data)} bytes, 타임스탬프: {relative_timestamp}")

    def cleanup(self):
        logger.info("CustomSink cleanup 실행")
        # 녹음 세션이 콜백 함수에서 오디오 데이터를 처리할 수 있도록 복사
        self.captured_audio = self.audio_data.copy()
        self.capturing_speaking_times = self.speaking_times.copy()
        self.audio_data.clear()
        self.speaking_times.clear()

class CategorySelectionView(discord.ui.View):
    def __init__(self, guild, author, timeout=60):
        super().__init__(timeout=timeout)
        self.guild = guild
        self.author = author
        self.message = None

        logger.info("서버 역할 기반 카테고리 버튼 생성 시작")
        roles_added = 0

        # 역할 필터 조건을 수정 또는 제거
        for role in guild.roles:
            if role.name not in ["@everyone","Riv"]:  # 'everyone' 역할 제외
                self.add_item(CategoryButton(label=role.name, role=role))
                roles_added += 1
        
        if roles_added == 0:
            logger.warning("조건에 맞는 역할이 없습니다. 모든 역할을 확인하세요.")

        # 사용자 정의 버튼 추가
        self.add_item(UserDefinedButton())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)



class CategoryButton(discord.ui.Button):
    def __init__(self, label, role):
        super().__init__(style=discord.ButtonStyle.primary, label=label, custom_id=f"🏷️category_{role.id}")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: CategorySelectionView = self.view
        if interaction.user != view.author:
            await interaction.followup.send("카테고리 설정은 회의 명령어 작성자만 설정 가능합니다.", ephemeral=True)
            return
        selected_category = self.label
        logger.info(f"사용자 {interaction.user}가 카테고리 '{selected_category}' 선택")
        await interaction.followup.send(f"선택된 카테고리: **{selected_category}**", ephemeral=True)
        self.view.stop()  # View의 대기 중인 task를 종료
        # Proceed to start recording
        await view.message.channel.send(f"✅ 회의가 시작되었습니다!\n음성 녹음이 진행 중입니다. 종료하려면 아래 버튼을 눌러주세요", view=StopRecordingView(view.guild, view.author, selected_category))
        await start_recording(view.guild, view.author, selected_category, view.message.channel)
        await self.view.message.delete() 


class UserDefinedButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.secondary, label="📝카테고리 직접설정", custom_id="category_user_defined")

    async def callback(self, interaction: discord.Interaction):
        view: CategorySelectionView = self.view
        if interaction.user != view.author:
            await interaction.response.send_message("이 버튼은 당신을 위한 것이 아닙니다.", ephemeral=True)
            return
        await interaction.response.send_message("📝 회의명을 채팅창에 입력해주세요!\n(취소하려면 아무 메시지도 보내지 않고 기다리세요.)", ephemeral=True)
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
            selected_category = msg.content.strip()
            if not selected_category:
                await interaction.followup.send("회의 생성이 취소되었습니다.", ephemeral=True)
                self.view.stop()
                return
            logger.info(f"사용자 {interaction.user}가 사용자 정의 카테고리 '{selected_category}' 입력")
            await interaction.followup.send(f"선택된 카테고리: **{selected_category}**", ephemeral=True)
            self.view.stop()
            # Proceed to start recording
            await view.message.channel.send(f"✅ 회의가 시작되었습니다!\n음성 녹음이 진행 중입니다. 종료하려면 아래 버튼을 눌러주세요", view=StopRecordingView(view.guild, view.author, selected_category))
            await start_recording(view.guild, view.author, selected_category, view.message.channel)
        except asyncio.TimeoutError:
            await interaction.followup.send("회의 생성이 취소되었습니다 (시간 초과).", ephemeral=True)
            self.view.stop()

class StopRecordingView(discord.ui.View):
    def __init__(self, guild, author, meeting_category, timeout=None):
        super().__init__(timeout=timeout)
        self.guild = guild
        self.author = author
        self.meeting_category = meeting_category
        self.message = None  # message 속성 추가
        self.add_item(StopRecordingButton())

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)
class StopRecordingButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="🛑회의 종료", custom_id="stop_recording")

    async def callback(self, interaction: discord.Interaction):
        view: StopRecordingView = self.view
        if interaction.user != view.author:
            await interaction.response.send_message("이 버튼은 회의를 시작한 사용자만 사용할 수 있습니다.", ephemeral=True)
            return
        
        await interaction.response.defer()
        logger.info(f"사용자 {interaction.user}가 회의 종료 버튼 클릭")
        
        try:
            await interaction.followup.send("회의를 종료합니다...")
            self.view.stop()
            
            # 녹음 중지 시도
            await stop_recording(view.guild, view.message.channel)
            
            # 메시지 삭제 시도
            if view.message:
                try:
                    await view.message.delete()
                except discord.errors.NotFound:
                    logger.warning("삭제할 메시지를 찾을 수 없습니다.")
                except Exception as e:
                    logger.error(f"메시지 삭제 중 오류 발생: {e}")
        
        except Exception as e:
            logger.error(f"회의 종료 처리 중 오류 발생: {e}")
            await interaction.followup.send(f"회의 종료 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

async def start_recording(guild, author, meeting_category, message):
    """회의 녹음을 시작하는 함수"""
    try:
        if guild.id in recording_sessions:
            await message.channel.send("이미 녹음이 진행 중입니다.")
            return

        voice_state = author.voice
        if not voice_state or not voice_state.channel:
            await message.channel.send("먼저 음성 채널에 접속해주세요.")
            return

        voice_channel = voice_state.channel
        logger.info(f"음성 채널 확인됨: {voice_channel.name}")

        if guild.voice_client:
            logger.debug("기존 음성 클라이언트가 존재하여 연결을 해제합니다.")
            await guild.voice_client.disconnect()

        logger.debug("음성 채널 연결 시도")
        vc = await voice_channel.connect()
        sink = CustomSink()
        recording_sessions[guild.id] = sink

        # 음성 채널 멤버 가져오기
        members = await get_voice_channel_members(voice_channel)

        # 녹음 시작 시간 기록
        start_time = datetime.now()

        # 진행 상태 업데이트
        await update_status_message(message, "녹음 시작됨")

        async def recording_finished(sink, error=None):
            """녹음 완료 시 호출되는 콜백"""
            end_time = datetime.now()  # 녹음 종료 시간 기록
            if error:
                logger.error(f"녹음 중 오류 발생: {error}")
                await update_status_message(message, f"오류 발생: {error}")
            else:
                logger.info("녹음 콜백 시작")
                await update_status_message(message, "녹음 완료, 처리 중...")
                await process_recording(sink, message, meeting_category, members, start_time, end_time)  # `.channel` 제거

            # 녹음 세션 제거
            if guild.id in recording_sessions:
                del recording_sessions[guild.id]
                logger.info(f"서버 {guild.name}의 녹음 세션 제거")
            # 음성 클라이언트 종료
            if guild.voice_client:
                await guild.voice_client.disconnect()


        logger.debug("녹음 시작")
        vc.start_recording(sink, recording_finished)

        logger.info(f"녹음 시작됨 - 서버: {guild.name}, 채널: {voice_channel.name}")

    except Exception as e:
        error_msg = f"녹음 시작 중 오류 발생: {e}"
        logger.error(error_msg)
        await message.channel.send(f"녹음을 시작할 수 없습니다: {e}")

async def stop_recording(guild, channel):
    """회의 녹음을 중지하는 함수"""
    try:
        if guild.id not in recording_sessions:
            await channel.send("현재 녹음 중이 아닙니다.")
            return

        if guild.voice_client:
            logger.debug("녹음 중지 시도")
            vc = guild.voice_client
            
            try:
                # 녹음 중지 전에 녹음 상태 확인
                if hasattr(vc, '_recording') and vc._recording:
                    vc.stop_recording()  # 이 호출은 콜백을 트리거합니다.
                    logger.info("녹음이 정상적으로 중지되었습니다.")
                else:
                    logger.warning("이미 녹음이 중지된 상태입니다.")
            except discord.sinks.errors.RecordingException:
                logger.warning("녹음이 이미 중지되었거나 진행 중이지 않습니다.")
            except Exception as e:
                logger.error(f"녹음 중지 중 예외 발생: {e}")
            
            try:
                # voice client 연결 해제
                await vc.disconnect()
                logger.info(f"음성 채널 연결이 해제되었습니다.")
            except Exception as e:
                logger.error(f"음성 채널 연결 해제 중 오류: {e}")

            # 녹음 세션 정리
            if guild.id in recording_sessions:
                del recording_sessions[guild.id]
                logger.info(f"서버 {guild.name}의 녹음 세션이 제거되었습니다.")

    except Exception as e:
        error_msg = f"녹음을 중지하는 중 오류 발생: {e}"
        logger.error(error_msg)
        await channel.send(f"녹음을 중지하는 중 오류가 발생했습니다: {e}")

async def get_voice_channel_members(voice_channel):
    """음성 채널에서 현재 참여 중인 사용자 반환 (봇 제외)"""
    members = [member for member in voice_channel.members if not member.bot]
    return members




async def update_status_message(message, status):
    """진행 상태를 메시지에 업데이트"""
    content = f"🔄 **진행 상태**: {status}"
    await message.edit(content=content)
    
    
async def process_recording(sink, channel, meeting_title, members, start_time, end_time):
    """녹음 처리를 위한 비동기 함수"""
    try:
        audio_data = sink.captured_audio

        status_message = await channel.send("🔄 **진행 상태**: 녹음 데이터 병합 중...")
        await update_status_message(status_message, "녹음 데이터 병합 중...")

        merged_audio = merge_audio(audio_data)

        await update_status_message(status_message, "Whisper API를 통해 전사 중...")
        transcription_text, segments = await transcribe_audio(merged_audio)

        if transcription_text is None:
            await update_status_message(status_message, "회의록 생성 실패: Whisper API 호출 실패")
            return
        
        participants_list = "\n".join([f"- {member.display_name}" for member in members])

        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        await update_status_message(status_message, "회의 내용 요약 중...")
        summary = await summarize_text(transcription_text)

        markdown_content = f"""# 회의록

        ## 기본 정보
        - 시작 시간: {start_time_str}
        - 종료 시간: {end_time_str}
        - 회의 카테고리: {meeting_title}

        ## 참석자
        {participants_list}

        ## 회의 내용 요약
        {summary}
        """

        # 회의록을 API에 업로드
        upload_success = await upload_minutes_to_api(
            title=meeting_title,
            text=f"참석자 : {participants_list} \n\n{summary}",
            category_name=meeting_title,
            start_time=start_time,
            end_time=end_time,
            server_id=channel.guild.id,
            channel_id=channel.id
        )

        if upload_success:
            await channel.send("✅ 회의록이 서버에 성공적으로 업로드되었습니다!")
        else:
            await channel.send("⚠️ 회의록 업로드에 실패했습니다.")

        # 파일명 생성 및 디스코드 채널에도 전송
        filename = f"{start_time.strftime('%Y%m%d_%H%M')}-{meeting_title}.md"
        minutes_buffer = io.BytesIO(markdown_content.encode('utf-8'))
        minutes_buffer.seek(0)
        minutes_file = discord.File(fp=minutes_buffer, filename=filename)
        await channel.send("회의록이 생성되었습니다:", file=minutes_file)

        await update_status_message(status_message, "회의록 생성 및 업로드 완료")
        logger.info("회의록 생성 완료")

    except Exception as e:
        logger.error(f"회의록 생성 중 오류 발생: {e}")
        await channel.send(f"회의록 생성 중 오류 발생: {str(e)}")

    
async def upload_minutes_to_api(title, text, category_name, start_time, end_time, server_id, channel_id):
    """회의록을 API에 업로드하는 함수"""
    url = 'https://3.37.89.101:443/recoding/unique'

    payload = {
        "serverUniqueId": server_id,
        "channelUniqueId": channel_id,
        "title": title,
        "text": text,
        "categoryName": category_name,
        "startTime": start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "endTime": end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN'  # 필요한 경우 인증 토큰 입력
    }

    try:
        print("\n=== 회의록 업로드 API 호출 ===")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)

        print(f"응답 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")

        if response.status_code == 200:
            return True
        else:
            logger.warning(f"회의록 업로드 실패: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 중 오류 발생: {e}")
        return False


async def update_status_message(message, status):
    """진행 상태를 메시지에 업데이트"""
    try:
        content = f"🔄 **진행 상태**: {status}"
        await message.edit(content=content)
    except Exception as e:
        logger.error(f"상태 메시지 업데이트 실패: {e}")


@bot.event
async def on_ready():
    logger.info(f'봇 로그인 완료: {bot.user}')

@bot.command()
async def 역할목록(ctx):
    """서버에서 모든 역할 이름을 출력"""
    roles = ctx.guild.roles
    logger.info(f"서버 '{ctx.guild.name}' 역할 목록: {[role.name for role in roles]}")
    await ctx.send(f"서버에 등록된 역할: {[role.name for role in roles]}")


@bot.command()
async def 회의(ctx):
    """회의 시작 명령어
    사용 예시: !회의
    """
    logger.info(f"회의 명령어 실행 - 서버: {ctx.guild.name}, 채널: {ctx.channel.name}, 사용자: {ctx.author.name}")

    if not ctx.author.voice:
        await ctx.send("먼저 음성 채널에 접속해주세요.")
        return

    # 카테고리 선택을 위한 버튼 뷰 생성 및 전송
    view = CategorySelectionView(ctx.guild, ctx.author)
    message = await ctx.send("회의 카테고리를 선택해주세요:", view=view)
    view.message = message  # View 내에서 메시지를 참조할 수 있도록 설정


@bot.event
async def on_message(message):
    # 봇 자신이 보낸 메시지는 무시
    if message.author.bot:
        return
    await bot.process_commands(message)

def match_speaker(segment_start, segment_end, speaking_times, threshold=1.0):
    """
    세그먼트의 시작 및 종료 시간을 기반으로 발화자를 매칭하는 함수.
    :param segment_start: 세그먼트 시작 시간 (초)
    :param segment_end: 세그먼트 종료 시간 (초)
    :param speaking_times: 사용자별 발화 시간 리스트 (user_id: list of relative timestamps)
    :param threshold: 매칭을 위한 허용 오차 (초)
    :return: 발화자 ID 또는 None
    """
    closest_user = None
    closest_time_diff = float('inf')

    for user_id, times in speaking_times.items():
        for timestamp in times:
            # 발화 시간(timestamp)이 세그먼트 시간 범위에 포함되는지 확인
            if segment_start - threshold <= timestamp <= segment_end + threshold:
                time_diff = abs(segment_start - timestamp)
                if time_diff < closest_time_diff:
                    closest_time_diff = time_diff
                    closest_user = user_id

    return closest_user  # 발화자 ID 반환 (없으면 None)

async def transcribe_audio(file_bytes, timeout=120):
    """
    OpenAI Whisper API를 사용하여 오디오를 전사하는 함수.
    :param file_bytes: BytesIO 객체로 된 오디오 파일
    :param timeout: 요청 타임아웃 (초)
    :return: 전사된 텍스트 및 세그먼트 정보
    """
    try:
        # BytesIO 객체에 name 속성 추가
        file_bytes.name = "merged_audio.wav"

        logger.debug("Whisper API에 오디오 전송 중...")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.Audio.transcribe(
                model="whisper-1",
                file=file_bytes,
                language="ko",
                response_format="verbose_json"  # 세그먼트 정보 포함
            )
        )
        transcription_text = response['text'].strip()
        segments = response.get('segments', [])
        logger.debug("Whisper API로부터 전사된 텍스트 및 세그먼트 수신 완료.")
        return transcription_text, segments
    except RequestException as e:
        logger.error(f"네트워크 오류로 Whisper API 전사 실패: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Whisper API 전사 중 오류 발생: {e}")
        return None, None

def merge_audio(audio_data):
    """
    여러 사용자의 오디오 데이터를 병합하여 하나의 오디오 파일로 만드는 함수.
    :param audio_data: 사용자별 오디오 데이터 (user_id: list of (relative_timestamp, data))
    :return: BytesIO 객체로 된 병합된 오디오 파일
    """
    # 모든 오디오 데이터를 시간 순으로 정렬
    all_chunks = []
    for user_id, chunks in audio_data.items():
        for timestamp, data in chunks:
            all_chunks.append((timestamp, data))
    all_chunks.sort(key=lambda x: x[0])

    # 병합된 오디오 데이터
    merged_audio = b''.join([chunk[1] for chunk in all_chunks])

    # In-memory bytes buffer
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(48000)
        wav_file.writeframes(merged_audio)

    # Seek to the beginning of the BytesIO buffer
    wav_buffer.seek(0)

    return wav_buffer

async def summarize_text(text):
    """
    OpenAI GPT-3.5-turbo를 사용하여 텍스트를 요약하는 함수.
    :param text: 요약할 텍스트
    :return: 요약된 텍스트
    """

    prompt = """
    너는 회의록을 요약해주는 AI 어시스턴스야.
    주요 회의 내용을 한국어로 간결하게 개조식으로 요약해줘.
    주요 결정사안에 대해선 맥락을 유지하며 더욱 자세하게 설명해줘.
    """

    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system","content":prompt,},
                {"role": "user", "content": f"Please summarize the following meeting transcript:\n\n{text}"}
            ],
            max_tokens=150,
            temperature=0.5
        )
        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except Exception as e:
        logger.error(f"요약 생성 중 오류 발생: {e}")
        return "요약 생성 중 오류가 발생했습니다."


bot.run(TOKEN)
