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

        # Extract members with the provided roles.
        members_with_role1 = list(set([member for member in guild.members if role1 in member.roles]))
        members_with_role2 = list(set([member for member in guild.members if role2 in member.roles]))

        if len(members_with_role1) < num_teams or len(members_with_role2) < num_teams:
            await ctx.send("No hay suficientes miembros con los roles especificados.")
            return

        combined_teams = []
        all_assigned_players = []

        # Divide members into teams.
        for i in range(num_teams):
            if i % 2 == 0:
                if len(members_with_role1) < members_per_team:
                    await ctx.send(f"No hay suficientes miembros con el rol {role1.name} para formar un equipo.")
                    return
                team = random.sample(members_with_role1, members_per_team)
                for member in team:
                    members_with_role1.remove(member)
            else:
                if len(members_with_role2) < members_per_team:
                    await ctx.send(f"No hay suficientes miembros con el rol {role2.name} para formar un equipo.")
                    return
                team = random.sample(members_with_role2, members_per_team)
                for member in team:
                    members_with_role2.remove(member)
            all_assigned_players.extend(team)
            combined_teams.append(team)

        position_roles = [1127716398416797766, 1127716463478853702, 1127716528121446573, 1127716546370871316, 1127716426594140160]

        teams_with_positions = []

        if members_per_team == 5:  # Position comprobation only for teams of 5 members.
            for team_index, team in enumerate(combined_teams):
                team_positions = set()
                team_with_positions = []

                for user_index, user in enumerate(team):
                    member_roles = set(role.id for role in user.roles)
                    valid_positions = list(set(position_roles) - team_positions)
                    assigned_position = None

                    # Notify about preferred positions.
                    preferred_positions = member_roles & set(position_roles)
                    if preferred_positions:
                        pref_names = ', '.join([guild.get_role(pos).name for pos in preferred_positions])
                        await ctx.send(f"Se ha encontrado al jugador {user.mention}. Buscando posición [{pref_names}].")

                    # Assign position based on preference or random.
                    for pos in preferred_positions:
                        if pos in valid_positions:
                            assigned_position = pos
                            break

                    # If the player's preferred positions are all occupied, try finding a subsequent team where they can fit.
                    if not assigned_position:
                        for subsequent_team in teams_with_positions[team_index+1:]:
                            free_positions = list(set(position_roles) - set([assigned_role[1] for assigned_role in subsequent_team]))
                            suitable_position = None
                            for pref_pos in preferred_positions:
                                if pref_pos in free_positions:
                                    suitable_position = pref_pos
                                    break
                            
                    # If a suitable position is found in a subsequent team, swap the players
                    if suitable_position:
                        swap_index = team_index + 1 + teams_with_positions[team_index+1:].index(subsequent_team)
                        swap_user = next(member for member, pos in combined_teams[swap_index] if pos == suitable_position)
                        
                        combined_teams[swap_index][combined_teams[swap_index].index(swap_user)] = user
                        combined_teams[team_index][user_index] = swap_user
                        
                        assigned_position = suitable_position
                        break

                    if assigned_position:
                        position_name = guild.get_role(assigned_position).name
                        team_positions.add(assigned_position)
                        team_with_positions.append((user, position_name))
                        await ctx.send(f"La posición de {user.mention} para el Equipo {team_index + 1} es {position_name}.")
                    else:
                        await ctx.send(f"No se pudo encontrar una posición para {user.mention}.")

                teams_with_positions.append(team_with_positions)

        # Notify about team compositions.
        position_names = [guild.get_role(position_id).name for position_id in position_roles]
        lista_equipos = []
        for index, team in enumerate(teams_with_positions, start=1):
            miembros_equipo = " ".join([member[0].mention for member in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}\nPosiciones disponibles: [{', '.join(position_names)}]")

        # Create voice channels and move members.
        category = guild.get_channel(1127625556247203861)
        for index, team in enumerate(combined_teams, start=1):
            voice_channel_name = f"◇║Equipo {index}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                guild.me: discord.PermissionOverwrite(connect=True)
            }
            voice_channel = await category.create_voice_channel(voice_channel_name, overwrites=overwrites)

            for member in team:
                if member.voice:
                    await member.move_to(voice_channel)
