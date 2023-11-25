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

class PageJumpModal(discord.ui.Modal):
    def __init__(self, menu):
        super().__init__(title="Saltar a la página")
        self.menu = menu
        self.add_item(discord.ui.TextInput(label="Número de página", placeholder="Introduce el número de la página."))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            page_number = int(self.children[0].value) - 1
            await self.menu.update_page(interaction, page_number)
        except ValueError:
            await interaction.response.send_message("Por favor introduce un número válido.", ephemeral=True)

class PokeListMenu(discord.ui.View):
    def __init__(self, poke_list: PokeList, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.poke_list = poke_list
        self.current_page = 0
        self.message = None  # Reference to the message to which this view is attached

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def update_page(self, interaction: discord.Interaction, page_number: int):
        # Page update logic
        max_pages = self.poke_list.get_max_pages()
        if page_number < 0:
            self.current_page = max_pages - 1
        elif page_number >= max_pages:
            self.current_page = 0
        else:
            self.current_page = page_number

        embed = self.poke_list.format_page(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Anterior", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_page(interaction, self.current_page - 1)

    @discord.ui.button(label="Siguiente", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_page(interaction, self.current_page + 1)

    @discord.ui.button(label="Saltar a la página...", style=discord.ButtonStyle.secondary)
    async def jump_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PageJumpModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Cerrar", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

    async def start(self, channel: discord.abc.Messageable):
        embed = self.poke_list.format_page(self.current_page)
        self.message = await channel.send(embed=embed, view=self)

class GenericMenu(discord.ui.View):
    def __init__(self, source, ctx, len_poke=0, timeout: int = 180, delete_message_after: bool = False):
        super().__init__(timeout=timeout)
        self.source = source
        cog: Optional[commands.Cog] = None,
        self.ctx = ctx
        self.len_poke = len_poke
        self.delete_message_after = delete_message_after
        self.current_page = 0
        self.message = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def update_page(self, interaction: discord.Interaction, page_number: int):
        max_pages = await self.source.get_max_pages()
        if page_number < 0:
            self.current_page = max_pages - 1
        elif page_number >= max_pages:
            self.current_page = 0
        else:
            self.current_page = page_number

        content = await self.source.format_page(self, self.current_page)
        await interaction.response.edit_message(content=None, embed=content, view=self)

    @discord.ui.button(label="First", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_page(interaction, 0)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_page(interaction, self.current_page - 1)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_page(interaction, self.current_page + 1)

    @discord.ui.button(label="Last", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        max_pages = await self.source.get_max_pages()
        await self.update_page(interaction, max_pages - 1)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.delete_message_after:
            await interaction.message.delete()
        else:
            self.stop()
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)

    async def start(self, channel: discord.abc.Messageable):
        content = await self.source.format_page(self, self.current_page)
        self.message = await channel.send(embed=content, view=self)

class SearchFormat:
    def __init__(self, entries: Iterable[str], per_page: int = 1):
        self.entries = list(entries)
        self.per_page = per_page

    async def get_max_pages(self):
        return len(self.entries) // self.per_page + (1 if len(self.entries) % self.per_page else 0)

    async def format_page(self, menu: GenericMenu, page: int) -> discord.Embed:
        entry = self.entries[page]
        embed = discord.Embed(
            title="Pokemon Search",
            color=await menu.ctx.embed_color(),
            description=entry
        )
        embed.set_footer(text=f"Page {page + 1}/{len(self.entries)}")
        return embed

class PokedexFormat:
    def __init__(self, entries: Iterable[Dict], per_page: int = 1):
        self.entries = list(entries)
        self.per_page = per_page

    async def get_max_pages(self):
        return len(self.entries) // self.per_page + (1 if len(self.entries) % self.per_page else 0)

    async def format_page(self, menu: GenericMenu, page: int) -> discord.Embed:
        items = self.entries[page * self.per_page:(page + 1) * self.per_page]
        embed = discord.Embed(title="Pokédex", color=await menu.ctx.embed_color())
        for item in items:
            # Format each item as needed for the embed
            embed.add_field(name=item["name"], value=str(item["value"]))
        embed.set_footer(text=f"Showing {page + 1}-{min(len(self.entries), (page + 1) * self.per_page)} of {len(self.entries)}.")
        return embed