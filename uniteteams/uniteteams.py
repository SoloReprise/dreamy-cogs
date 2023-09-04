import discord
from discord.utils import get
from discord.ext import commands
from redbot.core import commands, Config
import asyncio
from typing import Union
from datetime import datetime

class UniteTeams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567810)
        self.config.register_guild(uniteteams={})

    @commands.guild_only()
    @commands.command()
    async def uniteteams(self, ctx, subcommand: str, *, leader_or_role_name: str = None):
        if ctx.guild.owner != ctx.author:
            await ctx.send("¡Solo el dueño del servidor puede usar este comando!")
            return
        
        if subcommand == "create":
            if not leader_or_role_name:
                await ctx.send("¡Por favor, menciona a un líder y proporciona un nombre de equipo!")
                return
            
            # Splitting the leader mention and the team name
            leader_mention, _, team_name = leader_or_role_name.partition(' ')
            
            leader = None
            try:
                leader_id = int(leader_mention.strip("<@!>").strip())
                leader = ctx.guild.get_member(leader_id)
            except ValueError:
                await ctx.send("¡Por favor, menciona a un líder válido!")
                return

            await self.create_team(ctx, leader, team_name)
        
        elif subcommand == "delete":
            if not leader_or_role_name:
                await ctx.send("¡Por favor, menciona un equipo válido para eliminar o escribe su nombre!")
                return
            
            await self.delete_team(ctx, leader_or_role_name)

        elif subcommand == "list":
            await self.list_teams(ctx)

        elif subcommand == "clean":
            await self.clean_teams(ctx)

        else:
            await ctx.send("Subcomando desconocido.")

    async def create_team(self, ctx, leader: discord.Member, team_name: str):        # Split the team_name to capture the acronym
        *team_name_parts, acronym = team_name.split()

        # Join back the team name parts without the acronym
        team_name = ' '.join(team_name_parts)

        # Validate the acronym
        if len(acronym) > 5 or not acronym.isupper():
            await ctx.send("El acrónimo debe estar en mayúsculas, contener a lo sumo 5 caracteres y puede incluir símbolos.")
            return
        
        if not isinstance(leader, discord.Member):
            await ctx.send("¡Por favor menciona a un líder válido!")
            return

        if discord.utils.get(ctx.guild.roles, name=team_name):
            await ctx.send("¡Este equipo ya existe!")
            return

        role = await ctx.guild.create_role(name=team_name, mentionable=False)
        scrims_role = ctx.guild.get_role(1147980466205507668)
        capitanes_role = ctx.guild.get_role(1147984884997050418)

        if scrims_role is None:
            await ctx.send("¡No se encontró el rol de scrims!")
            return

        if capitanes_role is None:
            await ctx.send("¡No se encontró el rol de Capitanes!")
            return

        await leader.add_roles(role, scrims_role, capitanes_role)

        # Extract acronym from the team name
        acronym = team_name.split()[-1].upper()

        await self.config.guild(ctx.guild).uniteteams.set_raw(team_name, value={
            "role_id": role.id,
            "leader_id": leader.id,
            "acronym": acronym,  # Store the acronym in the config data
            "members": []  # Adding an empty list for members
        })
        await ctx.send(f"¡Equipo {team_name} ({acronym}) creado con {leader.mention} como líder!")

    async def delete_team(self, ctx, leader_or_role_name: str):
        # If the input is a mention (for a role), let's try to process it as such.
        if leader_or_role_name.startswith("<@&") and leader_or_role_name.endswith(">"):
            leader_or_role_name = leader_or_role_name.strip("<@&>")  # Strip to get the ID
            team_role = discord.utils.get(ctx.guild.roles, id=int(leader_or_role_name))
        else:
            team_role = discord.utils.get(ctx.guild.roles, name=leader_or_role_name)

        # If we didn't find a role based on the input, send an error message
        if not team_role:
            await ctx.send("¡Este equipo no existe!")
            return

        team_data = await self.config.guild(ctx.guild).uniteteams.get_raw(team_role.name, default=None)
        if not team_data:
            await ctx.send("¡Este equipo no está registrado!")
            return

        # Remove the specified roles from the leader
        leader = ctx.guild.get_member(team_data["leader_id"])
        if leader:
            scrims_role = ctx.guild.get_role(1147980466205507668)
            capitanes_role = ctx.guild.get_role(1147984884997050418)
            
            roles_to_remove = []
            if scrims_role:
                roles_to_remove.append(scrims_role)
            if capitanes_role:
                roles_to_remove.append(capitanes_role)

            if roles_to_remove:
                await leader.remove_roles(*roles_to_remove)

        # Delete the team role and clear from the config
        await team_role.delete()
        await self.config.guild(ctx.guild).uniteteams.clear_raw(team_role.name)
        await ctx.send(f"¡Equipo {team_role.name} eliminado!")

    async def list_teams(self, ctx):
        teams_data = await self.config.guild(ctx.guild).uniteteams()
        if not teams_data:
            await ctx.send("¡No hay equipos creados!")
            return
        
        message = "Equipos:\n"
        for team, data in teams_data.items():
            leader = ctx.guild.get_member(data["leader_id"])
            acronym = data.get("acronym", "N/A")  # Just to be safe, in case an acronym wasn't added

            # Check if "members" key exists in the data, if not, create an empty list
            members_list = data.get("members", [])
            members = [ctx.guild.get_member(member_id).mention for member_id in members_list if ctx.guild.get_member(member_id)]

            acronym = data.get("acronym", "N/A")  # Get the acronym, default to "N/A" if not found
            message += f"- **{team}** ({acronym}) (Líder: {leader.mention if leader else 'Desconocido'}, Miembros: {', '.join(members) if members else 'Ninguno'})\n"

        await ctx.send(message)

    async def clean_teams(self, ctx):
        teams_data = await self.config.guild(ctx.guild).uniteteams()
        for team, data in teams_data.items():
            role = ctx.guild.get_role(data["role_id"])
            if role:
                await role.delete()

        await self.config.guild(ctx.guild).uniteteams.clear()
        await ctx.send("¡Todos los equipos han sido eliminados!")


