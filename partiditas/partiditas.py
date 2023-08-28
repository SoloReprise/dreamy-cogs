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
        """Comando para manejar batallas."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help("battle")

    @battle.command(name="inhouse")
    async def battle_inhouse(self, ctx, role: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Randomiza equipos con un rol específico y crea canales de voz."""
        guild = ctx.guild

        members_with_role = [member.id for member in guild.members if role in member.roles]

        total_members_needed = num_teams * members_per_team

        if len(members_with_role) < total_members_needed:
            await ctx.send("No hay suficientes miembros con el rol especificado.")
            return

        members_with_role = random.sample(members_with_role, min(len(members_with_role), total_members_needed))

        # Distribute members into teams
        teams = [members_with_role[i:i+members_per_team] for i in range(0, total_members_needed, members_per_team)]

        # Get the category
        category = guild.get_channel(1127625556247203861)

        # ... (Create voice channels and distribute members)

        await ctx.send("Equipos aleatorizados creados.")

        await self.config.guild(guild).role_to_team.set_raw(str(role.id), value=teams)

    @battle.command(name="vs")
    async def battle_vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Randomiza equipos con roles específicos y crea canales de voz."""
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

        # ... (Create voice channels and distribute members)

        await ctx.send("Equipos aleatorizados creados.")

        await self.config.guild(guild).role_to_team.set_raw(str(role1.id), value=teams)

    @battle.command(name="clear")
    async def battle_clear(self, ctx):
        """Elimina los canales de voz creados para el scrim."""
        guild = ctx.guild
        voice_channels = [channel for channel in guild.voice_channels if "◇║Equipo" in channel.name]

        for channel in voice_channels:
            await channel.delete()

        await ctx.send("Canales de voz de scrim eliminados.")