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
        """Comandos para crear equipos y canales de voz para enfrentamientos."""
        pass

    @battle.command(name="inhouse")
    async def inhouse(self, ctx, role: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Randomiza equipos con un rol específico y crea canales de voz."""
        await self._create_teams_and_channels(ctx, role, None, num_teams, members_per_team)

    @battle.command(name="vs")
    async def vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Enfrenta a dos roles en equipos y crea canales de voz."""
        await self._create_teams_and_channels_vs(ctx, role1, role2, num_teams, members_per_team)

    @battle.command(name="clear")
    async def clearscrim(self, ctx):
        """Elimina los canales de voz creados para el enfrentamiento."""
        guild = ctx.guild
        voice_channels = [channel for channel in guild.voice_channels if "◇║Equipo" in channel.name]

        for channel in voice_channels:
            await channel.delete()

        await ctx.send("Canales de voz de enfrentamiento eliminados.")

    @battle.command(name="unteam")
    async def unteam(self, ctx, member1: discord.Member, member2: discord.Member):
        """Evita que dos usuarios estén en el mismo equipo."""
        if member1 == member2:
            await ctx.send("¡No puedes poner a la misma persona en la lista de exclusión!")
            return

        # Store the unteaming relationship using sorted IDs to avoid duplication
        sorted_ids = sorted([str(member1.id), str(member2.id)])
        await self.config.guild(ctx.guild).user_pairs.set_raw(sorted_ids[0], value=sorted_ids[1])

        await ctx.send(f"¡Los usuarios {member1.mention} y {member2.mention} no estarán en el mismo equipo!")
    
    @battle.command(name="unteamlist")
    async def unteam_list(self, ctx):
        """Muestra la lista de usuarios que no pueden estar en el mismo equipo."""
        user_pairs = await self.config.guild(ctx.guild).user_pairs()
        unteam_list = []
        for member_id, exclusion_id in user_pairs.items():
            member = ctx.guild.get_member(int(member_id))
            if exclusion_id:
                exclusion = ctx.guild.get_member(int(exclusion_id))
                if member and exclusion:
                    unteam_list.append(f"{member.mention} y {exclusion.mention}")
        if unteam_list:
            await ctx.send("Lista de usuarios que no pueden estar en el mismo equipo:\n" + "\n".join(unteam_list))
        else:
            await ctx.send("No hay casos de usuarios que no puedan estar en el mismo equipo.")

    @battle.command(name="ununteam")
    async def un_unteam(self, ctx, member1: discord.Member, member2: discord.Member):
        """Elimina un caso de usuarios que no pueden estar en el mismo equipo."""
        # Remove the unteaming relationship using sorted IDs
        sorted_ids = sorted([str(member1.id), str(member2.id)])
        await self.config.guild(ctx.guild).user_pairs.set_raw(sorted_ids[0], value=None)
        await self.config.guild(ctx.guild).user_pairs.set_raw(sorted_ids[1], value=None)
        await ctx.send(f"Caso de unteaming entre {member1.mention} y {member2.mention} eliminado.")
        
    async def _create_teams_and_channels(self, ctx, role1: discord.Role, role2: discord.Role = None, num_teams: int = 2, members_per_team: int = 5):
        guild = ctx.guild

        members_with_role1 = [member for member in guild.members if role1 in member.roles]
        members_with_role2 = [member for member in guild.members if role2 in member.roles] if role2 else []

        total_members_needed = num_teams * members_per_team

        if len(members_with_role1) + len(members_with_role2) < total_members_needed:
            await ctx.send("No hay suficientes miembros con los roles especificados.")
            return

        random.shuffle(members_with_role1)
        random.shuffle(members_with_role2)

        teams = []
        for _ in range(num_teams):
            team = []
            for _ in range(members_per_team):
                member = None
                if members_with_role1:
                    member = members_with_role1.pop()
                elif members_with_role2:
                    member = members_with_role2.pop()
                elif guild.members:
                    member = random.choice(guild.members)

                if member:
                    team.append(member)

            teams.append(team)

        await self._create_voice_channels(ctx, teams)

    async def _create_teams_and_channels_vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int, members_per_team: int):
        guild = ctx.guild

        members_with_role1 = [member for member in guild.members if role1 in member.roles]
        members_with_role2 = [member for member in guild.members if role2 in member.roles]

        total_members_needed = num_teams * members_per_team

        if len(members_with_role1) < num_teams or len(members_with_role2) < num_teams:
            await ctx.send("No hay suficientes miembros con los roles especificados.")
            return

        random.shuffle(members_with_role1)
        random.shuffle(members_with_role2)

        odd_teams = [members_with_role1[i:i+members_per_team] for i in range(0, total_members_needed, members_per_team)]
        even_teams = [members_with_role2[i:i+members_per_team] for i in range(0, total_members_needed, members_per_team)]

        combined_teams = []
        for i in range(num_teams):
            if i % 2 == 0:
                combined_teams.append(odd_teams.pop(0))
            else:
                combined_teams.append(even_teams.pop(0))

        await self._create_voice_channels(ctx, combined_teams)

    async def _create_voice_channels(self, ctx, teams):
        guild = ctx.guild
        category = guild.get_channel(1127625556247203861)

        voice_channels = []
        for index, team in enumerate(teams, start=1):
            voice_channel_name = f"◇║Equipo {index}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                guild.me: discord.PermissionOverwrite(connect=True)
            }
            voice_channel = await category.create_voice_channel(voice_channel_name, overwrites=overwrites)
            voice_channels.append(voice_channel)

            for member in team:
                if member.voice:
                    await member.move_to(voice_channel)

        await self._send_team_list(ctx, teams)
        await self._store_teams(ctx, teams)

    async def _send_team_list(self, ctx, teams):
        guild = ctx.guild
        lista_equipos = []
        for index, team in enumerate(teams, start=1):
            miembros_equipo = " ".join([member.mention for member in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

    async def _store_teams(self, ctx, teams):
        guild = ctx.guild
        role1_id = None
        role2_id = None

        for team in teams:
            for member in team:
                if role1_id is None and any(role.id == 1127716398416797766 for role in member.roles):
                    role1_id = member.roles[0].id
                if role2_id is None and any(role.id == 1127716463478853702 for role in member.roles):
                    role2_id = member.roles[1].id

        serialized_teams = [team.ids for team in teams]
        await self.config.guild(guild).role_to_team.set_raw(str(role1_id), value=serialized_teams)
        await self.config.guild(guild).role_to_team.set_raw(str(role2_id), value=serialized_teams)
