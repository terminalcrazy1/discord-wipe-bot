import json
import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime

def load_data():
    if not os.path.exists("data.json"):
        return {"accepted_roles": {}}
    with open("data.json", "r") as f:
        data = json.load(f)
        if "accepted_roles" not in data:
            data["accepted_roles"] = {}
        return data

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

class AdminApprovalView(discord.ui.View):
    def __init__(self, applicant_id: int, requested_role: str, guild_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.requested_role = requested_role.strip()
        self.guild_id = guild_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = bot.get_guild(self.guild_id)
        if not guild:
            await interaction.followup.send("Guild not found.", ephemeral=True)
            return
            
        applicant = guild.get_member(self.applicant_id)
        if not applicant:
            await interaction.followup.send("User is no longer in the server.", ephemeral=True)
            return

        data = load_data()
        
        # Remove old role if exists
        old_role_name = data["accepted_roles"].get(str(self.applicant_id))
        if old_role_name:
            old_role = discord.utils.get(guild.roles, name=old_role_name)
            if old_role and old_role in applicant.roles:
                try:
                    await applicant.remove_roles(old_role)
                except discord.Forbidden:
                    pass

        # Find or create new role
        new_role = discord.utils.get(guild.roles, name=self.requested_role)
        if not new_role:
            try:
                new_role = await guild.create_role(name=self.requested_role)
            except discord.Forbidden:
                await interaction.followup.send("Missing permissions to create roles.", ephemeral=True)
                return

        # Give new role
        try:
            await applicant.add_roles(new_role)
        except discord.Forbidden:
            pass

        data["accepted_roles"][str(self.applicant_id)] = self.requested_role

        if str(self.applicant_id) in data.get("pending_wipe_joins", []):
            wipe_role = discord.utils.get(guild.roles, name="wipe")
            if wipe_role:
                try:
                    await applicant.add_roles(wipe_role)
                except discord.Forbidden:
                    pass
            if "pending_wipe_joins" in data:
                data["pending_wipe_joins"].remove(str(self.applicant_id))

        save_data(data)

        # Update view
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(content=f"{interaction.message.content}\n\n**Result:** Accepted", view=self)
        
        # Notify user
        try:
            await applicant.send(f"Your application for **{self.requested_role}** has been accepted!")
        except discord.Forbidden:
            pass

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild = bot.get_guild(self.guild_id)
        
        # Update view
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(content=f"{interaction.message.content}\n\n**Result:** Denied", view=self)

        if not guild: return
        applicant = guild.get_member(self.applicant_id)
        if applicant:
            try:
                await applicant.send(f"Your application for **{self.requested_role}** has been denied.")
            except discord.Forbidden:
                pass

class ApplicationModal(discord.ui.Modal, title='Role Application'):
    role_text = discord.ui.TextInput(
        label='What role are you applying for?',
        style=discord.TextStyle.short,
        placeholder='Builder',
        required=True
    )
    
    def __init__(self, guild_id: int = None):
        super().__init__()
        self.custom_guild_id = guild_id
        
    async def on_submit(self, interaction: discord.Interaction):
        valid_roles = ["builder", "farmer", "fighter"]
        if self.role_text.value.strip().lower() not in valid_roles:
            await interaction.response.send_message("Invalid role. Please apply for Builder, Farmer, or Fighter.", ephemeral=True)
            return

        guild_id = self.custom_guild_id or interaction.guild_id
        guild = bot.get_guild(guild_id) if guild_id else None
        owner = guild.owner if guild else None
        
        if owner:
            try:
                await owner.send(
                    f"Application from {interaction.user.mention} ({interaction.user}):\n"
                    f"**Role:** {self.role_text.value}",
                    view=AdminApprovalView(interaction.user.id, self.role_text.value, guild_id)
                )
            except discord.Forbidden:
                pass
        await interaction.response.send_message("Your application has been sent to the server owner.", ephemeral=True)

class ApplyView(discord.ui.View):
    def __init__(self, guild_id: int = None):
        super().__init__(timeout=None)
        self.custom_guild_id = guild_id
        if guild_id:
            for child in self.children:
                child.custom_id = os.urandom(16).hex()

    @discord.ui.button(label="Apply for Role", style=discord.ButtonStyle.primary, custom_id="apply_role_btn")
    async def apply_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_id = self.custom_guild_id or interaction.guild_id
        await interaction.response.send_modal(ApplicationModal(guild_id))

class JoinWipeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Wipe", style=discord.ButtonStyle.success, custom_id="join_wipe_btn")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        valid_roles = ["builder", "farmer", "fighter"]
        
        if not interaction.guild:
            await interaction.response.send_message("This can only be used in a server.", ephemeral=True)
            return

        has_role = any(role.name.lower() in valid_roles for role in interaction.user.roles)
        
        if has_role:
            wipe_role = discord.utils.get(interaction.guild.roles, name="wipe")
            if wipe_role:
                try:
                    await interaction.user.add_roles(wipe_role)
                    await interaction.response.send_message("You have successfully joined the wipe!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("I don't have permission to assign the wipe role.", ephemeral=True)
            else:
                await interaction.response.send_message("The wipe role doesn't exist.", ephemeral=True)
        else:
            data = load_data()
            if "pending_wipe_joins" not in data:
                data["pending_wipe_joins"] = []
            if str(interaction.user.id) not in data["pending_wipe_joins"]:
                data["pending_wipe_joins"].append(str(interaction.user.id))
                save_data(data)

            try:
                guild_id = interaction.guild.id
                await interaction.user.send("You need a role to join the wipe. Click below to apply for a role:", view=ApplyView(guild_id))
                await interaction.response.send_message("I've sent you a DM with instructions to apply for a role.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("You need a role to join the wipe. Please enable DMs to apply.", ephemeral=True)

class WipeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all()
        )

    async def setup_hook(self):
        self.add_view(ApplyView())
        self.add_view(JoinWipeView())
        await self.tree.sync()
        check_wipe_schedule.start()

bot = WipeBot()

async def ensure_roles(guild):
    role_names = ["owns-rust", "wipe"]
    for name in role_names:
        if not discord.utils.get(guild.roles, name=name):
            await guild.create_role(name=name)

@bot.tree.command(name="wipe-schedule", description="Schedule a wipe [mm-dd hh:mm]")
async def wipe_schedule(interaction: discord.Interaction, time_str: str):
    try:
        now = datetime.now()
        dt = datetime.strptime(f"{now.year}-{time_str}", "%Y-%m-%d %H:%M")
        if dt < now:
            dt = dt.replace(year=now.year + 1)
    except ValueError:
        await interaction.response.send_message("Invalid format. Use mm-dd hh:mm", ephemeral=True)
        return

    await ensure_roles(interaction.guild)
    
    data = load_data()
    data["schedule"] = dt.timestamp()
    data["guild_id"] = interaction.guild.id
    data["channel_id"] = interaction.channel.id
    data["pending_wipe_joins"] = []
    save_data(data)
    
    role = discord.utils.get(interaction.guild.roles, name="owns-rust")
    mention = role.mention if role else "@owns-rust"
    
    await interaction.response.send_message(f"{mention} A new wipe is scheduled for {time_str}.", view=JoinWipeView())

@tasks.loop(minutes=1)
async def check_wipe_schedule():
    data = load_data()
    if not data.get("schedule"): return
    
    now = datetime.now().timestamp()
    if now >= data["schedule"]:
        guild_id = data.get("guild_id")
        channel_id = data.get("channel_id")
        guild = bot.get_guild(guild_id)
        if not guild: return
        channel = guild.get_channel(channel_id)
        
        await trigger_wipe(guild, channel, data)
        
        data["schedule"] = None
        save_data(data)

async def trigger_wipe(guild, channel, data):
    wipe_role = discord.utils.get(guild.roles, name="wipe")
    
    if channel:
        if wipe_role and wipe_role.members:
            mentions = ", ".join(m.mention for m in wipe_role.members)
            await channel.send(f"Wipe started! Participants: {mentions}")
        else:
            await channel.send("Wipe started, but no one has the wipe role!")

@bot.tree.command(name="wipe-cancel", description="Cancel the scheduled wipe")
async def wipe_cancel(interaction: discord.Interaction, message: str):
    data = load_data()
    data["schedule"] = None
    data["pending_wipe_joins"] = []
    save_data(data)
    
    guild = interaction.guild
    wipe_role = discord.utils.get(guild.roles, name="wipe")
    
    await interaction.response.defer()
    
    if wipe_role:
        for member in wipe_role.members:
            try:
                await member.remove_roles(wipe_role)
            except discord.Forbidden:
                pass
                
    await interaction.followup.send(f"Wipe cancelled: {message}")

@bot.tree.command(name="wipe-end", description="End the wipe")
async def wipe_end(interaction: discord.Interaction):
    data = load_data()
    data["pending_wipe_joins"] = []
    save_data(data)

    guild = interaction.guild
    wipe_role = discord.utils.get(guild.roles, name="wipe")
    
    if not wipe_role or not wipe_role.members:
        await interaction.response.send_message("No ongoing wipe found or no participants.", ephemeral=True)
        return
        
    await interaction.response.send_message("The wipe has ended!")
    
    for member in wipe_role.members:
        try:
            await member.remove_roles(wipe_role)
        except discord.Forbidden:
            pass

@bot.tree.command(name="wipe-apply", description="Apply for a role")
async def wipe_apply(interaction: discord.Interaction):
    await interaction.response.send_modal(ApplicationModal())

if __name__ == "__main__":
    with open("credentials.json", "r") as f:
        creds = json.load(f)
    bot.run(creds["BOT_TOKEN"])
