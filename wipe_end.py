import discord
import json
from helper import hasRole, parseInput

valid_roles = json.load(open("config.json"))["VALID_ROLES"]
eligible_role = json.load(open("config.json"))["ELIGIBLE_ROLE"]
wipe_role = json.load(open("config.json"))["WIPE_ROLE"]

async def wipe_end_back(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name=f"{wipe_role}")
    await interaction.response.send_message(content=f"{role.mention} the wipe has ended. See you next time!")
    for member in role.members:
        await member.remove_roles(role)