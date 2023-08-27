import discord
import random
from redbot.core import commands, Config

class Partiditas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier
        default_guild = {
            "role_to_team": {}  # Maps roles to team lists
        }
        self.config.register_guild(**default_guild)

    @commands.command()
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def battlers(self, ctx, role: discord.Role, num_teams: int):
        """Randomiza equipos con un rol específico."""
        guild = ctx.guild
        members_with_role = [member for member in guild.members if role in member.roles]

        if len(members_with_role) < num_teams * 5:
            await ctx.send("No hay suficientes miembros con el rol especificado.")
            return

        random.shuffle(members_with_role)
        teams = [members_with_role[i:i+5] for i in range(0, len(members_with_role), 5)]

        lista_equipos = []
        for index, team in enumerate(teams, start=1):
            miembros_equipo = ", ".join([member.display_name for member in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

        # Store member IDs (as strings) in the configuration
        member_ids = [[str(member.id) for member in team] for team in teams]
        await self.config.guild(guild).role_to_team.set_raw(str(role.id), value=member_ids)
        
def setup(bot):
    bot.add_cog(Partiditas(bot))
