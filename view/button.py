# view/button.py

import discord
from discord.ui import Button
from record.file import filing, MySink
import asyncio
import logging
from utils.utils import fileName
from stt.transcription import TranscriptionService

logger = logging.getLogger('discord')

class MeetingView(discord.ui.View):
    def __init__(self, roles, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.filename = None
        self.message = None
        self.sink = None  # 녹음용 Sink 인스턴스 저장

    async def checkAndInit(self, roles):
        try:
            self.clear_items()
            logger.info("checkAndInit 함수가 호출되었습니다.")

            voice = self.ctx.author.voice
            if not voice:
                logger.warning("사용자가 음성 채널에 접속하지 않았습니다.")
                await self.message.edit(content="❗ 음성 채널에 접속한 뒤 다시 시도해주세요.", view=None)
                return

            other_members = [member for member in voice.channel.members if not member.bot]
            logger.info(f"🔍 다른 사용자 목록: {[member.name for member in other_members]}")

            if len(other_members) == 0:
                logger.warning("현재 음성 채널에 다른 사용자가 없습니다.")
                await self.message.edit(content="❗ 현재 음성 채널에 다른 사용자가 없습니다.", view=None)
                return

            for role in roles:
                if role.name != "@everyone":
                    button = Button(
                        label=role.name,
                        style=discord.ButtonStyle.primary,
                        emoji="🏷️"
                    )
                    button.callback = self.create_filename_callback(role.name)
                    self.add_item(button)
                    logger.info(f"버튼이 추가되었습니다: {role.name}")

            define_button = Button(
                label="카테고리 직접설정",
                style=discord.ButtonStyle.secondary,
                emoji="📝"
            )
            define_button.callback = self.custom_filename_callback
            self.add_item(define_button)
            logger.info("사용자 정의 회의명 설정 버튼이 추가되었습니다.")

            initial_message = (
                "🔊 **음성 채널 접속 확인 완료**\n\n"
                "아래에서 회의 카테고리를 선택하거나, `카테고리 직접설정` 버튼을 눌러\n"
                "원하는 이름을 채팅창에 입력해주세요."
            )
            await self.message.edit(content=initial_message, view=self)
            logger.info("회의 카테고리 설정 안내 메시지가 수정되었습니다.")
        except Exception as e:
            logger.error(f"checkAndInit 함수에서 오류 발생: {e}")
            await self.message.edit(content="❗ 예상치 못한 오류가 발생했습니다. 관리자에게 문의해주세요.", view=None)

    def create_filename_callback(self, role_name):
        async def callback(interaction):
            try:
                logger.info(f"{role_name} 역할로 회의를 시작합니다.")
                self.filename = fileName(role_name)
                logger.info(f"회의 파일명: {self.filename}")

                await start_meeting(self, self.filename)

                self.clear_items()
                self.add_end_meeting_button()
                logger.info("회의 종료 버튼이 추가되었습니다.")

                await interaction.response.edit_message(
                    content="✅ 회의가 시작되었습니다!\n음성 녹음이 진행 중입니다. 종료하려면 아래 버튼을 눌러주세요.",
                    view=self
                )
                logger.info("회의 시작 메시지가 업데이트되었습니다.")
            except Exception as e:
                logger.error(f"회의 시작 중 오류 발생: {e}")
                await interaction.response.edit_message(
                    content="❗ 회의 시작 중 오류가 발생했습니다. 관리자에게 문의해주세요.",
                    view=None
                )
        return callback

    async def custom_filename_callback(self, interaction):
        try:
            await interaction.response.edit_message(
                content="📝 회의명을 채팅창에 입력해주세요!\n(취소하려면 아무 메시지도 보내지 않고 기다리세요.)",
                view=self
            )
            logger.info("사용자에게 회의명 입력을 요청했습니다.")

            def check(m):
                return m.author == self.ctx.author and m.channel == self.ctx.channel

            try:
                msg = await self.ctx.bot.wait_for('message', check=check, timeout=60.0)
                logger.info(f"사용자가 입력한 회의명: {msg.content}")
            except asyncio.TimeoutError:
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    content="⏰ 시간이 초과되었습니다. 다시 시도해주세요.",
                    view=None
                )
                logger.warning("회의명 입력 타임아웃 발생.")
                return

            try:
                self.filename = fileName(msg.content, custom=True)
                logger.info(f"회의 파일명: {self.filename}")
                await start_meeting(self, self.filename)

                self.clear_items()
                self.add_end_meeting_button()
                logger.info("회의 종료 버튼이 추가되었습니다.")

                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    content="✅ 회의가 시작되었습니다!\n음성 녹음이 진행 중입니다. 종료하려면 아래 버튼을 눌러주세요.",
                    view=self
                )
                logger.info("회의 시작 메시지가 업데이트되었습니다.")
            except Exception as e:
                logger.error(f"회의 시작 중 오류 발생: {e}")
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    content="❗ 회의 시작 중 오류가 발생했습니다. 관리자에게 문의해주세요.",
                    view=None
                )
        except Exception as e:
            logger.error(f"custom_filename_callback 함수에서 오류 발생: {e}")
            await interaction.response.edit_message(
                content="❗ 예상치 못한 오류가 발생했습니다. 관리자에게 문의해주세요.",
                view=None
            )

    def add_end_meeting_button(self):
        end_button = Button(label="회의종료", style=discord.ButtonStyle.danger, emoji="🛑")
        end_button.callback = self.end_meeting_button
        self.add_item(end_button)
        logger.info("회의 종료 버튼이 추가되었습니다.")

    async def end_meeting_button(self, interaction):
        try:
            logger.info("회의 종료 요청을 받았습니다.")
            if self.sink is None:
                logger.error("Sink 인스턴스가 저장되지 않았습니다.")
                await interaction.response.edit_message(
                    content="❗ 녹음 세션이 활성화되지 않았습니다.",
                    view=None
                )
                return
            await filing(self.sink, self.ctx.channel, self.filename)
            await interaction.response.edit_message(
                content="🛑 회의가 종료되었습니다.\n녹음 파일이 정상적으로 저장되고 전송되었습니다. 수고하셨습니다!",
                view=None
            )
            logger.info("회의 종료 메시지가 업데이트되었습니다.")
        except Exception as e:
            logger.error(f"회의 종료 중 오류 발생: {e}")
            await interaction.response.edit_message(
                content="❗ 회의 종료 중 오류가 발생했습니다. 관리자에게 문의해주세요.",
                view=None
            )

async def start_meeting(view, filename):
    """
    녹음을 시작하는 함수입니다.
    """
    voice = view.ctx.author.voice
    if not voice:
        await view.ctx.send("❗ 음성 채널에 먼저 접속해주세요.")
        return

    channel = voice.channel
    try:
        vc = await channel.connect()
    except discord.ClientException:
        vc = channel.guild.voice_client
    sink = MySink()
    view.sink = sink  # sink 인스턴스를 MeetingView에 저장

    # 'finished_callback'을 포지셔널 인수로 전달
    vc.start_recording(
        sink,
        lambda sink, _: asyncio.run_coroutine_threadsafe(
            finished_recording(sink, view, filename), 
            view.ctx.bot.loop
        )
    )
    logger.info("녹음이 시작되었습니다.")

async def finished_recording(sink, view, filename):
    """
    녹음이 종료되었을 때 호출되는 콜백 함수입니다.
    """
    await view.ctx.voice_client.disconnect()
    logger.info("녹음이 종료되고 음성 채널 연결이 해제되었습니다.")
    # 'filing' 함수는 '회의종료' 버튼 클릭 시 호출되므로 여기서는 별도로 처리하지 않습니다.
