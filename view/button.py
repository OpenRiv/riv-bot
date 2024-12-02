import discord
from discord.ui import Button

class CustomButton(Button):
    def __init__(self, label, style, callback):
        super().__init__(label=label, style=style)
        self.callback_func = callback

    async def callback(self, interaction):
        await self.callback_func(interaction)