# TEAMS
    async def add_team_members(self, ctx, team_name, members):
        team_data = await self.config.guild(ctx.guild).uniteteams.get_raw(team_name)
        
        for member in members:
            # Get member object from mention
            member_obj = ctx.guild.get_member(member)
            
            if not member_obj:
                await ctx.send(f"Couldn't find member {member}")
                continue

            if member_obj.id not in team_data["members"]:
                team_data["members"].append(member_obj.id)

        await self.config.guild(ctx.guild).uniteteams.set_raw(team_name, value=team_data)

    async def list_team_members(self, ctx):
        # Check if the user is a captain of any team
        teams_data = await self.config.guild(ctx.guild).uniteteams()
        user_team = None
        for team, data in teams_data.items():
            if ctx.author.id == data["leader_id"]:
                user_team = team
                break

        if not user_team:
            await ctx.send("¡No eres el capitán de ningún equipo!")
            return

        team_data = teams_data[user_team]
        leader = ctx.guild.get_member(team_data["leader_id"])

        # Extract acronym
        acronym = team_data.get("acronym", "N/A")  # Get the acronym, default to "N/A" if not found
        
        # Check if "members" key exists in the team_data, if not, create an empty list
        members_list = team_data.get("members", [])
        members = [ctx.guild.get_member(member_id).mention for member_id in members_list if ctx.guild.get_member(member_id)]
        
        await ctx.send(
            f"Equipo: **{user_team}**\n"
            f"Acrónimo: **{acronym}**\n"  # Displaying the acronym here
            f"Líder: {leader.mention}\n"
            f"Miembros: {', '.join(members) if members else 'Ninguno'}"
        )

    @commands.guild_only()
    @commands.command()
    async def team(self, ctx, subcommand: str = None, *args):
        """Command usable only by the Captain of each team."""

        # Ensure the user is a captain.
        captain_teams = await self.config.guild(ctx.guild).uniteteams()
        user_team = None
        for team_name, data in captain_teams.items():
            if data["leader_id"] == ctx.author.id:
                user_team = team_name
                break

        if not user_team:
            await ctx.send("¡No eres capitán de ningún equipo!")
            return

        # If no subcommand is provided, show an error.
        if not subcommand:
            await ctx.send("¡Por favor proporciona un subcomando válido (add, delete, rename)!")
            return
        
        elif subcommand == "acronym":
            new_acronym = " ".join(args).upper()
            if not new_acronym or len(new_acronym.split()) > 1 or len(new_acronym) > 5:
                await ctx.send("¡Por favor proporciona un acrónimo válido de una sola palabra y no más de 5 caracteres!")
                return

            team_data = await self.config.guild(ctx.guild).uniteteams.get_raw(user_team)
            team_data["acronym"] = new_acronym
            await self.config.guild(ctx.guild).uniteteams.set_raw(user_team, value=team_data)
            
            await ctx.send(f"El acrónimo del equipo {user_team} ha sido actualizado a {new_acronym}.")
    
        # Subcommand: add
        if subcommand == "add":
            await self.add_team_members(ctx, user_team, args)
            members_to_add = [member for member in ctx.message.mentions]
            if not members_to_add:
                await ctx.send("¡Por favor menciona a los miembros que deseas agregar!")
                return
            
            # Add roles to mentioned members
            scrims_role = ctx.guild.get_role(1147980466205507668)
            team_role = discord.utils.get(ctx.guild.roles, name=user_team)
            for member in members_to_add:
                await member.add_roles(scrims_role, team_role)
            await ctx.send(f"Miembros añadidos al equipo {user_team}.")
        
        # Subcommand: delete
        elif subcommand == "delete":
            members_to_remove = [member for member in ctx.message.mentions]
            if not members_to_remove:
                await ctx.send("¡Por favor menciona a los miembros que deseas eliminar!")
                return
            
            # Remove roles from mentioned members
            scrims_role = ctx.guild.get_role(1147980466205507668)
            team_role = discord.utils.get(ctx.guild.roles, name=user_team)
            for member in members_to_remove:
                await member.remove_roles(scrims_role, team_role)
            await ctx.send(f"Miembros eliminados del equipo {user_team}.")

        # Subcommand: list        
        if subcommand == "list":
            await self.list_team_members(ctx)

        # Subcommand: rename
        elif subcommand == "rename":
            new_name = " ".join(args)
            if not new_name:
                await ctx.send("¡Por favor proporciona un nuevo nombre para el equipo!")
                return
            
            team_role = discord.utils.get(ctx.guild.roles, name=user_team)
            if not team_role:
                await ctx.send("¡Error al obtener el rol del equipo!")
                return
            
            await team_role.edit(name=new_name)
            # Update the name in the config
            team_data = await self.config.guild(ctx.guild).uniteteams.get_raw(user_team)
            await self.config.guild(ctx.guild).uniteteams.set_raw(new_name, value=team_data)
            await self.config.guild(ctx.guild).uniteteams.clear_raw(user_team)
            
            await ctx.send(f"El equipo {user_team} ahora se llama {new_name}.")

        else:
            await ctx.send("Subcomando desconocido.")

    ## Scrims
    @commands.guild_only()
    @commands.command(aliases=["scrims"])
    async def scrim(self, ctx, *, target: Union[discord.Member, discord.Role, str]):
        # Ensure the user is a captain
        captain_teams = await self.config.guild(ctx.guild).uniteteams()
        challenger_team = None
        for team_name, data in captain_teams.items():
            if data["leader_id"] == ctx.author.id:
                challenger_team = team_name
                break

        if not challenger_team:
            await ctx.send("¡No eres capitán de ningún equipo!")
            return

        # Identify the challenged team
        if isinstance(target, discord.Member):  # captain mention
            challenged_team = [team for team, data in captain_teams.items() if data["leader_id"] == target.id][0]
        elif isinstance(target, discord.Role):  # role mention
            challenged_team = target.name
        else:  # team name
            challenged_team = target

        if not challenged_team or challenged_team == challenger_team:
            await ctx.send("¡No puedes retarte a ti mismo!")
            return

        # Create challenge message
        challenged_captain = get(ctx.guild.members, id=captain_teams[challenged_team]["leader_id"])
        challenge_msg = await ctx.send(
            f"¡Atención, {challenged_captain.mention}! {challenger_team} ha retado a {challenged_team} a unas scrims! ¿Aceptas el desafío?"
        )
        await challenge_msg.add_reaction("✅")
        await challenge_msg.add_reaction("❌")

        def check(reaction, user):
            return user == challenged_captain and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == challenge_msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("El tiempo ha terminado para aceptar el desafío.")
        else:
            if str(reaction.emoji) == "✅":
                # Create category and channels
                category_name = f"【 {captain_teams[challenger_team]['acronym']} vs {captain_teams[challenged_team]['acronym']} 】"
                category_position = get(ctx.guild.categories, id=1127625556247203861).position
                category = await ctx.guild.create_category_channel(category_name, position=category_position)
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    get(ctx.guild.roles, id=1127785805969113238): discord.PermissionOverwrite(read_messages=True, send_messages=True),  # Mod role
                    get(ctx.guild.roles, name=challenger_team): discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    get(ctx.guild.roles, name=challenged_team): discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }

                text_channel = await ctx.guild.create_text_channel('❃║scrim-general', category=category, overwrites=overwrites)
                await text_channel.send(
                    f"¡Atención, {get(ctx.guild.roles, name=challenger_team).mention} y {get(ctx.guild.roles, name=challenged_team).mention}! "
                    f"¡Ya pueden empezar vuestras scrims! Tenéis este chat para organizaros como deseéis. GLHF!"
                )
                voice_channel1 = await ctx.guild.create_voice_channel(f'❃║{challenger_team}', category=category, overwrites=overwrites)
                voice_channel2 = await ctx.guild.create_voice_channel(f'❃║{challenged_team}', category=category, overwrites=overwrites)

                # Start a background task for activity monitoring
                self.bot.loop.create_task(self.monitor_scrim_activity(text_channel, voice_channel1, voice_channel2, category))

            elif str(reaction.emoji) == "❌":
                await ctx.send("Desafío rechazado.")

    async def monitor_scrim_activity(self, text_channel, voice_channel1, voice_channel2, category):
        await asyncio.sleep(1800)  # Wait for 30 minutes

        # Check for inactivity
        last_message = await text_channel.history(limit=1).flatten()
        last_message = last_message[0] if last_message else None

        if not last_message or (datetime.utcnow() - last_message.created_at).seconds >= 1800:  # No new messages in the last 30 mins
            if len(voice_channel1.members) == 0 and len(voice_channel2.members) == 0:  # No members in voice channels
                await category.delete(reason="Inactivity during scrims.")

    @commands.command()
    async def scrim_end(self, ctx):
        captain_teams = await self.config.guild(ctx.guild).uniteteams()
        user_is_captain_of = [team_name for team_name, data in captain_teams.items() if data["leader_id"] == ctx.author.id]
        
        # Check if the command is being used in a scrim channel
        if ctx.channel.category and "【" in ctx.channel.category.name and "】" in ctx.channel.category.name:
            teams_involved = ctx.channel.category.name.replace("【", "").replace("】", "").split(" vs ")
            
            # Check intersection of teams involved in the scrim and teams the user is captain of, or if the author is the guild owner
            if set(teams_involved).intersection(user_is_captain_of) or ctx.author == ctx.guild.owner:
                await ctx.channel.category.delete(reason=f"Scrim ended by {ctx.author.name}.")
            else:
                await ctx.send("¡No tienes permisos para terminar estas scrims!")
        else:
            await ctx.send("¡Este comando solo puede ser utilizado en canales de scrims!")