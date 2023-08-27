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

    @commands.command()
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def unteam(self, ctx, member1: discord.Member, member2: discord.Member):
        """Evita que dos usuarios estén en el mismo equipo."""
        if member1 == member2:
            await ctx.send("¡No puedes poner a la misma persona en la lista de exclusión!")
            return

        await self.config.guild(ctx.guild).user_pairs.set_raw(str(member1.id), value=member2.id)
        await self.config.guild(ctx.guild).user_pairs.set_raw(str(member2.id), value=member1.id)
        await ctx.send(f"¡Los usuarios {member1.mention} y {member2.mention} no estarán en el mismo equipo!")

    @commands.command()
    @commands.guild_only()
    @commands.mod_or_permissions()
    async def battlers(self, ctx, role: discord.Role, num_teams: int):
        """Randomiza equipos con un rol específico."""
        guild = ctx.guild
        members_with_role = [member.id for member in guild.members if role in member.roles]

        if len(members_with_role) < num_teams * 5:
            await ctx.send("No hay suficientes miembros con el rol especificado.")
            return

        random.shuffle(members_with_role)

        # Distribute members into teams
        teams = [members_with_role[i:i+5] for i in range(0, len(members_with_role), 5)]

        # Get user pairs to exclude from the same team
        user_pairs = await self.config.guild(guild).user_pairs()
        for member_id, exclusion_id in user_pairs.items():
            if member_id in members_with_role and exclusion_id in members_with_role:
                member_team_index = next((i for i, team in enumerate(teams) if member_id in team), None)
                exclusion_team_index = next((i for i, team in enumerate(teams) if exclusion_id in team), None)
                if member_team_index is not None and exclusion_team_index is not None and member_team_index == exclusion_team_index:
                    # Swap the excluded member to another team
                    target_team = (exclusion_team_index + 1) % num_teams
                    teams[exclusion_team_index].remove(exclusion_id)
                    teams[target_team].append(exclusion_id)

        lista_equipos = []
        for index, team in enumerate(teams, start=1):
            miembros_equipo = " ".join([guild.get_member(member_id).mention for member_id in team])
            lista_equipos.append(f"Equipo {index}: {miembros_equipo}")

        equipos_unidos = "\n".join(lista_equipos)
        await ctx.send(f"Equipos aleatorizados:\n{equipos_unidos}")

        await self.config.guild(guild).role_to_team.set_raw(str(role.id), value=teams)