import asyncio
import contextlib
from typing import Optional, Any, Dict, Iterable, List, Optional
import tabulate

import discord
import tabulate
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils.predicates import MessagePredicate
from redbot.vendored.discord.ext import menus


from .functions import poke_embed

_ = Translator("Pokecord", __file__)

class PokeList:
    def __init__(self, entries: Iterable[Dict], per_page: int = 8):
        self.entries = list(entries)
        self.per_page = per_page

    def get_max_pages(self):
        return len(self.entries) // self.per_page + (1 if len(self.entries) % self.per_page else 0)

    def format_page(self, current_page: int) -> discord.Embed:
        start = current_page * self.per_page
        end = start + self.per_page
        entries = self.entries[start:end]

        # Header for the ASCII table
        table_header = "ID | Pokémon              | Nº Pokédex | Nivel | XP"
        lines = [table_header]

        for idx, pokemon in enumerate(entries, start=1 + (current_page * self.per_page)):
            # Determine gender symbol
            gender_symbol = ""
            if pokemon.get("gender") == "Male":
                gender_symbol = "♂️"
            elif pokemon.get("gender") == "Female":
                gender_symbol = "♀️"

            # Check if the Pokémon is shiny
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
        footer_text = f"Página {current_page + 1}/{self.get_max_pages()}"
        embed.set_footer(text=footer_text)
        return embed

class PokeListMenu(discord.ui.View):
    def __init__(self, poke_list: PokeList, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.poke_list = poke_list
        self.current_page = 0
        self.add_item(discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="prev"))
        self.add_item(discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next"))
        self.add_item(discord.ui.Button(label="Jump to Page", style=discord.ButtonStyle.secondary, custom_id="jump"))
        self.add_item(discord.ui.Button(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # Modify this to restrict who can interact with this view

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def on_interaction(self, interaction: discord.Interaction):
        custom_id = interaction.data.get("custom_id")

        if custom_id == "prev":
            await self.show_page(interaction, self.current_page - 1)
        elif custom_id == "next":
            await self.show_page(interaction, self.current_page + 1)
        elif custom_id == "jump":
            await self.number_page(interaction)
        elif custom_id == "stop":
            for item in this.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            self.stop()

    async def show_page(self, interaction: discord.Interaction, page_number: int):
        max_pages = self.poke_list.get_max_pages()
        if page_number < 0:
            self.current_page = max_pages - 1
        elif page_number >= max_pages:
            self.current_page = 0
        else:
            self.current_page = page_number

        content = self.poke_list.format_page(self.current_page)
        await interaction.response.edit_message(content=None, embed=content, view=self)

    async def number_page(self, interaction: discord.Interaction):
        # Implementation for jumping to a specific page can be added here
        pass

    async def start(self, channel: discord.abc.Messageable):
        embed = self.poke_list.format_page(self.current_page)
        self.message = await channel.send(embed=embed, view=self)

class GenericMenu(menus.MenuPages, inherit_buttons=False):
    def __init__(
        self,
        source: menus.PageSource,
        cog: Optional[commands.Cog] = None,
        len_poke: Optional[int] = 0,
        clear_reactions_after: bool = True,
        delete_message_after: bool = False,
        add_reactions: bool = True,
        using_custom_emoji: bool = False,
        using_embeds: bool = False,
        keyword_to_reaction_mapping: Dict[str, str] = None,
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
            check_embeds=using_embeds,
            timeout=timeout,
            message=message,
            **kwargs,
        )

    def reaction_check(self, payload):
        """The function that is used to check whether the payload should be processed.
        This is passed to :meth:`discord.ext.commands.Bot.wait_for <Bot.wait_for>`.
        There should be no reason to override this function for most users.
        Parameters
        ------------
        payload: :class:`discord.RawReactionActionEvent`
            The payload to check.
        Returns
        ---------
        :class:`bool`
            Whether the payload should be processed.
        """
        if payload.message_id != self.message.id:
            return False
        if payload.user_id not in (*self.bot.owner_ids, self._author_id):
            return False

        return payload.emoji in self.buttons

    def _skip_single_arrows(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages == 1

    def _skip_double_triangle_buttons(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 2

    # left
    @menus.button(
        "\N{BLACK LEFT-POINTING TRIANGLE}",
        position=menus.First(1),
        skip_if=_skip_single_arrows,
    )
    async def prev(self, payload: discord.RawReactionActionEvent):
        if self.current_page == 0:
            await self.show_page(self._source.get_max_pages() - 1)
        else:
            await self.show_checked_page(self.current_page - 1)

    @menus.button("\N{CROSS MARK}", position=menus.First(2))
    async def stop_pages_default(self, payload: discord.RawReactionActionEvent) -> None:
        self.stop()
        with contextlib.suppress(discord.NotFound):
            await self.message.delete()

    @menus.button(
        "\N{BLACK RIGHT-POINTING TRIANGLE}",
        position=menus.First(2),
        skip_if=_skip_single_arrows,
    )
    async def next(self, payload: discord.RawReactionActionEvent):
        if self.current_page == self._source.get_max_pages() - 1:
            await self.show_page(0)
        else:
            await self.show_checked_page(self.current_page + 1)

    @menus.button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        position=menus.First(0),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_first_page(self, payload):
        """go to the first page"""
        await self.show_page(0)

    @menus.button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        position=menus.Last(1),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
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
