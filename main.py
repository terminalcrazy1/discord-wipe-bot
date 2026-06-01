import json
import discord
from discord import app_commands
from discord.ext import commands

valid_roles = ["builder", "farmer", "fighter"]

def parseInput(input: str):
    return input.strip().lower()

def hasRole(interaction: discord.Interaction, roles=valid_roles):
    for role in roles:
        if discord.utils.get(interaction.guild.roles, name=role) in interaction.user.roles:
            return True
    return False

class JoinWipeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Join Wipe", style=discord.ButtonStyle.success, custom_id="join_wipe_btn")
    async def join_wipe_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if hasRole(interaction, ["owns-rust"]):
            await interaction.response.send_message("See you on the spawn beach!", ephemeral=True)
            await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, name="wipe"))
        else:
            await interaction.response.send_message("Oops! It seems you don't own rust, please contact the web master.", ephemeral=True)

class WipeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all()
            )
    
    async def setup_hook(self):
        self.add_view(JoinWipeView())
        await self.tree.sync()

bot = WipeBot()

@bot.tree.command(name="wipe-schedule", description="Alerts @owns-rust users of an upcoming wipe")
@app_commands.describe(time="Format: MM-DD HH:MM")
async def wipe_schedule(interaction: discord.Interaction, time: str):
    role = discord.utils.get(interaction.guild.roles, name="owns-rust")
    await interaction.response.send_message(content=f"{role.mention} there will be a wipe at {time}. Click below to attend:", view=JoinWipeView())

@bot.tree.command(name="wipe-end", description="Alerts @wipe users about the end of the wipe")
async def wipe_end(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name="wipe")
    await interaction.response.send_message(content=f"{role.mention} the wipe has ended.")
    for member in role.members:
        await member.remove_roles(role)

@bot.tree.command(name="apply", description="Apply for a role")
@app_commands.describe(role="Builder, Farmer, or Fighter")
async def apply(interaction: discord.Interaction, role: str):
    if parseInput(role) not in valid_roles:
        await interaction.response.send_message("Oops! That role doesn't exist.", ephemeral=True)   
    elif not hasRole(interaction):
        parsed_role = parseInput(role)
        await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, name=parsed_role))
        await interaction.response.send_message(f"You have been granted the role {parsed_role}. See you on the spawn beach!", ephemeral=True)
    else:
        await interaction.response.send_message("Oops! You already have a role, please /quit and then try again.", ephemeral=True)
    
@bot.tree.command(name="quit", description="Quit a role")
async def quit(interaction: discord.Interaction):
    if hasRole(interaction):
        for role in valid_roles:
            if hasRole(interaction, [role]):
                await interaction.user.remove_roles(discord.utils.get(interaction.guild.roles, name=role))
                await interaction.response.send_message(f"You have been removed from the role {role}.", ephemeral=True)
                return
    else:
        await interaction.response.send_message("Oops! It seems you don't have a role.", ephemeral=True)
    
if __name__ == "__main__":
    creds = json.load(open("credentials.json"))
    bot.run(creds["BOT_TOKEN"])