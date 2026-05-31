import json
import discord
import discord.ext

class WipeBot(commands.bot):
    def __init__(self):
        super().__init__(
            command_prefix="/", 
            intents=discord.Intents.default(),
            intents.members=True
            )
    
    async def setup_hook(self):
        await self.tree.sync()
        