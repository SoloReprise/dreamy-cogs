import asyncio
import contextlib
from typing import Any, Dict, Iterable, List, Optional

import discord
from discord.ext import menus
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils.predicates import MessagePredicate

from .functions import poke_embed

_ = Translator("Pokecord", __file__)

class PokeListMenu(menus.MenuPages):
    def __init__(
        self,
        source: menus.PageSource,
        cog: Optional[commands.Cog] = None,
        ctx=None,
        user=None,
        clear_reactions_after: bool = True,
        delete_message_after: bool = False,
        timeout: int = 180,
        message: discord.Message = None,
        **kwargs: Any,
    ) -> None:
        self.cog = cog
        self.ctx = ctx
        self.user = user
        self._search_lock = asyncio.Lock()
        self._search_task: asyncio.Task = None
        super().__init__(
            source,
            clear_reactions_after=clear_reactions_after,
            delete_message_after=delete_message_after,
            timeout=timeout,
            message=message,
            **kwargs,
        )
        self.add_item(discord.ui.Button(label="Previous", style=discord.ButtonStyle.grey, callback=self.prev))
        self.add_item(discord.ui.Button(label="Stop", style=discord.ButtonStyle.red, callback=self.stop_pages))
        self.add_item(discord.ui.Button(label="Next", style=discord.ButtonStyle.grey, callback=self.next))
        self.add_item(discord.ui.Button(label="Jump", style=discord.ButtonStyle.blurple, callback=self.number_page))
        self.add_item(discord.ui.Button(label="Select", style=discord.ButtonStyle.green, callback=self.select))

    async def finalize(self, timed_out):
        if not self._running:
            return

        await self.stop(do_super=False)

    async def stop(self, do_super: bool = True):
        if self._search_task is not None:
            self._search_task.cancel()
        if do_super:
            super().stop()

    async def prev(self, interaction: discord.Interaction):
        if self.current_page == 0:
            await self.show_page(self._source.get_max_pages() - 1)
        else:
            await self.show_checked_page(self.current_page - 1)

    async def stop_pages(self, interaction: discord.Interaction):
        with contextlib.suppress(discord.NotFound):
            await self.message.delete()

        await self.stop()

    async def next(self, interaction: discord.Interaction):
        if self.current_page == self._source.get_max_pages() - 1:
            await self.show_page(0)
        else:
            await self.show_checked_page(self.current_page + 1)

    async def number_page(self, interaction: discord.Interaction):
        if self._search_lock.locked() and self._search_task is not None:
            return

        self._search_task = asyncio.get_running_loop().create_task(self._number_page_task())

    async def select(self, interaction: discord.Interaction):
        command = self.ctx.bot.get_command("select")
        await self.ctx.invoke(command, _id=self.current_page + 1)

class PokeList(menus.ListPageSource):
    def __init__(self, entries: Iterable[Dict], per_page: int = 8):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: PokeListMenu, entries: List[Dict]) -> discord.Embed:
        # Header for the ASCII table
        table_header = "ID | Pokémon              | Nº Pokédex | Nivel | XP"
        lines = [table_header]

        for idx, pokemon in enumerate(entries, start=1 + (menu.current_page * self.per_page)):
            # Determine gender symbol
            gender_symbol = ""
            if pokemon.get("gender") == "Male":
                gender_symbol = "♂️"
            elif pokemon.get("gender") == "Female":
                gender_symbol = "♀️"

            # Check if the Pokémon is shiny
            # Assuming 'shiny' status is determined by checking if the English name contains 'shiny'
            name_english = pokemon['name'].get('english', '')  # Get the English name
            shiny_symbol = "✨" if "shiny" in name_english.lower() else ""  # Check if 'shiny' is in the name

            # Construct Pokémon name with optional nickname
            name = f"{shiny_symbol}{name_english}{gender_symbol}"
            if "nickname" in pokemon and pokemon["nickname"]:
                name += f" ({pokemon['nickname']})"

            # Format row for the table
            row = f"{str(idx).center(3)} | {name.ljust(20)} | {str(pokemon['id']).center(11)} | {str(pokemon['level']).center(5)} | {str(pokemon['xp']).center(3)}"
            lines.append(row)

        # Combine lines into a single string for the table
        table = "\n".join(lines)

        # Embed with ASCII table as plain text
        embed = discord.Embed(description=f"```\n{table}\n```", color=0x00FF00)
        footer_text = f"Página {menu.current_page + 1}/{self.get_max_pages()}\n"
        footer_text += "Puedes comprobar las estadísticas completas de un Pokémon con !stats <ID>"
        embed.set_footer(text=footer_text)
        return embed

