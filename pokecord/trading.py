import asyncio
import json
import random

import discord
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.menus import start_adding_reactions  # Import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate, MessagePredicate
from redbot.core.i18n import Translator
from .functions import chunks, poke_embed

from .abc import MixinMeta
from .statements import *

from datetime import datetime, timedelta

poke = MixinMeta.poke

_ = Translator("Pokecord", __file__)

MAX_WONDER_TRADES_PER_DAY = 5

class TradeMixin(MixinMeta):
    """Comandos de intercambio de Pokecord"""

    @poke.command(usage="<usuario> <ID de tu pokémon> <ID de su pokémon>")
    async def trade(self, ctx, user: discord.Member, your_pokemon_id: int, their_pokemon_id: int):
        """Intercambia un Pokémon con otro usuario especificando los ID de los Pokémon."""
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

        # Solicitar confirmación del usuario que inicia el intercambio
        confirm_message = await ctx.send(
            f"Vas a intercambiar tu {your_pokemon_name} por el {their_pokemon_name} de {user.mention}. Reacciona con ✅ para continuar o ❌ para cancelar."
        )
        start_adding_reactions(confirm_message, ReactionPredicate.YES_OR_NO_EMOJIS)
        try:
            pred = ReactionPredicate.yes_or_no(confirm_message, ctx.author)
            await ctx.bot.wait_for("reaction_add", check=pred, timeout=20)
        except asyncio.TimeoutError:
            return await ctx.send("Operación cancelada por tiempo de espera.")

        if not pred.result:
            return await ctx.send("Intercambio cancelado por el iniciador.")

        # Solicitar confirmación del otro usuario
        confirm_message = await ctx.send(
            f"{user.mention}, {ctx.author.mention} quiere intercambiar su {your_pokemon_name} por tu {their_pokemon_name}. Reacciona con ✅ para aceptar o ❌ para rechazar."
        )
        start_adding_reactions(confirm_message, ReactionPredicate.YES_OR_NO_EMOJIS)

        try:
            pred = ReactionPredicate.yes_or_no(confirm_message, user)
            await ctx.bot.wait_for("reaction_add", check=pred, timeout=20)
        except asyncio.TimeoutError:
            return await ctx.send(f"{user.mention} no respondió a tiempo. Intercambio cancelado.")

        if not pred.result:
            return await ctx.send(f"{user.mention} ha rechazado el intercambio.")

        # Realizar el intercambio
        await self.cursor.execute(
            "UPDATE users SET user_id = :new_user_id WHERE message_id = :message_id",
            values={"new_user_id": user.id, "message_id": your_pokemon[1]}
        )
        await self.cursor.execute(
            "UPDATE users SET user_id = :new_user_id WHERE message_id = :message_id",
            values={"new_user_id": ctx.author.id, "message_id": their_pokemon[1]}
        )

        # Actualizar la Pokedex de ambos usuarios
        conf_author = await self.user_is_global(ctx.author)
        conf_user = await self.user_is_global(user)

        async with conf_author.pokeids() as author_pokeids, conf_user.pokeids() as user_pokeids:
            # Añadir el Pokémon del otro usuario a tu Pokedex si no está presente
            their_pokemon_id_str = str(their_pokemon[0]["id"])
            if their_pokemon_id_str not in author_pokeids:
                author_pokeids[their_pokemon_id_str] = 1
            else:
                author_pokeids[their_pokemon_id_str] += 1

            # Añadir tu Pokémon a la Pokedex del otro usuario si no está presente
            your_pokemon_id_str = str(your_pokemon[0]["id"])
            if your_pokemon_id_str not in user_pokeids:
                user_pokeids[your_pokemon_id_str] = 1
            else:
                user_pokeids[your_pokemon_id_str] += 1

        await ctx.send(
            f"¡Intercambio completado! {ctx.author.mention} ha intercambiado su {your_pokemon_name} por el {their_pokemon_name} de {user.mention}."
        )
        
    @poke.command(usage="<ID de tu pokémon>")
    async def wondertrade(self, ctx, pokemon_id: int):
        """Intercambia tu Pokémon por uno aleatorio. Límite de 5 intercambios por día."""
        user_conf = await self.user_is_global(ctx.author)
        user_conf = self.config.user(ctx.author)
        last_trade_date = await user_conf.last_trade_date()
        trade_count = await user_conf.trade_count()

        # Obtener la información de intercambio del día
        last_trade_date = await user_conf.last_trade_date()
        trade_count = await user_conf.trade_count()

        # Comprobar si es un nuevo día
        if last_trade_date != str(datetime.utcnow().date()):
            trade_count = 0
            await user_conf.last_trade_date.set(str(datetime.utcnow().date()))

        # Comprobar si se ha alcanzado el límite diario
        if trade_count >= MAX_WONDER_TRADES_PER_DAY:
            return await ctx.send(f"Has alcanzado el límite de {MAX_WONDER_TRADES_PER_DAY} intercambios por día.")
        async with ctx.typing():
            # Obtener tu Pokémon
            result = await self.cursor.fetch_all(
                query="SELECT pokemon, message_id FROM users WHERE user_id = :user_id",
                values={"user_id": ctx.author.id},
            )
            your_pokemons = []
            for i, data in enumerate(result):
                poke = json.loads(data[0])
                poke["sid"] = i + 1  # Asignar 'sid' comenzando en 1
                your_pokemons.append([poke, data[1]])

            if pokemon_id < 1 or pokemon_id > len(your_pokemons):
                return await ctx.send("No tienes un Pokémon con ese ID.")

            # Ajustar para el índice de la lista (que comienza en 0)
            your_pokemon = your_pokemons[pokemon_id - 1]

            # Generar un Pokémon aleatorio
            random_pokemon = self.pokemon_choose()

            # Ajustar nivel dentro del 10% del nivel del Pokémon intercambiado
            exchanged_level = your_pokemon[0]['level']
            level_variation = round(exchanged_level * 0.1)
            min_level = max(1, exchanged_level - level_variation)  # Asegurarse de que el nivel no sea menor que 1
            max_level = min(100, exchanged_level + level_variation)  # Asegurarse de que el nivel no sea mayor que 100
            random_pokemon["level"] = random.randint(min_level, max_level)

            # Asignar el mismo ID 'sid' al nuevo Pokémon
            random_pokemon["sid"] = your_pokemon[0]["sid"]  # Usar el mismo 'sid' que el Pokémon intercambiado
            random_pokemon["xp"] = 0
            random_pokemon["gender"] = self.gender_choose(random_pokemon["name"]["english"])
            random_pokemon["ivs"] = {
                "HP": random.randint(0, 31),
                "Attack": random.randint(0, 31),
                "Defence": random.randint(0, 31),
                "Sp. Atk": random.randint(0, 31),
                "Sp. Def": random.randint(0, 31),
                "Speed": random.randint(0, 31),
            }
            # Aquí puedes agregar cualquier otra información necesaria

            # Intercambio
            await self.cursor.execute(
                "DELETE FROM users WHERE message_id = :message_id",
                values={"message_id": your_pokemon[1]}
            )
            await self.cursor.execute(
                query=INSERT_POKEMON,
                values={
                    "user_id": ctx.author.id,
                    "message_id": ctx.message.id,
                    "pokemon": json.dumps(random_pokemon),
                },
            )

            # Obtener el ID actual del nuevo Pokémon tras agregarlo a la base de datos
            new_pokemon_result = await self.cursor.fetch_all(
                query="SELECT pokemon, message_id FROM users WHERE user_id = :user_id",
                values={"user_id": ctx.author.id},
            )
            new_pokemon_id = None
            for i, data in enumerate(new_pokemon_result, start=1):
                if data[1] == ctx.message.id:
                    new_pokemon_id = i
                    break

            if new_pokemon_id is not None:
                random_pokemon["sid"] = new_pokemon_id
            else:
                return await ctx.send("Error al obtener el ID del nuevo Pokémon.")

            # Actualizar la Pokedex del usuario
            conf = await self.user_is_global(ctx.author)
            async with conf.pokeids() as pokeids:
                poke_id_str = str(random_pokemon["id"])
                if poke_id_str not in pokeids:
                    pokeids[poke_id_str] = 1
                else:
                    pokeids[poke_id_str] += 1

            # Mostrar las estadísticas del nuevo Pokémon
            embed, _file = await poke_embed(self, ctx, random_pokemon, file=True)
            await ctx.send(
                f"Has intercambiado tu {self.get_name(your_pokemon[0]['name'], ctx.author)} por un {self.get_name(random_pokemon['name'], ctx.author)} nivel {random_pokemon['level']}.",
                embed=embed, file=_file
            )

            # Actualizar la información de intercambio
            await user_conf.trade_count.set(trade_count + 1)

            # Informar al usuario sobre los intercambios restantes
            trades_left = MAX_WONDER_TRADES_PER_DAY - trade_count - 1
            await ctx.send(
                f"Intercambio realizado. Te quedan {trades_left} intercambios por hoy.",
                embed=embed, file=_file
            )