import discord
from redbot.core import commands, Config

class UniteTeams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567810)
        self.config.register_guild(uniteteams={})

    @commands.guild_only()
    @commands.command()
    async def uniteteams(self, ctx, subcommand: str, leader_or_role: discord.Member=None, *, team_name: str = None):
        if ctx.guild.owner != ctx.author:
            await ctx.send("¡Solo el dueño del servidor puede usar este comando!")
            return

        if subcommand == "create":
            if not leader_or_role or not team_name:
                await ctx.send("¡Por favor, menciona a un líder y proporciona un nombre de equipo!")
                return
            await self.create_team(ctx, leader_or_role, team_name)

        elif subcommand == "delete":
            await self.delete_team(ctx, leader_or_role)  # Assuming leader_or_role here will be a role

        elif subcommand == "list":
            await self.list_teams(ctx)

        elif subcommand == "clean":
            await self.clean_teams(ctx)

        else:
            await ctx.send("Subcomando desconocido.")

    async def create_team(self, ctx, leader: discord.Member, team_name: str):
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

        await self.config.guild(ctx.guild).uniteteams.set_raw(team_name, value={"role_id": role.id, "leader_id": leader.id})
        await ctx.send(f"¡Equipo {team_name} creado con {leader.mention} como líder!")

    async def delete_team(self, ctx, team_role: discord.Role):
        team_data = await self.config.guild(ctx.guild).uniteteams.get_raw(team_role.name, default=None)
        if not team_data:
            await ctx.send("¡Este equipo no existe!")
            return

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
            message += f"- {team} (Líder: {leader.mention if leader else 'Desconocido'})\n"

        await ctx.send(message)

    async def clean_teams(self, ctx):
        teams_data = await self.config.guild(ctx.guild).uniteteams()
        for team, data in teams_data.items():
            role = ctx.guild.get_role(data["role_id"])
            if role:
                await role.delete()

        await self.config.guild(ctx.guild).uniteteams.clear()
        await ctx.send("¡Todos los equipos han sido eliminados!")
