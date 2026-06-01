import json
import discord

valid_roles = json.load(open("config.json"))["VALID_ROLES"]

def parseInput(input: str):
    return input.strip().lower()

def hasRole(interaction: discord.Interaction, roles: list[str]=valid_roles):
    for role in roles:
        if discord.utils.get(interaction.guild.roles, name=role) in interaction.user.roles:
            return True
    return False