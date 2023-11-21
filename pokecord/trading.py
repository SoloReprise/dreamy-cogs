import asyncio
import json

import discord
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.predicates import ReactionPredicate, MessagePredicate

from .abc import MixinMeta
from .statements import *

poke = MixinMeta.poke

_ = Translator("Pokecord", __file__)

class TradeMixin(MixinMeta):
    """Comandos de intercambio de Pokecord"""

    @poke.command(usage="<usuario> <ID de tu pokémon> <ID de su pokémon>")
    async def trade(self, ctx, user: discord.Member, your_pokemon_id: int, their_pokemon_id: int):
        """Intercambio de Pokémon

        Intercambia un Pokémon con otro usuario especificando los ID de los Pokémon."""
        async with ctx.typing():
            # Obtener tus Pokémon
            result = await self.cursor.fetch_all(
                query="SELECT pokemon, message_id FROM users WHERE user_id = :user_id",
                values={"user_id": ctx.author.id},
            )
            your_pokemons = [None]
            for data in result:
                your_pokemons.append([json.loads(data[0]), data[1]])

            # Obtener Pokémon del otro usuario
            result = await self.cursor.fetch_all(
                query="SELECT pokemon, message_id FROM users WHERE user_id = :user_id",
                values={"user_id": user.id},
            )
            their_pokemons = [None]
            for data in result:
                their_pokemons.append([json.loads(data[0]), data[1]])

        # Verificar si los ID de Pokémon son válidos
        if not your_pokemons or your_pokemon_id >= len(your_pokemons):
            return await ctx.send("No tienes un Pokémon con ese ID.")
        if not their_pokemons or their_pokemon_id >= len(their_pokemons):
            return await ctx.send(f"{user.mention} no tiene un Pokémon con ese ID.")

        your_pokemon = your_pokemons[your_pokemon_id]
        their_pokemon = their_pokemons[their_pokemon_id]

        your_pokemon_name = self.get_name(your_pokemon[0]["name"], ctx.author)
        their_pokemon_name = self.get_name(their_pokemon[0]["name"], user)

        # Confirmar el intercambio
        confirm_message = await ctx.send(
            f"Vas a intercambiar tu {your_pokemon_name} por el {their_pokemon_name} de {user.mention}. Reacciona con ✅ para continuar o ❌ para cancelar."
        )
        start_adding_reactions(confirm_message, ReactionPredicate.YES_OR_NO_EMOJIS)
        try:
            pred = ReactionPredicate.yes_or_no(confirm_message, ctx.author)
            await ctx.bot.wait_for("reaction_add", check=pred, timeout=20)
        except asyncio.TimeoutError:
            return await ctx.send("Operación cancelada por tiempo de espera.")

        if pred.result:
            # Intercambio
            await self.cursor.execute(
                "UPDATE users SET user_id = :new_user_id WHERE message_id = :message_id",
                values={"new_user_id": user.id, "message_id": your_pokemon[1]}
            )
            await self.cursor.execute(
                "UPDATE users SET user_id = :new_user_id WHERE message_id = :message_id",
                values={"new_user_id": ctx.author.id, "message_id": their_pokemon[1]}
            )

            await ctx.send(
                f"¡Intercambio completado! {ctx.author.mention} ha intercambiado su {your_pokemon_name} por el {their_pokemon_name} de {user.mention}."
            )
        else:
            await ctx.send("Intercambio cancelado.")