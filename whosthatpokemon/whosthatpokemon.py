# This cog did not have a license but is now licensed under the MIT License.
# This cog was created by owocado and is now continued by ltzmax.
# This cog was transfered via a pr from the author of the code https://github.com/ltzmax/maxcogs/pull/46
"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
from datetime import datetime, timedelta, timezone, time
from io import BytesIO
from random import randint
from typing import Any, Dict, Final, List, Optional

import aiohttp
import discord
from discord import File, Role
from discord.ext import tasks
from PIL import Image
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number
from redbot.core.utils.views import ConfirmView, SimpleMenu

from .converter import Generation
from .view import WhosThatPokemonView

API_URL: Final[str] = "https://pokeapi.co/api/v2"


class WhosThatPokemon(commands.Cog):
    """¿Puedes adivinar el Pokémon?"""

    @tasks.loop(hours=24)
    async def reset_usage_counts(self):
        """Reset the daily usage counts for all users."""
        now = datetime.now(timezone.utc)
        reset_time = datetime.combine(now.date(), time(7, 0, tzinfo=timezone.utc))  # 9 am GMT+2 is 7 am UTC
        if now >= reset_time:
            # Move to the next day if current time is already past the reset time
            reset_time += timedelta(days=1)

        # Sleep until the reset time
        await asyncio.sleep((reset_time - now).total_seconds())

        # Reset all user data
        await self.config.clear_all_users()

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_user = {
            "total_correct_guesses": 0,
            "usage_count": 0
        }
        self.config.register_user(**default_user)
        self.reset_usage_counts.start()

    async def mention_role_temporarily(self, ctx, role_id: int):
        role = ctx.guild.get_role(role_id)  # Fetch the role using role_id
        if not role:
            return  # If the role is not found, simply return

        try:
            await role.edit(mentionable=True)
            await ctx.send(role.mention)
        finally:
            await role.edit(mentionable=False)

    async def cog_unload(self) -> None:
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {humanize_list(self.__author__)}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def get_data(self, url: str) -> Dict[str, Any]:
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {"http_code": response.status}
                return await response.json()
        except asyncio.TimeoutError:
            return {"http_code": 408}


    # _____ ________  ______  ___  ___   _   _______  _____
    # /  __ \  _  |  \/  ||  \/  | / _ \ | \ | |  _  \/  ___|
    # | /  \/ | | | .  . || .  . |/ /_\ \|  \| | | | |\ `--.
    # | |   | | | | |\/| || |\/| ||  _  || . ` | | | | `--. \
    # | \__/\ \_/ / |  | || |  | || | | || |\  | |/ / /\__/ /
    # \____/\___/\_|  |_/\_|  |_/\_| |_/\_| \_/___/  \____/
    @commands.command(name="wtpversion", hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def whosthatpokemon_version(self, ctx: commands.Context) -> None:
        """Shows the version of the cog"""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["wtp"])
    @app_commands.describe(
        generation=("Optionally choose generation from gen1 to gen9.")
    )
    @app_commands.choices(
        generation=[
            app_commands.Choice(name="Generation 1", value="gen1"),
            app_commands.Choice(name="Generation 2", value="gen2"),
            app_commands.Choice(name="Generation 3", value="gen3"),
            app_commands.Choice(name="Generation 4", value="gen4"),
            app_commands.Choice(name="Generation 5", value="gen5"),
            app_commands.Choice(name="Generation 6", value="gen6"),
            app_commands.Choice(name="Generation 7", value="gen7"),
            app_commands.Choice(name="Generation 8", value="gen8"),
            app_commands.Choice(name="Leyendas: Arceus", value="arceus"),
            app_commands.Choice(name="Generation 9", value="gen9"),
        ]
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.bot_has_permissions(attach_files=True, embed_links=True)
    @commands.mod_or_permissions(administrator=True)
    async def whosthatpokemon(
        self,
        ctx: commands.Context,
        generation: Generation = None,
    ) -> None:

        """Guess Who's that Pokémon in 30 seconds!

        You can optionally specify generation from `gen1` to `gen8` only.

        **Example:**
        - `[p]whosthatpokemon` - This will start a new Generation.
        - `[p]whosthatpokemon gen1` - This will pick any pokemon from generation 1 for you to guess.

        **Arguments:**
        - `[generation]` - Where you choose any generation from gen 1 to gen 8.
        """

        mewtwo_wars_role = discord.utils.get(ctx.guild.roles, id=1147262532231385219)
        mewtwo_x_role = discord.utils.get(ctx.guild.roles, id=1147254156491509780)
        mewtwo_y_role = discord.utils.get(ctx.guild.roles, id=1147253975893159957)

        usage_count = await self.config.user(ctx.author).usage_count() or 0

        if usage_count >= 5:
            # Calculate the remaining time until 9 am GMT+2 (or 7 am UTC)
            remaining_time = (datetime.combine(datetime.now().date(), time(7, 0)) + timedelta(days=1)) - datetime.now()
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes = remainder // 60
            await ctx.send(f"{ctx.author.mention} Has alcanzado el límite diario de 5 usos. Espera {hours} horas y {minutes} minutos para otro intento.", delete_after=7)
            return

        # If they haven't hit the limit, increment the count
        await self.config.user(ctx.author).usage_count.set(usage_count + 1)

        # Notify the user about how many uses they have left
        remaining_uses = 5 - (usage_count + 1)
        await ctx.send(f"{ctx.author.mention} ¡Tienes {remaining_uses} usos restantes hoy!", delete_after=7)
                
        # Now use the function to mention these roles
        await self.mention_role_temporarily(ctx, mewtwo_wars_role)
        await self.mention_role_temporarily(ctx, mewtwo_x_role)
        await self.mention_role_temporarily(ctx, mewtwo_y_role)

        await ctx.send(
            f"{mewtwo_wars_role.mention}\n{mewtwo_x_role.mention} {mewtwo_y_role.mention}\n¡Un nuevo Pokémon ha aparecido! ¿Os veis capaces de adivinarlo?",
            allowed_mentions=discord.AllowedMentions(roles=True)  # This will allow role mentions
        )

        await asyncio.sleep(15)  # waiting for 15 seconds

        await ctx.typing()

        poke_id = generation or randint(1, 898)
        if_guessed_right = False

        temp = await self.generate_image(f"{poke_id:>03}", hide=True)
        if temp is None:
            return await ctx.send("Failed to generate whosthatpokemon card image.")

        # Took this from Core's event file.
        # https://github.com/Cog-Creators/Red-DiscordBot/blob/41d89c7b54a1f231a01f79655c20d4acf1799633/redbot/core/_events.py#L424-L426
        img_timeout = discord.utils.format_dt(
            datetime.now(timezone.utc) + timedelta(minutes=5), "R"
        )
        species_data = await self.get_data(f"{API_URL}/pokemon-species/{poke_id}")
        if species_data.get("http_code"):
            return await ctx.send("Failed to get species data from PokeAPI.")
        names_data = species_data.get("names", [{}])
        eligible_names = [x["name"].lower() for x in names_data]
        # Get name in Spanish or, if not available, in English
        filtered_names_es = [x["name"] for x in names_data if x["language"]["name"] == "es"]
        filtered_names_en = [x["name"] for x in names_data if x["language"]["name"] == "en"]

        english_name = filtered_names_es[0] if filtered_names_es else (filtered_names_en[0] if filtered_names_en else "Unknown")

        revealed = await self.generate_image(f"{poke_id:>03}", hide=False)
        revealed_img = File(revealed, "whosthatpokemon.png")

        view = WhosThatPokemonView(self.bot, eligible_names)
        view.message = await ctx.send(
            f"**¡¿Cuál es este Pokémon?!**\nNecesito una respuesta válida en menos de {img_timeout}.",
            file=File(temp, "guessthatpokemon.png"),
            view=view,
        )

        embed = discord.Embed(
            title=":tada: ¡Pokémon acertado! :tada:",
            description=f"El Pokémon era... **{english_name}**.",
            color=0x76EE00,
        )
        embed.set_image(url="attachment://whosthatpokemon.png")
        embed.set_footer(text=f"Author: {ctx.author}", icon_url=ctx.author.avatar.url)
        # because we want it to timeout and not tell the user that they got it right.
        # This is probably not the best way to do it, but it works perfectly fine.
        timeout = await view.wait()
        if timeout:
            embed = discord.Embed(
                title=":x: ¡Tiempoooooooooo! :x:",
                description=f"Nadie ha respondido a tiempo.\nEl Pokémon era... **{english_name}**.",
                color=0x8B0000,
            )
            return await ctx.send(embed=embed)

        if await self.config.user(ctx.author).all():
            await self.config.user(ctx.author).total_correct_guesses.set(
                await self.config.user(ctx.author).total_correct_guesses() + 1
            )
            
        await ctx.send(file=revealed_img, embed=embed)

    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.mod_or_permissions(administrator=True)
    @commands.command(name="wtpleaderboard", aliases=["wtplb"])
    async def whosthatpokemon_leaderboard(self, ctx: commands.Context):
        """Shows the leaderboard for whosthatpokemon.

        This is global leaderboard and not per server.
        This will show the top 10 users with most correct guesses.
        """
        pages = []
        users = await self.config.all_users()
        sorted_users = sorted(users.items(), key=lambda x: x[1]["total_correct_guesses"])
        sorted_users.reverse()
        if not sorted_users:
            return await ctx.send(
                "No one has played whosthatpokemon yet. Use `[p]whosthatpokemon` to start!"
            )
        embed = discord.Embed(
            title="WhosThatPokemon Leaderboard",
            description="Top 10 users with most correct guesses.",
            color=await ctx.embed_color(),
        )
        for index, user in enumerate(sorted_users[:10], start=1):
            user_id = int(user[0])
            total_correct_guesses = await self.config.user_from_id(
                user_id
            ).total_correct_guesses()
            total = humanize_number(total_correct_guesses)
            user_obj = self.bot.get_user(user_id)
            if user_obj is None:
                continue
            embed.add_field(
                name=f"{index}. {user_obj}",
                value=f"Total correct guesses: **{total}**",
                inline=False,
            )
        pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=300,
        ).start(ctx)

    @commands.command(name="wtpstats")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.mod_or_permissions(administrator=True)
    async def whosthatpokemon_stats(self, ctx: commands.Context):
        """Shows your stats for whosthatpokemon.

        This will show your total correct guesses.
        """
        total_correct_guesses = await self.config.user(
            ctx.author
        ).total_correct_guesses()
        if not total_correct_guesses:
            return await ctx.send(
                f"You have not played whosthatpokemon yet. Use `{ctx.clean_prefix}whosthatpokemon` to start!"
            )
        human = humanize_number(total_correct_guesses)
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s WhosThatPokemon Stats",
            description=f"Total Correct Guesses: **{human}**",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command(name="wtpreset")
    @commands.cooldown(2, 43200, commands.BucketType.user)
    async def whosthatpokemon_preset(self, ctx: commands.Context):
        """Resets the whosthatpokemon leaderboard.

        This will reset the leaderboard globally.
        This can only be used by the bot owner and 2 times per 12 hours.
        """
        if not await self.config.all_users():
            return await ctx.send(
                "No one has played whosthatpokemon yet so nothing to reset."
            )
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset the leaderboard?\n**This will reset the leaderboard globally**.",
            view=view,
        )
        await view.wait()
        if view.result:
            await self.config.clear_all_users()
            await ctx.send("✅ WhosThatPokemon leaderboard has been reset.")
        else:
            await ctx.send("❌ WhosThatPokemon leaderboard reset has been cancelled.")

    @commands.command(name="wtpusesreset")
    @commands.is_owner()
    async def reset_uses(self, ctx: commands.Context):
        """Resetea los usos del comando wtp para todos los usuarios."""
        
        users_data = await self.config.all_users()
        
        for user_id in users_data.keys():
            await self.config.user_from_id(user_id).usage_count.set(0)
        
        await ctx.send("Todos los usos del comando wtp han sido reiniciados.")
    async def generate_image(self, poke_id: str, *, hide: bool) -> Optional[BytesIO]:
        base_image = Image.open(bundled_data_path(self) / "template.webp").convert(
            "RGBA"
        )
        bg_width, bg_height = base_image.size
        base_url = (
            f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{poke_id}.png"
        )
        try:
            async with self.session.get(base_url) as response:
                if response.status != 200:
                    return None
                data = await response.read()
        except asyncio.TimeoutError:
            return None

        pbytes = BytesIO(data)
        poke_image = Image.open(pbytes)
        poke_width, poke_height = poke_image.size
        poke_image_resized = poke_image.resize(
            (int(poke_width * 1.6), int(poke_height * 1.6))
        )

        if hide:
            p_load = poke_image_resized.load()  # type: ignore
            for y in range(poke_image_resized.size[1]):
                for x in range(poke_image_resized.size[0]):
                    if p_load[x, y] == (0, 0, 0, 0):  # type: ignore
                        continue
                    p_load[x, y] = (1, 1, 1)  # type: ignore

        paste_w = int((bg_width - poke_width) / 10)
        paste_h = int((bg_height - poke_height) / 4)

        base_image.paste(poke_image_resized, (paste_w, paste_h), poke_image_resized)

        temp = BytesIO()
        base_image.save(temp, "png")
        temp.seek(0)
        pbytes.close()
        base_image.close()
        poke_image.close()
        return temp

