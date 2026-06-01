import discord
import json
from helper import hasRole, valid_roles

valid_roles = json.load(open("config.json"))["VALID_ROLES"]
eligible_role = json.load(open("config.json"))["ELIGIBLE_ROLE"]
wipe_role = json.load(open("config.json"))["WIPE_ROLE"]

async def quit_back(interaction: discord.Interaction):
    if hasRole(interaction):
        for role in valid_roles:
            if hasRole(interaction, [role]):
                await interaction.user.remove_roles(discord.utils.get(interaction.guild.roles, name=role))
                await interaction.response.send_message(f"You have been removed from the role {role}. Your rock will be missed :(", ephemeral=True)
                return
    else:
        await interaction.response.send_message("Oops! It seems you don't have a role.", ephemeral=True)