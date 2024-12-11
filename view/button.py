import discord
from discord.ui import Button
from record.record import start_meeting, end_meeting
from record.file import fileName
import asyncio
import logging

logger = logging.getLogger('discord')

class MeetingView(discord.ui.View):
    """
    이 View 클래스는 음성 채널 회의 시작 및 종료를 위한 상호작용 버튼을 제공하고,
    하나의 메시지를 단계적으로 수정하며 사용자 경험을 개선한다.
    """

    def __init__(self, roles, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.filename = None
        self.message = None  # 명령어 실행 부분에서 먼저 생성한 메시지 객체를 참조

    async def checkAndInit(self, roles):
        """
        음성 채널 접속 여부와 사용자 수를 확인한 뒤, 하나의 메시지를 수정하여 단계별 안내.
        """
        try:
            # 메시지 내 버튼 중복 추가 방지
            self.clear_items()
            logger.info("checkAndInit 함수가 호출되었습니다.")

            # 음성 채널 접속 여부 확인
            voice = self.ctx.author.voice
            if not voice:
                logger.warning("사용자가 음성 채널에 접속하지 않았습니다.")
                await self.message.edit(content="❗ 음성 채널에 접속한 뒤 다시 시도해주세요.", view=None)
                return

            # 음성 채널 내 사용자 수 확인 (봇 제외)
            other_members = [member for member in voice.channel.members if not member.bot]
            logger.info(f"🔍 다른 사용자 목록: {[member.name for member in other_members]}")

            if len(other_members) == 0:
                logger.warning("현재 음성 채널에 다른 사용자가 없습니다.")
                await self.message.edit(content="❗ 현재 음성 채널에 다른 사용자가 없습니다.", view=None)
                return

            # 역할 목록에서 @everyone을 제외한 각 역할 이름으로 버튼 생성
            for role in roles:
                if role.name != "@everyone":
                    # 역할명 버튼 (예: Design, PM, Frontend 등)
                    button = Button(
                        label=role.name,
                        style=discord.ButtonStyle.primary,
                        emoji="🏷️"  # 카테고리를 상징하는 유효한 이모지
                    )
                    button.callback = self.create_filename_callback(role.name)
                    self.add_item(button)
                    logger.info(f"버튼이 추가되었습니다: {role.name}")

            # 사용자 정의 회의명 설정 버튼
            define_button = Button(
                label="카테고리 직접설정",
                style=discord.ButtonStyle.secondary,
                emoji="📝"  # 유효한 이모지
            )
            define_button.callback = self.custom_filename_callback
            self.add_item(define_button)
            logger.info("사용자 정의 회의명 설정 버튼이 추가되었습니다.")

            # 카테고리 설정 안내 메시지로 수정
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
        """
        역할 이름으로 회의명을 생성하고 회의를 시작하는 콜백을 반환하는 메서드.
        """

        async def callback(interaction):
            try:
                logger.info(f"{role_name} 역할로 회의를 시작합니다.")
                # 역할 이름을 기반으로 파일명 생성
                self.filename = fileName(role_name)
                logger.info(f"회의 파일명: {self.filename}")
                # 회의(녹음) 시작
                await start_meeting(self.ctx, self.filename)

                # 기존 버튼 모두 제거 후 회의 종료 버튼만 추가
                self.clear_items()
                self.add_end_meeting_button()
                logger.info("회의 종료 버튼이 추가되었습니다.")

                # 회의 시작 메시지 업데이트
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
        """
        사용자가 직접 회의명을 입력할 수 있도록 하는 콜백.
        """
        try:
            # 회의 제목 입력 안내 메시지로 수정
            await interaction.response.edit_message(
                content="📝 회의명을 채팅창에 입력해주세요!\n(취소하려면 아무 메시지도 보내지 않고 기다리세요.)",
                view=self
            )
            logger.info("사용자에게 회의명 입력을 요청했습니다.")

            def check(m):
                return m.author == self.ctx.author and m.channel == self.ctx.channel

            try:
                # 사용자로부터 메시지를 기다림 (타임아웃 설정 가능)
                msg = await self.ctx.bot.wait_for('message', check=check, timeout=60.0)
                logger.info(f"사용자가 입력한 회의명: {msg.content}")
            except asyncio.TimeoutError:
                # 타임아웃 시 안내 메시지 수정
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    content="⏰ 시간이 초과되었습니다. 다시 시도해주세요.",
                    view=None
                )
                logger.warning("회의명 입력 타임아웃 발생.")
                return

            try:
                # 입력받은 메시지를 통해 사용자 정의 파일명 생성
                self.filename = fileName(msg.content, custom=True)
                logger.info(f"회의 파일명: {self.filename}")
                # 회의(녹음) 시작
                await start_meeting(self.ctx, self.filename)

                # 기존 버튼 모두 제거 후 회의 종료 버튼 추가
                self.clear_items()
                self.add_end_meeting_button()
                logger.info("회의 종료 버튼이 추가되었습니다.")

                # 회의 시작 안내 메시지로 수정
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
        """
        회의 종료 버튼을 추가하는 메서드.
        """
        end_button = Button(label="회의종료", style=discord.ButtonStyle.danger, emoji="🛑")
        end_button.callback = self.end_meeting_button
        self.add_item(end_button)
        logger.info("회의 종료 버튼이 추가되었습니다.")

    async def end_meeting_button(self, interaction):
        """
        회의 종료 버튼 클릭 시 호출되는 콜백 함수.
        """
        try:
            logger.info("회의 종료 요청을 받았습니다.")
            # 회의 종료 처리
            await end_meeting(self.ctx, self.filename)
            # 회의 종료 안내 메시지로 수정
            await interaction.response.edit_message(
                content="🛑 회의가 종료되었습니다.\n녹음 파일이 정상적으로 저장되었습니다. 수고하셨습니다!",
                view=None  # View를 제거하여 더 이상 상호작용 불가
            )
            logger.info("회의 종료 메시지가 업데이트되었습니다.")
        except Exception as e:
            logger.error(f"회의 종료 중 오류 발생: {e}")
            await interaction.response.edit_message(
                content="❗ 회의 종료 중 오류가 발생했습니다. 관리자에게 문의해주세요.",
                view=None
            )