## WTPADMINTEST
    @commands.command(name="wtpadmin", hidden=True)
    @commands.has_permissions(administrator=True)
    async def whosthatpokemon_admin(self, ctx: commands.Context, poke_id: str, *, hide: bool = False):
        """Admin version of the WhosThatPokemon command."""
        temp = await self.generate_image_new(poke_id, hide=hide)
        if temp is None:
            return await ctx.send("Failed to generate new WhosThatPokemon card image.")
        
        await ctx.send(file=File(temp, "new_whosthatpokemon.png"))

    async def generate_image_new(self, poke_id: str, *, hide: bool) -> Optional[BytesIO]:
        # Fetch pokemon data from the API
        response = await self.session.get(f"https://pokeapi.co/api/v2/pokemon/{poke_id}")
        if response.status != 200:
            return None
        pkmn_data = await response.json()
        
        # Get the official artwork URL
        base_url = pkmn_data['sprites']['other']['official-artwork']['front_default']
        if base_url is None:
            return None
        
        base_image = Image.open(bundled_data_path(self) / "template.webp").convert("RGBA")
        bg_width, bg_height = base_image.size
        
        try:
            async with self.session.get(base_url) as response:
                if response.status != 200:
                    return None
                data = await response.read()
        except asyncio.TimeoutError:
            return None

        pbytes = BytesIO(data)
        poke_image = Image.open(pbytes)
        poke_width, poke_height = poke_image.size
        poke_image_resized = poke_image.resize((int(poke_width * 1.6), int(poke_height * 1.6)))

        if hide:
            p_load = poke_image_resized.load()
            for y in range(poke_image_resized.size[1]):
                for x in range(poke_image_resized.size[0]):
                    if p_load[x, y] == (0, 0, 0, 0):
                        continue
                    p_load[x, y] = (1, 1, 1)

        paste_w = int((bg_width - poke_width) / 10)
        paste_h = int((bg_height - poke_height) / 4)

        base_image.paste(poke_image_resized, (paste_w, paste_h), poke_image_resized)

        temp = BytesIO()
        base_image.save(temp, "png")
        temp.seek(0)
        pbytes.close()
        base_image.close()
        poke_image.close()
        return temp
