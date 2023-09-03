import discord
from discord.ext import commands

class UniteTeams(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="uniteteams")
    async def uniteteams(self, ctx):
        await ctx.send("Uso: !uniteteams create <@líder> <nombre del equipo> o !uniteteams delete @rolDelEquipo")

    @commands.has_permissions(administrator=True)
    @commands.group(name="create", invoke_without_command=True)
    async def create_team(self, ctx, leader: discord.Member, *, team_name: str):
        if ctx.message.guild.owner_id != ctx.author.id:
            return await ctx.send("Solo el dueño del servidor puede crear equipos.")
        role = await ctx.guild.create_role(name=team_name, mentionable=False)
        scrims_role = ctx.guild.get_role(1147980466205507668)
        if not scrims_role:
            return await ctx.send("El rol de scrims no fue encontrado.")
        await leader.add_roles(role, scrims_role)
        await ctx.send(f"Equipo '{team_name}' creado con éxito y {leader.mention} ha sido añadido como líder.")

    @commands.has_permissions(administrator=True)
    @commands.group(name="delete", invoke_without_command=True)
    async def delete_team(self, ctx, team_role: discord.Role):
        if ctx.message.guild.owner_id != ctx.author.id:
            return await ctx.send("Solo el dueño del servidor puede eliminar equipos.")
        await team_role.delete()
        await ctx.send(f"Equipo '{team_role.name}' ha sido eliminado con éxito.")
