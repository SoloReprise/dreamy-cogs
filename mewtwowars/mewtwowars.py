import discord
from discord.ext import commands
from redbot.core import commands
from collections import defaultdict
from tabulate import tabulate
import json

class MewtwoWars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_data()
        self.team_points = {'Mewtwo X': 0, 'Mewtwo Y': 0}
        self.user_points = defaultdict(int)  # default value for a user is 0

    def load_data(self):
        try:
            with open("mewtwo_data.json", "r") as f:
                data = json.load(f)
                self.user_points = data.get("user_points", {})
                self.team_points = data.get("team_points", {"Mewtwo X": 0, "Mewtwo Y": 0})
        except FileNotFoundError:
            # If file doesn't exist, initialize with default values
            self.user_points = {}
            self.team_points = {"Mewtwo X": 0, "Mewtwo Y": 0}

    def save_data(self):
        with open("mewtwo_data.json", "w") as f:
            data = {
                "user_points": self.user_points,
                "team_points": self.team_points
            }
            json.dump(data, f)

    @commands.group(name="mwpoints")
    @commands.has_permissions(administrator=True)
    async def mwpoints(self, ctx):
        """Command to manage user points."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Uso incorrecto. Usa `!mwpoints add <user> <points>` o `!mwpoints delete <user> <points>`.")

    @mwpoints.command(name="add")
    async def mwpoints_add(self, ctx, user: discord.Member, points: int):
        """Add points to a user."""
        if self.is_valid_team(user):
            self.user_points[user.id] = self.user_points.get(user.id, 0) + points
            team = 'Mewtwo X' if any(role.id == 1147254156491509780 for role in user.roles) else 'Mewtwo Y'
            self.team_points[team] += points
            self.save_data()
            await ctx.send(f"Se han añadido {points} puntos a {user.display_name}.")
        else:
            await ctx.send(f"{user.display_name} no pertenece a ningún equipo válido.")

    @mwpoints.command(name="delete")
    async def mwpoints_delete(self, ctx, user: discord.Member, points: int):
        """Delete points from a user."""
        current_points = self.user_points.get(user.id, 0)
        if self.is_valid_team(user) and current_points - points >= 0:
            self.user_points[user.id] = current_points - points
            team = 'Mewtwo X' if any(role.id == 1147254156491509780 for role in user.roles) else 'Mewtwo Y'
            self.team_points[team] -= points
            self.save_data()
            await ctx.send(f"Se han eliminado {points} puntos de {user.display_name}.")
        else:
            await ctx.send(f"{user.display_name} no tiene puntos suficientes o no pertenece a ningún equipo válido.")
            
    async def display_ranking(self, ctx):
        table = [["Ranking", "Usuario", "Puntos"]]
        
        # Sort the users by their points in descending order
        sorted_users = sorted(self.user_points.items(), key=lambda x: x[1], reverse=True)[:10]
        for idx, (user_id, points) in enumerate(sorted_users):
            user = ctx.guild.get_member(user_id)
            if user:
                team = "X" if any(role.id == 1147254156491509780 for role in user.roles) else "Y"
                table.append([f"# {idx + 1}", f"{user.display_name} ({team})", f"{points} puntos"])
            else:
                table.append([f"# {idx + 1}", "Unknown", f"{points} puntos"])
        table_str = tabulate(table, headers="firstrow", tablefmt="grid")

        embed = discord.Embed(title="Clasificación Mewtwo Wars")
        embed.add_field(name="Mewtwo X", value=f"{self.team_points['Mewtwo X']} puntos", inline=True)
        embed.add_field(name="Mewtwo Y", value=f"{self.team_points['Mewtwo Y']} puntos", inline=True)
        embed.description = f"```\n{table_str}\n```"
        await ctx.send(embed=embed)

    @commands.command(name="mwreset")
    @commands.is_owner()  # Ensure only the bot owner can run this
    async def mwreset(self, ctx):
        """Reset the Mewtwo Wars ranking."""
        
        # Reset user points and team points
        self.user_points = {}
        self.team_points = {
            'Mewtwo X': 0,
            'Mewtwo Y': 0
        }

        await ctx.send("¡Clasificación de Mewtwo Wars reiniciada!")
