import json
import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime

def load_data():
    if not os.path.exists("data.json"):
        return {"karma": {}, "choices": {}}
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

class RoleChoiceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Builder", style=discord.ButtonStyle.primary, custom_id="choice_builder")
    async def builder_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.save_choice(interaction, "builder")

    @discord.ui.button(label="Farmer", style=discord.ButtonStyle.success, custom_id="choice_farmer")
    async def farmer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.save_choice(interaction, "farmer")

    @discord.ui.button(label="Fighter", style=discord.ButtonStyle.danger, custom_id="choice_fighter")
    async def fighter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.save_choice(interaction, "fighter")

    async def save_choice(self, interaction: discord.Interaction, choice: str):
        data = load_data()
        user_id = str(interaction.user.id)
        if "choices" not in data: data["choices"] = {}
        data["choices"][user_id] = choice
        save_data(data)
        await interaction.response.send_message(f"You have chosen **{choice}**.", ephemeral=True)

class ParticipateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Participate", style=discord.ButtonStyle.green, custom_id="participate_btn")
    async def participate_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="wipe")
        if role:
            await interaction.user.add_roles(role)
        await interaction.response.send_message("Awesome! Please choose your preferred role for the wipe:", view=RoleChoiceView(), ephemeral=True)

class RatingView(discord.ui.View):
    def __init__(self, rater_id: int, target_id: int, total_wipes: int):
        super().__init__(timeout=None)
        self.rater_id = rater_id
        self.target_id = target_id
        self.total_wipes = total_wipes

    async def record_rating(self, interaction: discord.Interaction, rating: int):
        data = load_data()
        target_str = str(self.target_id)
        
        if "karma" not in data:
            data["karma"] = {}
        if target_str not in data["karma"]:
            data["karma"][target_str] = 0.0
            
        data["karma"][target_str] += rating / self.total_wipes
        save_data(data)
        await interaction.response.edit_message(content=f"You rated them a {rating}.", view=None)

    @discord.ui.button(label="1", style=discord.ButtonStyle.danger)
    async def btn1(self, interaction: discord.Interaction, button: discord.ui.Button): await self.record_rating(interaction, 1)
    @discord.ui.button(label="2", style=discord.ButtonStyle.primary)
    async def btn2(self, interaction: discord.Interaction, button: discord.ui.Button): await self.record_rating(interaction, 2)
    @discord.ui.button(label="3", style=discord.ButtonStyle.primary)
    async def btn3(self, interaction: discord.Interaction, button: discord.ui.Button): await self.record_rating(interaction, 3)
    @discord.ui.button(label="4", style=discord.ButtonStyle.success)
    async def btn4(self, interaction: discord.Interaction, button: discord.ui.Button): await self.record_rating(interaction, 4)

class WipeBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all()
        )

    async def setup_hook(self):
        self.add_view(ParticipateView())
        self.add_view(RoleChoiceView())
        await self.tree.sync()
        check_wipe_schedule.start()

bot = WipeBot()

async def ensure_roles(guild):
    role_names = ["owns-rust", "wipe", "builder", "farmer", "fighter"]
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
    data["choices"] = {}
    save_data(data)
    
    role = discord.utils.get(interaction.guild.roles, name="owns-rust")
    mention = role.mention if role else "@owns-rust"
    
    await interaction.response.send_message(f"{mention} A new wipe is scheduled for {time_str}. Are you participating?", view=ParticipateView())

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
    if not wipe_role: return
    
    members = wipe_role.members
    total_wipes = len(members)
    if total_wipes == 0:
        if channel:
            await channel.send("Wipe started, but no one participated!")
        return

    num_builders = 1 if total_wipes <= 5 else 2
    remaining_slots = total_wipes - num_builders
    num_fighters = remaining_slots // 2
    num_farmers = remaining_slots - num_fighters

    choices = data.get("choices", {})
    karmas = data.get("karma", {})
    
    sorted_members = sorted(members, key=lambda m: karmas.get(str(m.id), 0.0), reverse=True)
    
    preferred = {"builder": [], "farmer": [], "fighter": []}
    for m in sorted_members:
        pref = choices.get(str(m.id))
        if pref in preferred:
            preferred[pref].append(m)
        else:
            preferred["farmer"].append(m)
            
    final_teams = {"builder": [], "farmer": [], "fighter": []}
    
    def fill_role(role_name, limit):
        while len(final_teams[role_name]) < limit and preferred[role_name]:
            final_teams[role_name].append(preferred[role_name].pop(0))
            
    fill_role("builder", num_builders)
    fill_role("fighter", num_fighters)
    fill_role("farmer", num_farmers)
    
    leftovers = []
    for r in ["builder", "farmer", "fighter"]:
        leftovers.extend(preferred[r])
        
    for role_name, limit in [("builder", num_builders), ("fighter", num_fighters), ("farmer", num_farmers)]:
        while len(final_teams[role_name]) < limit and leftovers:
            final_teams[role_name].append(leftovers.pop(0))
            
    teams_str = "**Final Teams:**\n"
    for r_name, team_members in final_teams.items():
        r = discord.utils.get(guild.roles, name=r_name)
        if r:
            for m in team_members:
                await m.add_roles(r)
        
        team_mentions = ", ".join([m.mention for m in team_members]) if team_members else "None"
        teams_str += f"**{r_name.capitalize()}**: {team_mentions}\n"
        
    if channel:
        await channel.send(teams_str)

@bot.tree.command(name="wipe-cancel", description="Cancel the scheduled wipe")
async def wipe_cancel(interaction: discord.Interaction, message: str):
    data = load_data()
    data["schedule"] = None
    save_data(data)
    
    guild = interaction.guild
    roles_to_strip = ["wipe", "builder", "farmer", "fighter"]
    roles = [discord.utils.get(guild.roles, name=rn) for rn in roles_to_strip]
    roles = [r for r in roles if r]
    
    await interaction.response.defer()
    
    for member in guild.members:
        member_roles = [r for r in roles if r in member.roles]
        if member_roles:
            try:
                await member.remove_roles(*member_roles)
            except discord.Forbidden:
                pass
                
    await interaction.followup.send(f"Wipe cancelled: {message}")

@bot.tree.command(name="wipe-end", description="End the wipe")
async def wipe_end(interaction: discord.Interaction):
    guild = interaction.guild
    wipe_role = discord.utils.get(guild.roles, name="wipe")
    
    if not wipe_role or not wipe_role.members:
        await interaction.response.send_message("No ongoing wipe found or no participants.", ephemeral=True)
        return
        
    wipe_members = wipe_role.members
    total_wipes = len(wipe_members)
    
    await interaction.response.send_message("The wipe has ended! Check your DMs to rate your teammates.")
    
    for rater in wipe_members:
        for target in wipe_members:
            if rater.id == target.id: continue
            try:
                await rater.send(f"Rate **{target.display_name}** (1-4):", view=RatingView(rater.id, target.id, total_wipes))
            except discord.Forbidden:
                pass
                
    roles_to_strip = ["wipe", "builder", "farmer", "fighter"]
    roles = [discord.utils.get(guild.roles, name=rn) for rn in roles_to_strip]
    roles = [r for r in roles if r]
    
    for member in guild.members:
        member_roles = [r for r in roles if r in member.roles]
        if member_roles:
            try:
                await member.remove_roles(*member_roles)
            except discord.Forbidden:
                pass

if __name__ == "__main__":
    with open("credentials.json", "r") as f:
        creds = json.load(f)
    bot.run(creds["BOT_TOKEN"])
