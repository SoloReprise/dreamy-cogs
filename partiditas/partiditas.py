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
        self.combined_teams = []
        self.team_leaders = []
        self.user_original_voice_channels = {}  # Initialize the dictionary 

    @commands.group()
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def battle(self, ctx):
        """Comandos para crear equipos y canales de voz para enfrentamientos."""
        pass

    @battle.command(name="clear")
    async def clearscrim(self, ctx):
        """Elimina los canales de voz creados para el enfrentamiento y resetea la información."""
        guild = ctx.guild
        voice_channels = [channel for channel in guild.voice_channels if "◇║Equipo" in channel.name]

        # Move users back to their original voice channels
        for channel in voice_channels:
            for member in channel.members:
                if member.id in self.user_original_voice_channels:
                    original_channel = self.user_original_voice_channels[member.id]
                    await member.move_to(original_channel)

        # Delete voice channels
        for channel in voice_channels:
            await channel.delete()

        await self.config.guild(guild).clear()

        # Clear out the team data.
        self.combined_teams = []
        self.team_leaders = []
        self.user_original_voice_channels = {}  # Clear the stored original voice channels

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
        
    @battle.command(name="inhouse")
    async def inhouse(self, ctx, role: discord.Role, num_teams: int = 2, members_per_team: int = 5):
        """Randomiza equipos con un rol específico y crea canales de voz."""
        await self._create_teams_and_channels(ctx, role, None, num_teams, members_per_team)

    @battle.command(name="vs")
    async def vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int, members_per_team: int):
        """Randomiza equipos con dos roles y crea canales de voz."""
        await self._create_teams_and_channels(ctx, role1, role2, num_teams, members_per_team)

    async def _create_teams_and_channels(self, ctx, role1: discord.Role, role2: discord.Role = None, num_teams: int = 2, members_per_team: int = 5):
        guild = ctx.guild

        self.combined_teams = []
        self.user_original_voice_channels = {}

        members_with_role1 = [member for member in guild.members if role1 in member.roles]
        members_with_role2 = [member for member in guild.members if role2 in member.roles] if role2 else []

        total_members_needed = num_teams * members_per_team
        if len(members_with_role1) + len(members_with_role2) < total_members_needed:
            await ctx.send("No hay suficientes miembros con los roles especificados.")
            return

        random.shuffle(members_with_role1)
        random.shuffle(members_with_role2)

        selected_from_role1 = random.sample(members_with_role1, min(len(members_with_role1), members_per_team * ((num_teams + 1) // 2)))
        selected_from_role2 = random.sample(members_with_role2, min(len(members_with_role2), members_per_team * (num_teams // 2)))

        all_selected_players = []
        for i in range(members_per_team):
            if i < len(selected_from_role1):
                all_selected_players.append(selected_from_role1[i])
            if i < len(selected_from_role2):
                all_selected_players.append(selected_from_role2[i])

        selected_players_mentions = [member.mention for member in all_selected_players]
        await ctx.send(f"Jugadores seleccionados:\n{', '.join(selected_players_mentions)}")

        teams = [all_selected_players[i:i + members_per_team] for i in range(0, len(all_selected_players), members_per_team)]
        # For role assignment
        position_roles = [1127716398416797766, 1127716463478853702, 1127716528121446573, 1127716546370871316, 1127716426594140160]
        teams_with_positions = [[] for _ in teams]
        positions_by_team = {i: set() for i, _ in enumerate(teams, start=1)}

        # Split the members based on the number of preferences they have.
        all_members = [user for team in teams for user in team]
        members_by_preference_count = {i: [] for i in range(6)}
        for user in all_members:
            member_roles = set(role.id for role in user.roles)
            position_count = len(member_roles & set(position_roles))
            members_by_preference_count[position_count].append(user)

        for pref_count in range(1, 6):  # From 1 preference to 5 preferences
            for user in members_by_preference_count[pref_count]:
                member_roles = set(role.id for role in user.roles)
                preferred_positions = member_roles & set(position_roles)
                if preferred_positions:
                    pref_names = ', '.join([guild.get_role(pos).name for pos in preferred_positions])
                    await ctx.send(f"Se ha encontrado al jugador {user.mention}. Buscando posición [{pref_names}].")

                position_found = False
                for team_index, team in enumerate(teams, start=1):
                    if user not in team:
                        continue  # user is not in this team, skip

                    valid_positions = list(set(position_roles) - positions_by_team[team_index])
                    for pos in preferred_positions:
                        if pos in valid_positions:
                            positions_by_team[team_index].add(pos)
                            position_name = guild.get_role(pos).name
                            teams_with_positions[team_index - 1].append((user, position_name))
                            await ctx.send(f"La posición de {user.mention} para el Equipo {team_index} es {position_name}.")
                            position_found = True
                            break  # exit inner loop as position has been found

                    if position_found:
                        break  # exit outer loop as position has been found

                if not position_found:
                    await ctx.send(f"No se pudo encontrar una posición preferida para {user.mention} en ningún equipo.")

        # Handle members with no preference or all preferences.
        for user in members_by_preference_count[0] + members_by_preference_count[5]:
            position_found = False
            for team_index, team in enumerate(teams, start=1):
                if user not in team:
                    continue  # user is not in this team, skip

                valid_positions = list(set(position_roles) - positions_by_team[team_index])
                if valid_positions:
                    assigned_position = random.choice(valid_positions)
                    positions_by_team[team_index].add(assigned_position)
                    position_name = guild.get_role(assigned_position).name
                    teams_with_positions[team_index - 1].append((user, position_name))
                    await ctx.send(f"La posición de {user.mention} para el Equipo {team_index} es {position_name}.")
                    position_found = True
                    break

            if not position_found:
                await ctx.send(f"No se pudo encontrar una posición para {user.mention} en ningún equipo.")

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
        for index, team in enumerate(teams, start=1):
            voice_channel_name = f"◇║Equipo {index}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                guild.me: discord.PermissionOverwrite(connect=True)
            }
            voice_channel = await category.create_voice_channel(voice_channel_name, overwrites=overwrites)

            for member in team:
                if member.voice:
                    self.user_original_voice_channels[member.id] = member.voice.channel  # Populate the dictionary
                    await member.move_to(voice_channel)

        # Create a list of team leaders based on odd teams.
        self.team_leaders = [team[0] for index, team in enumerate(teams, start=1) if index % 2 == 1]

        #for leader in self.team_leaders:
            #await leader.send("¡Hola! Eres el encargado de crear la sala para el combate. Por favor, envíamelo para que pueda reenviárselo al resto de jugadores.")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if message is DM and author is a team leader.
        if isinstance(message.channel, discord.DMChannel) and message.author in self.team_leaders:
            if message.content.isdigit() and len(message.content) == 8:  # Check if the message contains an 8-digit number.
                await message.author.send("Código recibido. Se lo enviaré al resto de jugadores.")

                # Fetch the team of the leader.
                team_idx = [i for i, team in enumerate(self.combined_teams) if message.author in team][0]
                
                # Relay code to both the teams (odd and even).
                for member in self.combined_teams[team_idx] + self.combined_teams[team_idx + 1]:
                    await member.send(f"Código para el combate proporcionado por {message.author.display_name}: {message.content}")

            else:
                await message.author.send("El código proporcionado no es válido. Por favor, envía un número de 8 dígitos.")

