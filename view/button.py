import discord
from discord.ui import Button
from record.record import start_meeting, end_meeting
from record.file import fileName
import asyncio
import logging

logger = logging.getLogger('discord')


class MeetingView(discord.ui.View):
    def __init__(self, roles, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.filename = None
        self.message = None

    async def checkAndInit(self, roles):
        try:
            self.clear_items()
            logger.info("checkAndInit 함수가 호출되었습니다.")

            voice = self.ctx.author.voice
            if not voice:
                await self.message.edit(content="❗ 음성 채널에 접속한 뒤 다시 시도해주세요.", view=None)
                logger.warning("사용자가 음성 채널에 접속하지 않았습니다.")
                return

            other_members = [member for member in voice.channel.members if not member.bot]
            if len(other_members) == 0:
                await self.message.edit(content="❗ 현재 음성 채널에 다른 사용자가 없습니다.", view=None)
                logger.warning("현재 음성 채널에 다른 사용자가 없습니다.")
                return

            for role in roles:
                if role.name != "@everyone":
                    button = Button(label=role.name, style=discord.ButtonStyle.primary, emoji="🏷️")
                    button.callback = self.create_filename_callback(role.name)
                    self.add_item(button)
                    logger.info(f"버튼이 추가되었습니다: {role.name}")

            define_button = Button(label="카테고리 직접설정", style=discord.ButtonStyle.secondary, emoji="📝")
            define_button.callback = self.custom_filename_callback
            self.add_item(define_button)

            await self.message.edit(
                content="🔊 **음성 채널 접속 확인 완료**\n\n"
                        "아래에서 회의 카테고리를 선택하거나, `카테고리 직접설정` 버튼을 눌러 원하는 이름을 채팅창에 입력해주세요.",
                view=self
            )
            logger.info("회의 카테고리 설정 안내 메시지가 수정되었습니다.")
        except Exception as e:
            logger.error(f"checkAndInit 함수에서 오류 발생: {e}")
            await self.message.edit(content="❗ 예상치 못한 오류가 발생했습니다. 관리자에게 문의해주세요.", view=None)

    def create_filename_callback(self, role_name):
        async def callback(interaction):
            try:
                logger.info(f"{role_name} 역할로 회의를 시작합니다.")
                self.filename = fileName(role_name)
                await start_meeting(self.ctx, self.filename)

                self.clear_items()
                self.add_end_meeting_button()
                await interaction.response.edit_message(
                    content="✅ 회의가 시작되었습니다!\n음성 녹음이 진행 중입니다. 종료하려면 아래 버튼을 눌러주세요.",
                    view=self
                )
                logger.info(f"회의 시작 메시지가 업데이트되었습니다. 파일명: {self.filename}")
            except Exception as e:
                logger.error(f"회의 시작 중 오류 발생: {e}")
                await interaction.response.edit_message(
                    content="❗ 회의 시작 중 오류가 발생했습니다. 관리자에게 문의해주세요.", view=None
                )
        return callback

    async def custom_filename_callback(self, interaction):
        try:
            await interaction.response.edit_message(
                content="📝 회의명을 채팅창에 입력해주세요!\n(취소하려면 아무 메시지도 보내지 않고 기다리세요.)", view=self
            )
            logger.info("사용자에게 회의명 입력을 요청했습니다.")

            def check(m):
                return m.author == self.ctx.author and m.channel == self.ctx.channel

            try:
                msg = await self.ctx.bot.wait_for('message', check=check, timeout=60.0)
                self.filename = fileName(msg.content)
                await start_meeting(self.ctx, self.filename)

                self.clear_items()
                self.add_end_meeting_button()
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    content="✅ 회의가 시작되었습니다!\n음성 녹음이 진행 중입니다. 종료하려면 아래 버튼을 눌러주세요.",
                    view=self
                )
                logger.info(f"회의 시작 메시지가 업데이트되었습니다. 파일명: {self.filename}")
            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ 시간이 초과되었습니다. 다시 시도해주세요.", ephemeral=True)
                logger.warning("회의명 입력 타임아웃 발생.")
        except Exception as e:
            logger.error(f"custom_filename_callback 함수에서 오류 발생: {e}")
            await interaction.response.edit_message(
                content="❗ 예상치 못한 오류가 발생했습니다. 관리자에게 문의해주세요.", view=None
            )

    def add_end_meeting_button(self):
        end_button = Button(label="회의종료", style=discord.ButtonStyle.danger, emoji="🛑")
        end_button.callback = self.end_meeting_button
        self.add_item(end_button)

    async def end_meeting_button(self, interaction):
        try:
            await end_meeting(self.ctx, self.filename)
            await interaction.response.edit_message(
                content="🛑 회의가 종료되었습니다.\n녹음 파일이 정상적으로 저장되었습니다. 수고하셨습니다!", view=None
            )
            logger.info(f"회의 종료 처리 완료. 파일명: {self.filename}")
        except Exception as e:
            logger.error(f"회의 종료 중 오류 발생: {e}")
            await interaction.response.edit_message(
                content="❗ 회의 종료 중 오류가 발생했습니다. 관리자에게 문의해주세요.", view=None
            )
