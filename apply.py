import discord
import json
from helper import hasRole, parseInput

valid_roles = json.load(open("config.json"))["VALID_ROLES"]
eligible_role = json.load(open("config.json"))["ELIGIBLE_ROLE"]
wipe_role = json.load(open("config.json"))["WIPE_ROLE"]

async def apply_back(interaction: discord.Interaction, role: str):
    if parseInput(role) not in valid_roles:
        await interaction.response.send_message("Oops! That role doesn't exist.", ephemeral=True)   
    elif not hasRole(interaction):
        parsed_role = parseInput(role)
        await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, name=parsed_role))
        await interaction.response.send_message(f"You have been granted the role {parsed_role}. See you on the spawn beach!", ephemeral=True)
    else:
        await interaction.response.send_message("Oops! You already have a role, please /quit and then try again.", ephemeral=True)