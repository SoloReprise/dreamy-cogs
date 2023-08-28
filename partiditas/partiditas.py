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

    @commands.command()
    async def battle(self, ctx):
        """Comando para gestionar batallas."""
        pass  # No need to implement anything here as subcommands will handle it

    @battle.command(name="inhouse")
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def inhouse_battle(self, ctx, role: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Batalla interna aleatoria."""
        guild = ctx.guild
        await self._create_teams(ctx, role, num_teams, members_per_team)

    @battle.command(name="vs")
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def vs_battle(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Batalla entre dos roles."""
        guild = ctx.guild
        await self._create_teams(ctx, role1, num_teams, members_per_team)
        await self._create_teams(ctx, role2, num_teams, members_per_team)

    @battle.command(name="clear")
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def clear_battle(self, ctx):
        """Elimina los canales de voz creados para la batalla."""
        await self._clear_voice_channels(ctx)

    async def _create_teams(self, ctx, role: discord.Role, num_teams: int, members_per_team: int):
        """Crea equipos aleatorizados con un rol específico y canales de voz."""
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

        await self._handle_user_pairs(ctx, role, teams)
        
        lista_equipos = []
        for index, team in enumerate(teams, start=1):
            miembros_equipo = " ".join([guild.get_member(member_id).mention for member_id in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

        await self.config.guild(guild).role_to_team.set_raw(str(role.id), value=teams)

    async def _handle_user_pairs(self, ctx, role, teams):
        """Maneja las exclusiones de usuarios en el mismo equipo."""
        guild = ctx.guild
        user_pairs = await self.config.guild(guild).user_pairs()
        members_with_role = [member.id for member in guild.members if role in member.roles]

        for member_id, exclusion_id in user_pairs.items():
            if member_id in members_with_role and exclusion_id in members_with_role:
                member_team_index = next((i for i, team in enumerate(teams) if member_id in team), None)
                exclusion_team_index = next((i for i, team in enumerate(teams) if exclusion_id in team), None)
                if member_team_index is not None and exclusion_team_index is not None and member_team_index == exclusion_team_index:
                    # Swap the excluded member to another team
                    target_team = (exclusion_team_index + 1) % len(teams)
                    teams[exclusion_team_index].remove(exclusion_id)
                    teams[target_team].append(exclusion_id)

    async def _clear_voice_channels(self, ctx):
        """Elimina los canales de voz creados para la batalla."""
        guild = ctx.guild
        voice_channels = [channel for channel in guild.voice_channels if "◇║Equipo" in channel.name]

        for channel in voice_channels:
            await channel.delete()

        await ctx.send("Canales de voz de batalla eliminados.")