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

        members_with_role1 = [member.id for member in guild.members if role1 in member.roles]
        members_with_role2 = [member.id for member in guild.members if role2 in member.roles] if role2 else []

        total_members_needed = num_teams * members_per_team

        # Get the list of users with the specified roles
        roles_to_add = [
            guild.get_role(1127716398416797766),  # Equilibrado
            guild.get_role(1127716463478853702),  # Auxiliar
            guild.get_role(1127716528121446573),  # Defensivo
            guild.get_role(1127716546370871316),  # Ofensivo
            guild.get_role(1127716426594140160),  # Ágil
        ]

        members_with_roles = []
        for role in roles_to_add:
            members_with_role = [member.id for member in guild.members if role in member.roles]
            members_with_roles.extend(members_with_role)

        members_with_roles = list(set(members_with_roles))  # Remove duplicates

        # If there are not enough members with specified roles, fall back to randomly assigning users
        if len(members_with_roles) < total_members_needed:
            members_with_roles = random.sample(members_with_roles, min(len(members_with_roles), total_members_needed))

        # Distribute members into teams
        teams = [members_with_roles[i:i+members_per_team] for i in range(0, total_members_needed, members_per_team)]
        
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

        lista_equipos = []
        for index, team in enumerate(teams, start=1):
            miembros_equipo = " ".join([guild.get_member(member_id).mention for member_id in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

        await self.config.guild(guild).role_to_team.set_raw(str(role1.id), value=teams)
        if role2:
            await self.config.guild(guild).role_to_team.set_raw(str(role2.id), value=teams)

    async def _create_teams_and_channels_vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int, members_per_team: int):
        guild = ctx.guild

        # Similar logic as _create_teams_and_channels, combining users with specified roles
        roles_to_add = [
            guild.get_role(1127716398416797766),  # Equilibrado
            guild.get_role(1127716463478853702),  # Auxiliar
            guild.get_role(1127716528121446573),  # Defensivo
            guild.get_role(1127716546370871316),  # Ofensivo
            guild.get_role(1127716426594140160),  # Ágil
        ]

        members_with_roles1 = []
        for role in roles_to_add:
            members_with_role = [member.id for member in guild.members if role in member.roles]
            members_with_roles1.extend(members_with_role)

        members_with_roles1 = list(set(members_with_roles1))  # Remove duplicates

        members_with_roles2 = [member.id for member in guild.members if role2 in member.roles]

        # If there are not enough members with specified roles, fall back to randomly assigning users
        if len(members_with_roles1) < num_teams * members_per_team or len(members_with_roles2) < num_teams * members_per_team:
            members_with_roles1 = random.sample(members_with_roles1, min(len(members_with_roles1), num_teams * members_per_team))
            members_with_roles2 = random.sample(members_with_roles2, min(len(members_with_roles2), num_teams * members_per_team))

        odd_teams = [members_with_role1[i:i+members_per_team] for i in range(0, total_members_needed, members_per_team)]
        even_teams = [members_with_role2[i:i+members_per_team] for i in range(0, total_members_needed, members_per_team)]

        combined_teams = []
        for i in range(num_teams):
            if i % 2 == 0:
                combined_teams.append(odd_teams.pop(0))
            else:
                combined_teams.append(even_teams.pop(0))

        # Get the category
        category = guild.get_channel(1127625556247203861)

        # Create voice channels for each team within the specified category
        voice_channels = []
        for index, team in enumerate(combined_teams, start=1):
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

        lista_equipos = []
        for index, team in enumerate(combined_teams, start=1):
            miembros_equipo = " ".join([guild.get_member(member_id).mention for member_id in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

        await self.config.guild(guild).role_to_team.set_raw(str(role1.id), value=odd_teams)
        await self.config.guild(guild).role_to_team.set_raw(str(role2.id), value=even_teams)
