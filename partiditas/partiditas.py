import discord
import random
from redbot.core import commands, Config

class Partiditas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier
        default_guild = {
            "role_to_team": {},  # Maps roles to team lists
            "user_pairs": {}     # Stores user pairs that shouldn't be on the same team
        }
        self.config.register_guild(**default_guild)

    @commands.group()
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def battle(self, ctx):
        """Comandos de batallas."""
        pass

    @battle.command(name="inhouse")
    async def battle_inhouse(self, ctx, role1: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Randomiza equipos con un rol específico y crea canales de voz."""
        guild = ctx.guild
        await self._perform_battle(ctx, [role1], num_teams, members_per_team)

    @battle.command(name="vs")
    async def battle_vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Randomiza equipos con dos roles específicos y crea canales de voz."""
        guild = ctx.guild
        await self._perform_battle_vs(ctx, role1, role2, num_teams, members_per_team)

async def _perform_battle_vs(self, ctx, role1, role2, num_teams, members_per_team):
    guild = ctx.guild

    members_with_role1 = [member.id for member in guild.members if role1 in member.roles]
    members_with_role2 = [member.id for member in guild.members if role2 in member.roles]

    total_members_needed = num_teams * members_per_team

    if len(members_with_role1) + len(members_with_role2) < total_members_needed:
        await ctx.send("No hay suficientes miembros con los roles especificados.")
        return

    members_with_role1 = random.sample(members_with_role1, min(len(members_with_role1), total_members_needed))
    members_with_role2 = random.sample(members_with_role2, min(len(members_with_role2), total_members_needed))

    combined_members = members_with_role1 + members_with_role2
    random.shuffle(combined_members)

    # Distribute members into teams
    teams = [combined_members[i:i+members_per_team] for i in range(0, total_members_needed, members_per_team)]

    # Get the category
    category = guild.get_channel(1127625556247203861)

    # Create voice channels for each team within the specified category
    voice_channels = []
    for index, team in enumerate(teams, start=1):
        voice_channel_name = f"◇║Equipo {index}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False),
            guild.me: discord.PermissionOverwrite(connect=True)
        }
        voice_channel = await category.create_voice_channel(voice_channel_name, overwrites=overwrites)
        voice_channels.append(voice_channel)

        for member_id in team:
            member = guild.get_member(member_id)
            if member.voice:
                await member.move_to(voice_channel)

    # Get user pairs to exclude from the same team
    user_pairs = await self.config.guild(guild).user_pairs()
    for member_id, exclusion_id in user_pairs.items():
        if member_id in combined_members and exclusion_id in combined_members:
            member_team_index = next((i for i, team in enumerate(teams) if member_id in team), None)
            exclusion_team_index = next((i for i, team in enumerate(teams) if exclusion_id in team), None)
            if member_team_index is not None and exclusion_team_index is not None and member_team_index == exclusion_team_index:
                # Swap the excluded member to another team
                target_team = (exclusion_team_index + 1) % num_teams
                teams[exclusion_team_index].remove(exclusion_id)
                teams[target_team].append(exclusion_id)

    lista_equipos = []
    for index, team in enumerate(teams, start=1):
        miembros_equipo = " ".join([guild.get_member(member_id).mention for member_id in team])
        lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

    equipos_unidos = "\n".join(lista_equipos)
    await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

    await self.config.guild(guild).role_to_team.set_raw("_".join(str(role.id) for role in [role1, role2]), value=teams)
    
    @battle.command(name="clear")
    async def battle_clear(self, ctx):
        """Elimina los canales de voz creados para el scrim."""
        guild = ctx.guild
        voice_channels = [channel for channel in guild.voice_channels if "◇║Equipo" in channel.name]

        for channel in voice_channels:
            await channel.delete()

        await ctx.send("Canales de voz de scrim eliminados.")
