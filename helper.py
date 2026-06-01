import discord

def parseInput(input: str):
    return input.strip().lower()

def hasRole(interaction: discord.Interaction, roles: list[str]):
    for role in roles:
        if discord.utils.get(interaction.guild.roles, name=role) in interaction.user.roles:
            return True
    return False