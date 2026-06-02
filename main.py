import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from helper import parseInput, hasRole
from quit import quit_back
from apply import apply_back
from wipe_end import wipe_end_back
from wipe_schedule import wipe_schedule_back, JoinWipeView
from datetime import datetime

valid_roles = json.load(open("config.json"))["VALID_ROLES"]
eligible_role = json.load(open("config.json"))["ELIGIBLE_ROLE"]
wipe_role = json.load(open("config.json"))["WIPE_ROLE"]

class WipeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all()
            )
    
    async def setup_hook(self):
        self.add_view(JoinWipeView())
        is_wiping.start(0)
        await self.tree.sync()

bot = WipeBot()

@bot.tree.command(name="wipe-schedule", description=f"Alerts {eligible_role} users of an upcoming wipe")
@app_commands.describe(time="Format: MM-DD HH:MM")
async def wipe_schedule(interaction: discord.Interaction, time: str):
    await wipe_schedule_back(interaction, time)

@bot.tree.command(name="wipe-end", description=f"Alerts {wipe_role} users about the end of the wipe")
async def wipe_end(interaction: discord.Interaction):
    await wipe_end_back(interaction)

@bot.tree.command(name="apply", description="Apply for a role")
@app_commands.describe(role="Builder, Farmer, or Fighter")
async def apply(interaction: discord.Interaction, role: str):
    await apply_back(interaction, role)
    
@bot.tree.command(name="quit", description="Quit a role")
async def quit(interaction: discord.Interaction):
    await quit_back(interaction)

@tasks.loop(seconds = 10)
async def is_wiping(counted: int):
    if datetime.now().strftime("%m-%d %H:%M") == json.load(open("data.json"))["WIPE_SCHEDULE"]:
        if not counted == 1:
            counted = 1
            for guild in bot.guilds:
                role = discord.utils.get(guild.roles, name=f"{wipe_role}")
                await guild.system_channel.send(content=f"{role.mention} it is wipe time! Get on the beach.")
    if not (datetime.now().strftime("%m-%d %H:%M") == json.load(open("data.json"))["WIPE_SCHEDULE"]) and counted == 1:
        counted = 0

if __name__ == "__main__":
    creds = json.load(open("credentials.json"))
    bot.run(creds["BOT_TOKEN"])