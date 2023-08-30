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
        
    async def _create_teams_and_channels_vs(self, ctx, role1: discord.Role, role2: discord.Role, num_teams: int, members_per_team: int):
        guild = ctx.guild

        members_with_role1 = [member for member in guild.members if role1 in member.roles]
        members_with_role2 = [member for member in guild.members if role2 in member.roles]

        total_members_needed = num_teams * members_per_team

        if len(members_with_role1) < num_teams or len(members_with_role2) < num_teams:
            await ctx.send("No hay suficientes miembros con los roles especificados.")
            return

        odd_teams = [random.sample(members_with_role1, members_per_team) for _ in range(num_teams)]
        even_teams = [random.sample(members_with_role2, members_per_team) for _ in range(num_teams)]

        combined_teams = []
        for i in range(num_teams):
            if i % 2 == 0:
                combined_teams.append(odd_teams[i])
            else:
                combined_teams.append(even_teams[i])

        # Check if team size is 5
        if members_per_team == 5:
            position_roles = [1127716398416797766, 1127716463478853702, 1127716528121446573, 1127716546370871316, 1127716426594140160]
            random.shuffle(position_roles)

            for team in combined_teams:
                assigned_positions = set()

                # Create a dictionary to keep track of users and their preferred positions
                user_preferred_positions = {}

                for member in team:
                    member_roles = [role.id for role in member.roles]

                    # Check if the member has a pre-chosen position role
                    pre_chosen_positions = [role_id for role_id in member_roles if role_id in position_roles]

                    if pre_chosen_positions:
                        user_preferred_positions[member] = pre_chosen_positions

                # Assign roles to users with a single preferred role
                users_with_single_preferred_role = [user for user, positions in user_preferred_positions.items() if len(positions) == 1]
                for user in users_with_single_preferred_role:
                    position_id = user_preferred_positions[user][0]
                    position_role = guild.get_role(position_id)
                    await ctx.send(f"{user.mention}, tu posición en el equipo es: {position_role.name}")
                    assigned_positions.add(position_id)
                    del user_preferred_positions[user]

                # Assign roles to users with multiple preferred roles
                users_with_multiple_preferred_roles = [user for user, positions in user_preferred_positions.items() if len(positions) > 1]
                for user in users_with_multiple_preferred_roles:
                    valid_positions = [position for position in user_preferred_positions[user] if position not in assigned_positions]
                    if valid_positions:
                        chosen_position = random.choice(valid_positions)
                        position_role = guild.get_role(chosen_position)
                        await ctx.send(f"{user.mention}, tu posición en el equipo es: {position_role.name}")
                        assigned_positions.add(chosen_position)
                        del user_preferred_positions[user]

                # Assign remaining positions randomly
                remaining_positions = [role_id for role_id in position_roles if role_id not in assigned_positions]
                for user in user_preferred_positions.keys():
                    if not remaining_positions:
                        break

                    valid_positions = [position for position in user_preferred_positions[user] if position in remaining_positions]
                    if valid_positions:
                        chosen_position = random.choice(valid_positions)
                    else:
                        chosen_position = random.choice(remaining_positions)

                    position_role = guild.get_role(chosen_position)
                    await ctx.send(f"{user.mention}, tu posición en el equipo es: {position_role.name}")
                    assigned_positions.add(chosen_position)
                    remaining_positions.remove(chosen_position)

                # Assign positions to users without preferred roles
                users_without_preferred_roles = [user for user in team if user not in user_preferred_positions.keys()]
                for user in users_without_preferred_roles:
                    if not remaining_positions:
                        break

                    chosen_position = random.choice(remaining_positions)
                    position_role = guild.get_role(chosen_position)
                    await ctx.send(f"{user.mention}, tu posición en el equipo es: {position_role.name}")
                    remaining_positions.remove(chosen_position)

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

            for member in team:
                if member and member.voice:
                    await member.move_to(voice_channel)

        lista_equipos = []
        for index, team in enumerate(combined_teams, start=1):
            miembros_equipo = " ".join([member.mention for member in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")