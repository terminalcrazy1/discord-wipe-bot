import json
import discord
from discord import app_commands
from discord.ext import commands

valid_roles = ["builder", "farmer", "fighter"]

class JoinWipeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Join Wipe", style=discord.ButtonStyle.success, custom_id="join_wipe_btn")
    async def join_wipe_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if any(role.name.lower() in valid_roles for role in interaction.user.roles):
            await interaction.response.send_message("See you on the spawn beach!", ephemeral=True)
            wipe_role = discord.utils.find(lambda r: r.name.lower() == "wipe", interaction.guild.roles)
            if wipe_role:
                await interaction.user.add_roles(wipe_role)
        else:
            await interaction.response.send_message("Oops! It seems you don't have a role, please /apply and then try again.", ephemeral=True)

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
    await interaction.response.send_message(content="@owns-rust, there will be a wipe at {time}. Click below to attend:", view=JoinWipeView())

@bot.tree.command(name="wipe-end", description="Alerts @wipe users about the end of the wipe")
async def wipe_end(interaction: discord.Interaction):
    await interaction.response.send_message(content="@wipe, the wipe has ended.")
    wipe_role = discord.utils.get(interaction.guild.roles, name="wipe")
    for member in wipe_role.members:
        await member.remove_roles(wipe_role)

@bot.tree.command(name="apply", description="Apply for a role")
@app_commands.describe(role="Builder, Farmer, or Fighter")
async def apply(interaction: discord.Interaction, role: str):
    if role.lower() not in valid_roles:
        await interaction.response.send_message("Invalid role! Please choose Builder, Farmer, or Fighter.", ephemeral=True)
        return

    if not any(r.name.lower() in valid_roles for r in interaction.user.roles):
        role_obj = discord.utils.find(lambda r: r.name.lower() == role.lower(), interaction.guild.roles)
        if role_obj:
            await interaction.user.add_roles(role_obj)
            await interaction.response.send_message(f"You have been granted the role {role}. See you on the spawn beach!", ephemeral=True)
        else:
            await interaction.response.send_message(f"Role {role} does not exist in this server.", ephemeral=True)
    else:
        await interaction.response.send_message("Oops! You already have a role, please /quit and then try again.", ephemeral=True)
    
@bot.tree.command(name="quit", description="Quit a role")
async def quit(interaction: discord.Interaction):
    if any(r.name.lower() in valid_roles for r in interaction.user.roles):
        await interaction.response.send_message("You have been removed from your role.", ephemeral=True)
        for role_name in valid_roles:
            role_obj = discord.utils.find(lambda r: r.name.lower() == role_name, interaction.user.roles)
            if role_obj:
                await interaction.user.remove_roles(role_obj)
    else:
        await interaction.response.send_message("Oops! It seems you don't have a role.", ephemeral=True)
    
if __name__ == "__main__":
    creds = json.load(open("credentials.json"))
    bot.run(creds["BOT_TOKEN"])