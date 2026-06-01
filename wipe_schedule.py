import discord
import json
from helper import hasRole, parseInput

valid_roles = json.load(open("config.json"))["VALID_ROLES"]
eligible_role = json.load(open("config.json"))["ELIGIBLE_ROLE"]
wipe_role = json.load(open("config.json"))["WIPE_ROLE"]

class JoinWipeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Join Wipe", style=discord.ButtonStyle.success, custom_id="join_wipe_btn")
    async def join_wipe_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if hasRole(interaction, [f"{eligible_role}"]):
            await interaction.response.send_message("See you on the spawn beach!", ephemeral=True)
            await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, name=f"{wipe_role}"))
        else:
            await interaction.response.send_message(f"Oops! It seems you don't have the {eligible_role} role, please contact the web master.", ephemeral=True)

async def wipe_schedule_back(interaction: discord.Interaction, time: str):
    data = open("data.json", "w")
    data_dict = {"WIPE_SCHEDULE": time}
    json.dump(data_dict, data)
    data.close()

    role = discord.utils.get(interaction.guild.roles, name=f"{eligible_role}")
    await interaction.response.send_message(content=f"{role.mention} there will be a wipe at {time}. Click below to attend:", view=JoinWipeView())