class GenericMenu(menus.MenuPages):
    def __init__(
        self,
        source: menus.PageSource,
        cog: Optional[commands.Cog] = None,
        len_poke: Optional[int] = 0,
        clear_reactions_after: bool = True,
        delete_message_after: bool = False,
        timeout: int = 180,
        message: discord.Message = None,
        **kwargs: Any,
    ) -> None:
        self.cog = cog
        self.len_poke = len_poke
        super().__init__(
            source,
            clear_reactions_after=clear_reactions_after,
            delete_message_after=delete_message_after,
            timeout=timeout,
            message=message,
            **kwargs,
        )
        self.add_item(discord.ui.Button(label="First", style=discord.ButtonStyle.grey, callback=self.go_to_first_page))
        self.add_item(discord.ui.Button(label="Previous", style=discord.ButtonStyle.grey, callback=self.prev))
        self.add_item(discord.ui.Button(label="Stop", style=discord.ButtonStyle.red, callback=self.stop_pages))
        self.add_item(discord.ui.Button(label="Next", style=discord.ButtonStyle.grey, callback=self.next))
        self.add_item(discord.ui.Button(label="Last", style=discord.ButtonStyle.grey, callback=self.go_to_last_page))

    async def go_to_first_page(self, interaction: discord.Interaction):
        await self.show_page(0)

    async def prev(self, interaction: discord.Interaction):
        if self.current_page == 0:
            await self.show_page(self._source.get_max_pages() - 1)
        else:
            await self.show_checked_page(self.current_page - 1)

    async def stop_pages(self, interaction: discord.Interaction):
        self.stop()
        with contextlib.suppress(discord.NotFound):
            await self.message.delete()

    async def next(self, interaction: discord.Interaction):
        if self.current_page == self._source.get_max_pages() - 1:
            await self.show_page(0)
        else:
            await self.show_checked_page(self.current_page + 1)

    async def go_to_last_page(self, interaction: discord.Interaction):
        await self.show_page(self._source.get_max_pages() - 1)

class SearchFormat(menus.ListPageSource):
    def __init__(self, entries: Iterable[str]):
        super().__init__(entries, per_page=1)

    async def format_page(self, menu: GenericMenu, string: str) -> str:
        embed = discord.Embed(
            title="Pokemon Search",
            color=await menu.ctx.embed_color(),
            description=string,
        )
        embed.set_footer(
            text=_("Page {page}/{amount}").format(
                page=menu.current_page + 1, amount=menu._source.get_max_pages()
            )
        )
        return embed

class PokedexFormat(menus.ListPageSource):
    def __init__(self, entries: Iterable[str]):
        super().__init__(entries, per_page=1)

    async def format_page(self, menu: GenericMenu, item: List) -> str:
        embed = discord.Embed(title=_("Pokédex"), color=await menu.ctx.embed_colour())
        embed.set_footer(
            text=_("Showing {page}-{lenpages} of {amount}.").format(
                page=item[0][0], lenpages=item[-1][0], amount=menu.len_poke
            )
        )
        for pokemon in item:
            if pokemon[1]["amount"] > 0:
                msg = _("{amount} caught! \N{WHITE HEAVY CHECK MARK}").format(
                    amount=pokemon[1]["amount"]
                )
            else:
                msg = _("Not caught yet! \N{CROSS MARK}")
            embed.add_field(
                name="{pokemonname} {pokemonid}".format(
                    pokemonname=menu.cog.get_name(pokemon[1]["name"], menu.ctx.author),
                    pokemonid=pokemon[1]["id"],
                ),
                value=msg,
            )
        if menu.current_page == 0:
            embed.description = _("You've caught {total} out of {amount} pokémon.").format(
                total=len(await menu.cog.config.user(menu.ctx.author).pokeids()),
                amount=menu.len_poke,
            )
        return embed
