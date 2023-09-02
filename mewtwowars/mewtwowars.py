import discord
from discord.ext import commands
from redbot.core import Config, commands
from collections import defaultdict
from tabulate import tabulate
import json

class MewtwoWars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        default_guild = {
            "user_points": {},
            "team_points": {
                "Mewtwo X": 0,
                "Mewtwo Y": 0
            }
        }
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_guild(**default_guild)

    @commands.group(name="mwpoints")
    @commands.has_permissions(administrator=True)
    async def mwpoints(self, ctx):
        """Command to manage user points."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Uso incorrecto. Usa `!mwpoints add <user> <points>` o `!mwpoints delete <user> <points>`.")

    @mwpoints.command(name="add")
    async def mwpoints_add(self, ctx, user: discord.Member, points: int):
        """Add points to a user."""
        user_points = await self.config.guild(ctx.guild).user_points()
        user_points[user.id] = user_points.get(str(user.id), 0) + points
        await self.config.guild(ctx.guild).user_points.set(user_points)
        
        team = 'Mewtwo X' if any(role.id == 1147254156491509780 for role in user.roles) else 'Mewtwo Y'
        team_points = await self.config.guild(ctx.guild).team_points()
        team_points[team] += points
        await self.config.guild(ctx.guild).team_points.set(team_points)
        
        await ctx.send(f"Se han añadido {points} puntos a {user.display_name}.")

    @mwpoints.command(name="delete")
    async def mwpoints_delete(self, ctx, user: discord.Member, points: int):
        """Delete points from a user."""
        user_points = await self.config.guild(ctx.guild).user_points()
        if str(user.id) in user_points:
            user_points[str(user.id)] -= points
            await self.config.guild(ctx.guild).user_points.set(user_points)
        else:
            await ctx.send(f"{user.display_name} no tiene puntos.")
            return

        team = 'Mewtwo X' if any(role.id == 1147254156491509780 for role in user.roles) else 'Mewtwo Y'
        team_points = await self.config.guild(ctx.guild).team_points()
        team_points[team] -= points
        await self.config.guild(ctx.guild).team_points.set(team_points)
        
        await ctx.send(f"Se han eliminado {points} puntos de {user.display_name}.")            
        def is_valid_team(self, user):
            """Check if user belongs to a valid team."""
            return any(role.id in [1147254156491509780, 1147253975893159957] for role in user.roles)

    async def save_data(self):
        await self.config.guild(ctx.guild).user_points.set(self.user_points)
        await self.config.guild(ctx.guild).team_points.set(self.team_points)

    async def load_data(self):
        self.user_points = await self.config.guild(ctx.guild).user_points()
        self.team_points = await self.config.guild(ctx.guild).team_points()
            
    @commands.group(name="mwranking", invoke_without_command=True)
    async def mwranking(self, ctx):
        """Check the Mewtwo Wars ranking."""
        await self.display_ranking(ctx)

    async def display_ranking(self, ctx):
        table = [["Ranking", "Usuario", "Puntos"]]
        
        # Fetch the user points from the Config storage
        user_points = await self.config.guild(ctx.guild).user_points()

        # Sort the users by their points in descending order
        sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
        for idx, (user_id, points) in enumerate(sorted_users):
            user = ctx.guild.get_member(int(user_id))  # Convert user_id from str to int
            if user:
                team = "X" if any(role.id == 1147254156491509780 for role in user.roles) else "Y"
                table.append([f"# {idx + 1}", f"{user.display_name} ({team})", f"{points} puntos"])
            else:
                table.append([f"# {idx + 1}", "Unknown", f"{points} puntos"])

        # Fetch the team points from Config
        team_points = await self.config.guild(ctx.guild).team_points()

        table_str = tabulate(table, headers="firstrow", tablefmt="grid")

        embed = discord.Embed(title="Clasificación Mewtwo Wars")
        embed.add_field(name="Mewtwo X", value=f"{team_points['Mewtwo X']} puntos", inline=True)
        embed.add_field(name="Mewtwo Y", value=f"{team_points['Mewtwo Y']} puntos", inline=True)
        embed.description = f"```\n{table_str}\n```"
        await ctx.send(embed=embed)

    @commands.command(name="mwreset")
    @commands.is_owner()  # Ensure only the bot owner can run this
    async def mwreset(self, ctx):
        """Reset the Mewtwo Wars ranking."""
        
        # Reset user points and team points in the Config storage
        await self.config.guild(ctx.guild).user_points.set({})
        await self.config.guild(ctx.guild).team_points.set({
            'Mewtwo X': 0,
            'Mewtwo Y': 0
        })

        await ctx.send("¡Clasificación de Mewtwo Wars reiniciada!")