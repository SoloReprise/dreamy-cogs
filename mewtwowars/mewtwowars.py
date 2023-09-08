import discord
from discord.ext import commands
from redbot.core import Config, commands
from collections import defaultdict
from tabulate import tabulate
import json


class RankingView(discord.ui.View):
    def __init__(self, ctx, pages):
        super().__init__(timeout=180.0)
        self.ctx = ctx
        self.current_page = 0
        self.pages = pages

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def go_previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.edit_original_message(embed=self.pages[self.current_page])

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def go_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.edit_original_message(embed=self.pages[self.current_page])

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)
        log.error("Error in RankingView: %s", error, exc_info=True)            

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
        user_points = await self.config.guild(ctx.guild).user_points()
        sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
        
        # Split users into chunks of 10 for pagination
        chunks = [sorted_users[i:i + 10] for i in range(0, len(sorted_users), 10)]
        
        pages = []
        for chunk in chunks:
            table = [["Ranking", "Usuario", "Puntos"]]
            for idx, (user_id, points) in enumerate(chunk, start=1):
                user = ctx.guild.get_member(int(user_id))
                if user:
                    team = "X" if any(role.id == 1147254156491509780 for role in user.roles) else "Y"
                    table.append([f"# {idx}", f"{user.display_name} ({team})", f"{points} puntos"])
            
            table_str = tabulate(table, headers="firstrow", tablefmt="grid")
            embed = discord.Embed(title="Clasificación Mewtwo Wars")
            embed.description = f"```\n{table_str}\n```"
            
            # Add the team points here if you want them to be displayed on every page
            team_points = await self.config.guild(ctx.guild).team_points()
            embed.add_field(name="Mewtwo X", value=f"{team_points['Mewtwo X']} puntos", inline=True)
            embed.add_field(name="Mewtwo Y", value=f"{team_points['Mewtwo Y']} puntos", inline=True)

            pages.append(embed)

        view = RankingView(ctx, pages)
        await ctx.send(embed=pages[0], view=view)

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
