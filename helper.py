import json
import discord

#from discord import app_commands
#from discord.ext import commands

valid_roles = json.load(open("config.json"))["VALID_ROLES"]

def parseInput(input: str):
    return input.strip().lower()

def hasRole(interaction: discord.Interaction, roles: list[str]=valid_roles):
    for role in roles:
        if discord.utils.get(interaction.guild.roles, name=role) in interaction.user.roles:
            return True
    return False