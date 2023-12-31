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

        # Inform all players in the matches
        all_players = [player for pair in self.combined_teams for team in pair for player in team]
        for player in all_players:
            await player.send("Combate cancelado. Entra en United Legacy para saber más.")

    @battle.command(name="end")
    async def clearscrim(self, ctx):
        """Elimina los canales de voz creados para el enfrentamiento y resetea la información."""
        guild = ctx.guild
        voice_channels = [channel for channel in guild.voice_channels if "◇║Equipo" in channel.name]

        # Inform all players in the matches
        all_players = [player for pair in self.combined_teams for team in pair for player in team]
        for player in all_players:
            await player.send("¡Combate finalizado! ¡Recordad dar !gg a vuestros compas de equipo y a vuestros rivales!")

        # Move users back to their original voice channels
        for channel in voice_channels:
            for member in channel.members:
                if member.id in self.user_original_voice_channels:
                    original_channel = self.user_original_voice_channels[member.id]
                    if original_channel in guild.voice_channels:  # Check if the original channel still exists
                        try:
                            await member.move_to(original_channel)
                        except discord.DiscordException as e:
                            await ctx.send(f"Error al mover a {member.name}: {str(e)}")
                    else:
                        await ctx.send(f"El canal original para {member.name} ya no existe.")

        # Delete voice channels
        for channel in voice_channels:
            try:
                await channel.delete()
            except discord.DiscordException as e:
                await ctx.send(f"Error al eliminar el canal {channel.name}: {str(e)}")

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
        await self._create_teams_and_channels(ctx, role, None, num_teams, members_per_team, inhouse=True)
    
    @battle.command(name="vs")
    async def vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int, members_per_team: int):
        """Randomiza equipos con dos roles y crea canales de voz."""
        await self._create_teams_and_channels(ctx, role1, role2, num_teams, members_per_team)

    async def _create_teams_and_channels(self, ctx, role1: discord.Role, role2: discord.Role = None, num_teams: int = 2, members_per_team: int = 5, inhouse: bool = False):
        guild = ctx.guild

        self.combined_teams = []
        self.user_original_voice_channels = {}  # Store original voice channels

        # Extract members with the provided roles.
        members_with_role1 = [member for member in guild.members if role1 in member.roles]
        if role2:
            members_with_role2 = [member for member in guild.members if role2 in member.roles]
        else:
            members_with_role2 = []

        # Check if we have enough members from each role to form the teams
        if len(members_with_role1) < members_per_team or len(members_with_role2) < members_per_team:
            await ctx.send("No hay suficientes miembros en uno de los roles especificados para formar equipos.")
            return

        # Shuffle the members to ensure randomization.
        random.shuffle(members_with_role1)
        random.shuffle(members_with_role2)

        # Form teams iteratively
        all_selected_players = set()  # We'll use a set to ensure unique members
        teams = []

        if inhouse:
            # Only use members with role1 since we're in 'inhouse' mode
            all_members = members_with_role1[:]
            random.shuffle(all_members)
            for _ in range(num_teams):
                current_team = []
                while len(current_team) < members_per_team and all_members:
                    member = all_members.pop()
                    current_team.append(member)
                    all_selected_players.add(member)
                teams.append(current_team)
        else:
            # This is the existing logic for the 'vs' command, distinguishing between odd and even teams
            for i in range(num_teams):
                current_team = []
                
                if i % 2 == 0:  # Odd team (e.g., Team 1, Team 3)
                    while len(current_team) < members_per_team and members_with_role1:
                        member = members_with_role1.pop(0)
                        if member not in all_selected_players:
                            current_team.append(member)
                            all_selected_players.add(member)
                            if member in members_with_role2: 
                                members_with_role2.remove(member)
                else:  # Even team
                    while len(current_team) < members_per_team and members_with_role2:
                        member = members_with_role2.pop(0)
                        if member not in all_selected_players:
                            current_team.append(member)
                            all_selected_players.add(member)
                            if member in members_with_role1: 
                                members_with_role1.remove(member)

                teams.append(current_team)

        self.combined_teams = [teams[i:i+2] for i in range(0, len(teams), 2)]  # Group teams into battling pairs
        
        selected_players_mentions = [member.mention for member in all_selected_players]
        #await ctx.send(f"Jugadores seleccionados:\n{', '.join(selected_players_mentions)}")

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

        unassigned_members = []
        assigned_members = set()  # Added this to keep track of members that have been assigned

        # Start the assignment for members based on their preference count
        for pref_count in range(1, 6):  
            for user in members_by_preference_count[pref_count]:
                if user in assigned_members:  # Check if user has already been assigned
                    continue

                member_roles = set(role.id for role in user.roles)
                preferred_positions = member_roles & set(position_roles)
                
                if preferred_positions:
                    pref_names = ', '.join([guild.get_role(pos).name for pos in preferred_positions])
                    #await ctx.send(f"Se ha encontrado al jugador {user.mention}. Buscando posición [{pref_names}].")
                
                assigned = False
                for team_index, team in enumerate(teams, start=1):
                    if user not in team:
                        continue  # user is not in this team, skip
                    
                    valid_positions = list(set(position_roles) - positions_by_team[team_index])
                    for pref in preferred_positions:
                        if pref in valid_positions:
                            positions_by_team[team_index].add(pref)
                            position_name = guild.get_role(pref).name
                            teams_with_positions[team_index - 1].append((user, position_name))
                            #await ctx.send(f"La posición de {user.mention} para el Equipo {team_index} es {position_name}.")
                            assigned = True
                            assigned_members.add(user)  # Add user to assigned members
                            break

                    if assigned:
                        break  # exit loop as position has been found
                
                if not assigned:
                    #await ctx.send(f"No se pudo encontrar una posición preferida para {user.mention} en ningún equipo.")
                    unassigned_members.append(user)

        # Updated Fallback Logic
        for user in all_members:  # Now we'll iterate over all_members to ensure everyone gets assigned
            if user not in assigned_members:  # Only consider those who haven't been assigned yet
                for team_index, team in enumerate(teams, start=1):
                    if user not in team:
                        continue  # user is not in this team, skip

                    valid_positions = list(set(position_roles) - positions_by_team[team_index])
                    if valid_positions:
                        assigned_position = random.choice(valid_positions)
                        positions_by_team[team_index].add(assigned_position)
                        position_name = guild.get_role(assigned_position).name
                        teams_with_positions[team_index - 1].append((user, position_name))
                        #await ctx.send(f"La posición de {user.mention} para el Equipo {team_index} es {position_name}.")
                        break

        # Notify about team compositions.
        position_names = [guild.get_role(position_id).name for position_id in position_roles]
        lista_equipos = []
        for index, team in enumerate(teams_with_positions, start=1):
            miembros_equipo = " ".join([member[0].mention for member in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

        # Create voice channels and move members.
        category = guild.get_channel(1127625556247203861)
        for index, team in enumerate(teams, start=1):
            voice_channel_name = f"◇║Equipo {index}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True),
                guild.me: discord.PermissionOverwrite(connect=True)
            }
            voice_channel = await category.create_voice_channel(voice_channel_name, overwrites=overwrites)

            for member in team:
                if member.voice:
                    self.user_original_voice_channels[member.id] = member.voice.channel  # Populate the dictionary
                    await member.move_to(voice_channel)

        # Create a list of team leaders based on odd teams.
        self.team_leaders = [team[0] for index, team in enumerate(teams, start=1) if index % 2 == 1]
        for leader in self.team_leaders:
            await leader.send("¡Hola! Se te ha encargado la tarea de crear la sala para el combate. Por favor, envíamelo para que pueda reenviárselo al resto de jugadores.")
       
        for index, team in enumerate(teams, start=1):
            if index % 2 == 1:  # Odd team
                leader = team[0]
                for member in team[1:]:  # Excluding the leader
                    await member.send(f"¡Hola! La persona encargada de crear la sala para el combate es {leader.mention}. Por favor, espera mientras me envía el código de sala.")
            else:  # Even team
                corresponding_odd_team = teams[index-2]
                leader_of_odd_team = corresponding_odd_team[0]
                for member in team:  # All members of the even team
                    await member.send(f"¡Hola! La persona encargada de crear la sala para el combate es {leader_of_odd_team.mention}. Por favor, espera mientras me envía el código de sala.")
   
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if message is DM and author is a team leader.
        if isinstance(message.channel, discord.DMChannel) and message.author in self.team_leaders:
            if message.content.isdigit() and len(message.content) == 8:  # Check if the message contains an 8-digit number.
                await message.author.send("Código recibido. Se lo enviaré al resto de jugadores.")

                # Fetch the team of the leader.
                team_idx = [i for i, combined_team in enumerate(self.combined_teams) for team in combined_team if message.author in team][0]
                
                # Relay code to both the teams (odd and even).
                for team in self.combined_teams[team_idx]:
                    for member in team:
                        if member != message.author:  # Exclude the leader
                            await member.send(f"Código para el combate proporcionado por {message.author.display_name}: {message.content}")

            else:
                await message.author.send("El código proporcionado no es válido. Por favor, envía un número de 8 dígitos.")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def guerra(self, ctx):
        embed = discord.Embed(
            title="Guerra campal",
            color=0x7eaf4c,
            description="¡Es la hora de la Guerra Campal! ¡Es hora de defender a tu Mewtwo! Muestra tu lealtad a tu equipo y defiende tu color. ¿Rojo o azul? ¿X o Y?. ¡Hoy comienza a decidirse todo!\n\n¡Reacciona con :yellow_circle: a este mensaje para confirmar tu disponibilidad!"
        )
        message = await ctx.send(embed=embed)
        await message.add_reaction("🟡")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '🟡'

        reaction, _ = await self.bot.wait_for('reaction_add', check=check)

        member = ctx.author

        role1 = discord.utils.get(ctx.guild.roles, id=1147254156491509780)
        role2 = discord.utils.get(ctx.guild.roles, id=1147253975893159957)
        new_role1 = discord.utils.get(ctx.guild.roles, id=1150034423157362719)
        new_role2 = discord.utils.get(ctx.guild.roles, id=1150034469638635570)

        if role1 in member.roles:
            await member.add_roles(new_role1)
        elif role2 in member.roles:
            await member.add_roles(new_role2)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def warclear(self, ctx):
        new_role1 = discord.utils.get(ctx.guild.roles, id=1150034423157362719)
        new_role2 = discord.utils.get(ctx.guild.roles, id=1150034469638635570)

        for member in ctx.guild.members:
            if new_role1 in member.roles:
                await member.remove_roles(new_role1)
            if new_role2 in member.roles:
                await member.remove_roles(new_role2)

        await ctx.send("Roles cleared.")
