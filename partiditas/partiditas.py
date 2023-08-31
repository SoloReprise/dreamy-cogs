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
        """Elimina los canales de voz creados para el enfrentamiento y resetea la información."""
        guild = ctx.guild
        voice_channels = [channel for channel in guild.voice_channels if "◇║Equipo" in channel.name]

        for channel in voice_channels:
            await channel.delete()

        await self.config.guild(guild).clear()
        await ctx.send("Canales de voz de enfrentamiento eliminados y datos reseteados.")

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
        
    async def _create_teams_and_channels_vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int, members_per_team: int):
        guild = ctx.guild

        members_with_role1 = [member for member in guild.members if role1 in member.roles]
        members_with_role2 = [member for member in guild.members if role2 in member.roles]

        total_members_needed = num_teams * members_per_team

        if len(members_with_role1) < num_teams or len(members_with_role2) < num_teams:
            await ctx.send("No hay suficientes miembros con los roles especificados.")
            return

        combined_teams = []
        for i in range(num_teams):
            if i % 2 == 0:
                team = random.sample(members_with_role1, members_per_team)
                members_with_role1 = [member for member in members_with_role1 if member not in team]
            else:
                team = random.sample(members_with_role2, members_per_team)
                members_with_role2 = [member for member in members_with_role2 if member not in team]

            combined_teams.append(team)

        position_roles = [1127716398416797766, 1127716463478853702, 1127716528121446573, 1127716546370871316, 1127716426594140160]

        available_players = list(set(members_with_role1 + members_with_role2))  # List of available players

        teams_with_positions = []

        for team_index, team in enumerate(combined_teams, start=1):
            assigned_positions = set()  # Reset assigned positions for each team
            team_positions = set()  # Keep track of positions assigned to this team
            team_with_positions = []

            for user in team:
                member_roles = [role.id for role in user.roles]
                position_id = None  # Initialize position_id to None

                # Check if the member has a pre-chosen position role
                pre_chosen_positions = [role_id for role_id in member_roles if role_id in position_roles]

                if pre_chosen_positions:
                    preferred_positions = [guild.get_role(position_id) for position_id in pre_chosen_positions]
                    await ctx.send(f"Se ha encontrado al jugador {user.mention}. Buscando posición [{', '.join(p.name for p in preferred_positions)}].")
                    valid_positions = [position for position in preferred_positions if position.id not in team_positions and position.id not in assigned_positions]

                    if valid_positions:
                        position = random.choice(valid_positions)
                    else:
                        available_positions = [position_id for position_id in position_roles if position_id not in team_positions and position_id not in assigned_positions]
                        if available_positions:
                            position_id = random.choice(available_positions)
                            position = guild.get_role(position_id)
                        else:
                            available_teams = [t for t in teams_with_positions if user in [u for u, _ in t] and len(t) < members_per_team]
                            if available_teams:
                                other_team = random.choice(available_teams)
                                other_team_positions = [pos for _, pos in other_team]
                                position = None
                                for pref_pos in preferred_positions:
                                    if pref_pos.id not in other_team_positions:
                                        position = pref_pos
                                        break
                                if position is None:
                                    await ctx.send(f"No se pudo encontrar una posición para {user.mention}.")
                                    continue
                            else:
                                await ctx.send(f"No se pudo encontrar una posición para {user.mention}.")
                                continue

                        team_positions.add(position.id)
                        assigned_positions.add(position.id)
                        await ctx.send(f"Posición encontrada. La posición de {user.mention} es {position.name} en el Equipo {team_index}")
                        team_with_positions.append((user, position))
                else:
                    await ctx.send(f"Se ha encontrado al jugador {user.mention}. No tiene marcada ninguna posición favorita. Buscando posición.")
                    available_positions = [position_id for position_id in position_roles if position_id not in team_positions and position_id not in assigned_positions]
                    if available_positions:
                        position_id = random.choice(available_positions)
                        position = guild.get_role(position_id)
                    else:
                        available_teams = [t for t in teams_with_positions if user in [u for u, _ in t] and len(t) < members_per_team]
                        if available_teams:
                            other_team = random.choice(available_teams)
                            other_team_positions = [pos for _, pos in other_team]
                            position = None
                            for pos_id in available_positions:
                                if pos_id not in other_team_positions:
                                    position = guild.get_role(pos_id)
                                    break
                            if position is None:
                                await ctx.send(f"No se pudo encontrar una posición para {user.mention}.")
                                continue
                        else:
                            await ctx.send(f"No se pudo encontrar una posición para {user.mention}.")
                            continue

                    team_positions.add(position.id)
                    assigned_positions.add(position.id)
                    await ctx.send(f"Posición encontrada. La posición de {user.mention} es {position.name} en el Equipo {team_index}")
                    team_with_positions.append((user, position))

                available_players.remove(user)  # Remove user from available players

            teams_with_positions.append((team_with_positions, assigned_positions))

        # Notify each team about their positions
        lista_equipos = []
        position_names = [guild.get_role(position_id).name for position_id in position_roles]
        for index, (team, assigned_positions) in enumerate(teams_with_positions, start=1):
            miembros_equipo = " ".join([member.mention for member, _ in team])
            equipo_info = f"Equipo {index}: {miembros_equipo}"
            for user, position_id in team:
                position_name = guild.get_role(position_id).name
                equipo_info += f"\n  - {user.mention}: {position_name}"
            lista_equipos.append(equipo_info)

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}\nPosiciones disponibles: [{', '.join(position_names)}]")

        # Create voice channels and move members
        category = guild.get_channel(1127625556247203861)
        voice_channels = []
        for index, team in enumerate(combined_teams, start=1):
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

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")
