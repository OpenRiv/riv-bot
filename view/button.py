import discord
from discord.ui import Button
from record.record import start_meeting, end_meeting
from record.file import fileName
import asyncio

class MeetingView(discord.ui.View):
    
    def __init__(self, roles, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.filename = None
        self.message = None 

        asyncio.run_coroutine_threadsafe(self.checkAndInit(roles), asyncio.get_event_loop())

    async def checkAndInit(self, roles):
        voice = self.ctx.author.voice
        if not voice:
            self.message = await self.ctx.send("음성 채널에 접속해 주세요.")
            return
        
        if len(voice.channel.members) == 0:
            self.message = await self.ctx.send("음성 채널에 사용자가 없습니다.")
            return

        for role in roles:
            if role.name != "@everyone":
                button = Button(label=role.name, style=discord.ButtonStyle.primary)
                button.callback = self.create_filename_callback(role.name)
                self.add_item(button)

        define_button = Button(label="정의", style=discord.ButtonStyle.secondary)
        define_button.callback = self.custom_filename_callback
        self.add_item(define_button)

        self.message = await self.ctx.send("회의 종류를 선택하세요.", view=self)

    def create_filename_callback(self, role_name):
        async def callback(interaction):
            self.filename = fileName(role_name)
            await start_meeting(self.ctx, self.filename)

            self.clear_items()
            self.add_end_meeting_button()

            await interaction.response.edit_message(content="회의가 시작되었습니다.", view=self)
        return callback

    async def custom_filename_callback(self, interaction):
        await interaction.response.edit_message(content="회의 제목을 입력해 주세요.", view=self)
    
        def check(m):
            return m.author == self.ctx.author and m.channel == self.ctx.channel

        msg = await self.ctx.bot.wait_for('message', check=check)
        self.filename = fileName(msg.content, custom=True)
        await start_meeting(self.ctx, self.filename)

        self.clear_items()
        self.add_end_meeting_button()
        await interaction.followup.edit_message(message_id=interaction.message.id, content="회의가 시작되었습니다.", view=self)

    def add_end_meeting_button(self):
        end_button = Button(label="회의종료", style=discord.ButtonStyle.danger)
        end_button.callback = self.end_meeting_button
        self.add_item(end_button)

    async def end_meeting_button(self, interaction):
        await end_meeting(self.ctx, self.filename)
        await interaction.response.edit_message(content="회의가 종료되었습니다.", view=None)
