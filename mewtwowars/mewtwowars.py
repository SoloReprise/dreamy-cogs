import discord
from discord.ext import commands
from redbot.core import Config, commands
from collections import defaultdict
from tabulate import tabulate
import json
import asyncio

ITEMS_PER_PAGE = 10

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
        await self.display_ranking(ctx, 0)

    async def display_ranking(self, ctx, page):
        table = [["Ranking", "Usuario", "Puntos"]]
        
        # Fetch the user points from the Config storage
        user_points = await self.config.guild(ctx.guild).user_points()

        # Sort the users by their points in descending order
        filtered_users = {user_id: points for user_id, points in user_points.items() if points > 0}
        sorted_users = sorted(filtered_users.items(), key=lambda x: x[1], reverse=True)

        start_index = page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE

        for idx, (user_id, points) in enumerate(sorted_users[start_index:end_index]):
            user = ctx.guild.get_member(int(user_id))
            if user:
                team = "X" if any(role.id == 1147254156491509780 for role in user.roles) else "Y"
                handle = f"{user.name}"  # This gets the Discord handle
                table.append([f"# {start_index + idx + 1}", f"{handle} ({team})", f"{points} puntos"])
            else:
                table.append([f"# {start_index + idx + 1}", "Unknown", f"{points} puntos"])

        # Fetch the team points from Config
        team_points = await self.config.guild(ctx.guild).team_points()

        table_str = tabulate(table, headers="firstrow", tablefmt="grid")

        embed = discord.Embed(title="Clasificación Mewtwo Wars")
        embed.add_field(name="Mewtwo X", value=f"{team_points['Mewtwo X']} puntos", inline=True)
        embed.add_field(name="Mewtwo Y", value=f"{team_points['Mewtwo Y']} puntos", inline=True)
        embed.description = f"```\n{table_str}\n```"
        
        msg = await ctx.send(embed=embed)
        
        # Add reaction controls for pagination if there are more pages to show
        if page > 0:
            await msg.add_reaction("⬅️")
        if (page + 1) * ITEMS_PER_PAGE < len(sorted_users):
            await msg.add_reaction("➡️")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                
                if str(reaction.emoji) == "⬅️" and page > 0:
                    await msg.delete()  # delete the current message
                    await self.display_ranking(ctx, page - 1)
                    return
                elif str(reaction.emoji) == "➡️" and (page + 1) * ITEMS_PER_PAGE < len(sorted_users):
                    await msg.delete()  # delete the current message
                    await self.display_ranking(ctx, page + 1)
                    return
                await msg.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
                break

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

    async def add_points(self, guild: discord.Guild, user: discord.Member, points: int):
        """Utility method to add points to a user."""
        
        # Access the config for this specific guild
        user_points = await self.config.guild(guild).user_points()

        # Check if the user is already present in the user_points dictionary
        # If not, add them with the given points
        # If they are present, add the points to their existing total
        user_points[str(user.id)] = user_points.get(str(user.id), 0) + points
        
        await self.config.guild(guild).user_points.set(user_points)
        
        team = 'Mewtwo X' if any(role.id == 1147254156491509780 for role in user.roles) else 'Mewtwo Y'
        
        # Update team points similarly
        team_points = await self.config.guild(guild).team_points()
        team_points[team] += points
        await self.config.guild(guild).team_points.set(team_points)
