import discord
from redbot.core import commands, Config

class UniteTeams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(teams=[])

    @commands.guild_only()
    @commands.command()
    async def uniteteams(self, ctx, subcommand: str, *args):
        if ctx.guild.owner != ctx.author:
            await ctx.send("¡Solo el dueño del servidor puede usar este comando!")
            return
        
        if subcommand == "create":
            await self.create_team(ctx, *args)
        elif subcommand == "delete":
            await self.delete_team(ctx, *args)
        else:
            await ctx.send("Subcomando desconocido.")

    async def create_team(self, ctx, leader: discord.Member, team_name: str):
        if discord.utils.get(ctx.guild.roles, name=team_name):
            await ctx.send("¡Este equipo ya existe!")
            return

        role = await ctx.guild.create_role(name=team_name, mentionable=False)
        scrims_role = ctx.guild.get_role(1147980466205507668)

        if scrims_role is None:
            await ctx.send("¡No se encontró el rol de scrims!")
            return

        await leader.add_roles(role, scrims_role)

        await self.config.guild(ctx.guild).teams.set_raw(team_name, value={"role_id": role.id, "leader_id": leader.id})
        await ctx.send(f"¡Equipo {team_name} creado con {leader.mention} como líder!")

    async def delete_team(self, ctx, team_role: discord.Role):
        team_data = await self.config.guild(ctx.guild).teams.get_raw(team_role.name, default=None)
        if not team_data:
            await ctx.send("¡Este equipo no existe!")
            return

        await team_role.delete()

        await self.config.guild(ctx.guild).teams.clear_raw(team_role.name)
        await ctx.send(f"¡Equipo {team_role.name} eliminado!")
