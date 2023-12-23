import asyncio
import concurrent.futures
from datetime import datetime, timedelta
import json
import logging
import random
import string
from abc import ABC

import apsw
import discord
from databases import Database
from redbot.core import Config, commands
from redbot.core.data_manager import bundled_data_path, cog_data_path
from redbot.core.i18n import Translator, cog_i18n, set_contextual_locales_from_guild
from redbot.core.utils.chat_formatting import escape, humanize_list

from .dev import Dev
from .general import GeneralMixin
from .settings import SettingsMixin
from .statements import *
from .trading import TradeMixin
from PIL import Image, ImageOps
import io
import os

log = logging.getLogger("red.flare.pokecord")

PUNCT = string.punctuation + "’"
_ = Translator("Pokecord", __file__)
GENDERS = [
    "Male \N{MALE SIGN}\N{VARIATION SELECTOR-16}",
    "Female \N{FEMALE SIGN}\N{VARIATION SELECTOR-16}",
]
_MIGRATION_VERSION = 9


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """This allows the metaclass used for proper type detection to coexist with discord.py's
    metaclass."""

TYPE_BADGES = {
    "Normal": "Medalla Básica",
    "Fire": "Medalla Ardiente",
    "Water": "Medalla Acuática",
    "Electric": "Medalla Eléctrica",
    "Grass": "Medalla Herbácea",
    "Ice": "Medalla Helada",
    "Fighting": "Medalla Peleona",
    "Poison": "Medalla Venenosa",
    "Ground": "Medalla Terrestre",
    "Flying": "Medalla Celeste",
    "Psychic": "Medalla Psíquica",
    "Bug": "Medalla Invertebrada",
    "Rock": "Medalla Rocosa",
    "Ghost": "Medalla Fantasmagórica",
    "Dragon": "Medalla Dracónica",
    "Dark": "Medalla Siniestra",
    "Steel": "Medalla Acerosa",
    "Fairy": "Medalla Feérica"
}

TYPE_BADGES_SPANISH = {
    "Normal": "Medalla Básica",
    "Fuego": "Medalla Ardiente",
    "Agua": "Medalla Acuática",
    "Eléctrico": "Medalla Eléctrica",
    "Planta": "Medalla Herbácea",
    "Hielo": "Medalla Helada",
    "Lucha": "Medalla Peleona",
    "Veneno": "Medalla Venenosa",
    "Tierra": "Medalla Terrestre",
    "Volador": "Medalla Celeste",
    "Psíquico": "Medalla Psíquica",
    "Bicho": "Medalla Invertebrada",
    "Roca": "Medalla Rocosa",
    "Fantasma": "Medalla Fantasmagórica",
    "Dragón": "Medalla Dracónica",
    "Siniestro": "Medalla Siniestra",
    "Acero": "Medalla Acerosa",
    "Hada": "Medalla Feérica"
}

SPANISH_TO_ENGLISH_TYPES  = {
    "Normal": "Normal",
    "Fuego": "Fire",
    "Agua": "Water",
    "Eléctrico": "Electric",
    "Planta": "Grass",
    "Hielo": "Ice",
    "Lucha": "Fighting",
    "Veneno": "Poison",
    "Tierra": "Ground",
    "Volador": "Flying",
    "Psíquico": "Psychic",
    "Bicho": "Bug",
    "Roca": "Rock",
    "Fantasma": "Ghost",
    "Dragón": "Dragon",
    "Siniestro": "Dark",
    "Acero": "Steel",
    "Hada": "Fairy"
}

ENGLISH_TO_SPANISH_TYPES  = {
    "Normal": "Normal",
    "Fire": "Fuego",
    "Water": "Agua",
    "Electric": "Eléctrico",
    "Grass": "Planta",
    "Ice": "Hielo",
    "Fighting": "Lucha",
    "Poison": "Veneno",
    "Ground": "Tierra",
    "Flying": "Volador",
    "Psychic": "Psíquico",
    "Bug": "Bicho",
    "Rock": "Roca",
    "Ghost": "Fantasma",
    "Dragon": "Dragón",
    "Dark": "Siniestro",
    "Steel": "Acero",
    "Fairy": "Hada"
}
@cog_i18n(_)
class Pokecord(
    Dev,
    TradeMixin,
    SettingsMixin,
    GeneralMixin,
    commands.Cog,
    metaclass=CompositeMetaClass,
):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, identifier=95932766180343808, force_registration=True)
        self.config.register_global(
            isglobal=True,
            hashed=False,
            hashes={},
            spawnchance=[20, 120],
            hintcost=1000,
            spawnloop=False,
            migration=1,
        )
        defaults_guild = {
            "activechannels": [],
            "toggle": False,
            "whitelist": [],
            "blacklist": [],
            "levelup_messages": False,
        }
        self.config.register_guild(**defaults_guild)
        defaults_user = {
            "pokeids": {},
            "badges": [],  # List to store the names of the badges earned
            "silence": False,
            "timestamp": 0,
            "pokeid": 1,
            "has_starter": False,
            "locale": "en",
            "last_trade_date": str(datetime.utcnow().date()),
            "trade_count": 0,
            "incienso_count": 0,  # New key to track the number of Incienso
        }
        self.config.register_user(**defaults_user)
        self.config.register_member(**defaults_user)
        self.config.register_channel(pokemon=None)
        self.datapath = f"{bundled_data_path(self)}"
        self.maybe_spawn = {}
        self.guildcache = {}
        self.usercache = {}
        self.spawnchance = []
        self.cursor = Database(f"sqlite:///{cog_data_path(self)}/pokemon.db")
        self._executor = concurrent.futures.ThreadPoolExecutor(1)
        self.bg_loop_task = None

    def cog_unload(self):
        self._executor.shutdown()
        if self.bg_loop_task:
            self.bg_loop_task.cancel()

    async def initalize(self):
        await self.cursor.connect()
        await self.cursor.execute(PRAGMA_journal_mode)
        await self.cursor.execute(PRAGMA_wal_autocheckpoint)
        await self.cursor.execute(PRAGMA_read_uncommitted)
        await self.cursor.execute(POKECORD_CREATE_POKECORD_TABLE)
        with open(f"{self.datapath}/pokedex.json", encoding="utf-8") as f:
            pdata = json.load(f)
        with open(f"{self.datapath}/evolve.json", encoding="utf-8") as f:
            self.evolvedata = json.load(f)
        with open(f"{self.datapath}/genders.json", encoding="utf-8") as f:
            self.genderdata = json.load(f)
        with open(f"{self.datapath}/shiny.json", encoding="utf-8") as f:
            sdata = json.load(f)
        with open(f"{self.datapath}/legendary.json", encoding="utf-8") as f:
            ldata = json.load(f)
        with open(f"{self.datapath}/mythical.json", encoding="utf-8") as f:
            mdata = json.load(f)
        with open(f"{self.datapath}/galarian.json", encoding="utf-8") as f:
            gdata = json.load(f)
        with open(f"{self.datapath}/hisuian.json", encoding="utf-8") as f:
            gdata = json.load(f)
        with open(f"{self.datapath}/paldea.json", encoding="utf-8") as f:
            gdata = json.load(f)
        with open(f"{self.datapath}/alolan.json", encoding="utf-8") as f:
            adata = json.load(f)
        with open(f"{self.datapath}/megas.json", encoding="utf-8") as f:
            megadata = json.load(f)
        self.pokemondata = pdata + sdata + ldata + mdata + gdata + adata + megadata
        with open(f"{self.datapath}/url.json", encoding="utf-8") as f:
            url = json.load(f)
        for pokemon in self.pokemondata:
            name = (
                pokemon["name"]["english"]
                if not pokemon.get("variant")
                else pokemon.get("alias")
                if pokemon.get("alias")
                else pokemon["name"]["english"]
            )
            if "shiny" in name.lower():
                continue
            link = url[name]
            if isinstance(link, list):
                link = link[0]
            pokemon["url"] = link

        self.spawnchances = [x["spawnchance"] for x in self.pokemondata]
        self.pokemonlist = {
            pokemon["id"]: {
                "name": pokemon["name"],
                "amount": 0,
                "id": f"#{str(pokemon['id']).zfill(3)}",
            }
            for pokemon in sorted((self.pokemondata), key=lambda x: x["id"])
        }
        if await self.config.migration() < _MIGRATION_VERSION:
            self.usercache = await self.config.all_users()
            for user in self.usercache:
                await self.config.user_from_id(user).pokeids.clear()
                result = await self.cursor.fetch_all(
                    query=SELECT_POKEMON,
                    values={"user_id": user},
                )
                async with self.config.user_from_id(user).pokeids() as pokeids:
                    for data in result:
                        poke = json.loads(data[0])
                        if str(poke["id"]) not in pokeids:
                            pokeids[str(poke["id"])] = 1
                        else:
                            pokeids[str(poke["id"])] += 1

                        if not poke.get("gender", False):
                            if isinstance(poke["name"], str):
                                poke["gender"] = self.gender_choose(poke["name"])
                            else:
                                poke["gender"] = self.gender_choose(poke["name"]["english"])

                        if not poke.get("ivs", False):
                            poke["ivs"] = {
                                "HP": random.randint(0, 31),
                                "Attack": random.randint(0, 31),
                                "Defence": random.randint(0, 31),
                                "Sp. Atk": random.randint(0, 31),
                                "Sp. Def": random.randint(0, 31),
                                "Speed": random.randint(0, 31),
                            }

                        await self.cursor.execute(
                            query=UPDATE_POKEMON,
                            values={
                                "user_id": user,
                                "message_id": data[1],
                                "pokemon": json.dumps(poke),
                            },
                        )
                await self.config.migration.set(_MIGRATION_VERSION)
            log.info("Pokecord Migration complete.")

        await self.update_guild_cache()
        await self.update_spawn_chance()
        await self.update_user_cache()
        if await self.config.spawnloop():
            self.bg_loop_task = self.bot.loop.create_task(self.random_spawn())

    async def check_activity(self, guild_id):
        """Check for activity in the active channels of a guild.

        Args:
            guild_id (int): The ID of the guild to check for activity.

        Returns:
            bool: True if there's recent activity, False otherwise.
        """
        active_channels = self.guildcache[str(guild_id)]["activechannels"]
        time_limit = datetime.utcnow() - datetime.timedelta(minutes=10)

        for channel_id in active_channels:
            channel = self.bot.get_channel(int(channel_id))
            if channel is None:
                continue

            # Fetching the history of the channel to check for recent messages
            try:
                async for message in channel.history(limit=100, after=time_limit):
                    if message.created_at > time_limit:
                        return True
            except Exception as exc:
                log.error("Error checking activity in channel: ", exc_info=exc)
                continue

        return False

    async def random_spawn(self):
        await self.bot.wait_until_ready()
        log.debug("Starting loop for random spawns.")
        while True:
            try:
                for guild in self.guildcache:
                    if (
                        self.guildcache[guild]["toggle"]
                        and self.guildcache[guild]["activechannels"]
                    ):
                        if random.randint(1, 2) == 2:
                            continue
                        _guild = self.bot.get_guild(int(guild))
                        if _guild is None:
                            continue
                        channel = _guild.get_channel(
                            int(random.choice(self.guildcache[guild]["activechannels"]))
                        )
                        if channel is None:
                            continue
                        await self.spawn_pokemon(channel)
                        # Check if there is activity on the channel and set sleep time accordingly
                        if await self.check_activity(guild):  # Note the 'await' since it's an async function
                            sleep_time = 300  # 5 minutes
                        else:
                            sleep_time = 600  # 10 minutes
                    else:
                        sleep_time = 2400  # Original 40 minutes sleep time as a fallback
                    await asyncio.sleep(sleep_time)
            except Exception as exc:
                log.error("Exception in pokemon auto spawning: ", exc_info=exc)

    async def update_guild_cache(self):
        self.guildcache = await self.config.all_guilds()

    async def update_user_cache(self):
        self.usercache = await self.config.all_users()  # TODO: Support guild

    async def update_spawn_chance(self):
        self.spawnchance = await self.config.spawnchance()

    async def is_global(self, guild):
        toggle = await self.config.isglobal()
        if toggle:
            return self.config
        return self.config.guild(guild)

    async def user_is_global(self, user):
        toggle = await self.config.isglobal()
        if toggle:
            return self.config.user(user)
        return self.config.member(user)

    def pokemon_choose(self):
        return random.choices(self.pokemondata, weights=self.spawnchances, k=1)[0]

    def gender_choose(self, name):
        poke = self.genderdata.get(name, None)
        if poke is None:
            return "N/A"
        if poke == -1:
            return "Genderless"
        weights = [1 - (poke / 8), poke / 8]
        return random.choices(GENDERS, weights=weights)[0]

    def get_name(self, names, user):
        if isinstance(names, str):
            return names
        userconf = self.usercache.get(user.id)
        if userconf is None:
            return names["english"]
        localnames = {
            "en": names["english"],
            "fr": names["french"],
            "tw": names["chinese"],
            "jp": names["japanese"],
        }
        return (
            localnames[self.usercache[user.id]["locale"]]
            if localnames[self.usercache[user.id]["locale"]] is not None
            else localnames["en"]
        )

    def get_pokemon_name(self, pokemon: dict) -> set:
        """function returns all name for specified pokemon"""
        return {
            pokemon["name"][name].lower()
            for name in pokemon["name"]
            if pokemon["name"][name] is not None
        }

    @commands.command()
    async def starter(self, ctx, pokemon: str = None):
        """Choose your starter pokémon!"""
        conf = await self.user_is_global(ctx.author)
        if await conf.has_starter():
            return await ctx.send(_("You've already claimed your starter pokemon!"))
        if pokemon is None:
            msg = _(
                "Hey there trainer! Welcome to Pokecord. This is a ported plugin version of Pokecord adopted for use on Red.\n"
                "In order to get catchin' you must pick one of the starter Pokemon as listed below.\n"
                "**Generation 1**\nBulbasaur, Charmander and Squirtle\n"
                "**Generation 2**\nChikorita, Cyndaquil, Totodile\n"
                "**Generation 3**\nTreecko, Torchic, Mudkip\n"
                "**Generation 4**\nTurtwig, Chimchar, Piplup\n"
                "**Generation 5**\nSnivy, Tepig, Oshawott\n"
                "**Generation 6**\nChespin, Fennekin, Froakie\n"
                "**Generation 7**\nRowlet, Litten, Popplio\n"
                "**Generation 8**\nGrookey, Scorbunny, Sobble\n"
                "**Generation 9**\Sprigatito, Fuecoco, Quaxly\n"
            )
            msg += _("\nTo pick a pokemon, type {prefix}starter <pokemon>").format(
                prefix=ctx.clean_prefix
            )
            await ctx.send(msg)
            return
        starter_pokemon = {
            "bulbasaur": self.pokemondata[0],
            "charmander": self.pokemondata[3],
            "squirtle": self.pokemondata[6],
            "chikorita": self.pokemondata[146],
            "cyndaquil": self.pokemondata[149],
            "totodile": self.pokemondata[152],
            "treecko": self.pokemondata[240],
            "torchic": self.pokemondata[243],
            "mudkip": self.pokemondata[246],
            "turtwig": self.pokemondata[365],
            "chimchar": self.pokemondata[368],
            "piplup": self.pokemondata[371],
            "snivy": self.pokemondata[458],
            "tepig": self.pokemondata[461],
            "oshawott": self.pokemondata[464],
            "chespin": self.pokemondata[601],
            "fennekin": self.pokemondata[604],
            "froakie": self.pokemondata[607],
            "rowlet": self.pokemondata[668],
            "litten": self.pokemondata[671],
            "popplio": self.pokemondata[674],
            "grookey": self.pokemondata[740],
            "scorbunny": self.pokemondata[743],
            "sobble": self.pokemondata[746],
            "sprigatito": self.pokemondata[906],
            "fuecoco": self.pokemondata[909],
            "quaxly": self.pokemondata[912]
        }

        for starter in starter_pokemon.values():
            if pokemon.lower() in self.get_pokemon_name(starter):
                break

        else:
            return await ctx.send(_("That's not a valid starter pokémon, trainer!"))

        await ctx.send(
            _("You've chosen {pokemon} as your starter pokémon!").format(pokemon=pokemon.title())
        )

        # starter dict
        starter["level"] = 1
        starter["xp"] = 0
        starter["ivs"] = {
            "HP": random.randint(0, 31),
            "Attack": random.randint(0, 31),
            "Defence": random.randint(0, 31),
            "Sp. Atk": random.randint(0, 31),
            "Sp. Def": random.randint(0, 31),
            "Speed": random.randint(0, 31),
        }
        starter["gender"] = self.gender_choose(starter["name"]["english"])

        await self.cursor.execute(
            query=INSERT_POKEMON,
            values={
                "user_id": ctx.author.id,
                "message_id": ctx.message.id,
                "pokemon": json.dumps(starter),
            },
        )
        await conf.has_starter.set(True)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def hint(self, ctx):
        """Get a hint on the pokémon!"""
        pokemonspawn = await self.config.channel(ctx.channel).pokemon()
        if pokemonspawn is not None:
            name = self.get_name(pokemonspawn["name"], ctx.author)
            inds = [i for i, _ in enumerate(name)]
            if len(name) > 6:
                amount = len(name) - random.randint(2, 4)
            elif len(name) < 4:
                amount = random.randint(1, 2)
            else:
                amount = random.randint(3, 4)
            sam = random.sample(inds, amount)

            lst = list(name)
            for ind in sam:
                if lst[ind] != " ":
                    lst[ind] = "_"
            word = "".join(lst)
            await ctx.send(
                _("This wild pokemon is a {pokemonhint}.").format(
                    pokemonhint=escape(word, formatting=True)
                )
            )
            return
        await ctx.send(_("No pokemon is ready to be caught."))

    @commands.command()
    async def catch(self, ctx, *, pokemon: str):
        """Catch a pokemon!"""
        conf = await self.user_is_global(ctx.author)
        if not await conf.has_starter():
            return await ctx.send(
                _(
                    "You haven't chosen a starter pokemon yet, check out `{prefix}starter` for more information."
                ).format(prefix=ctx.clean_prefix)
            )
        pokemonspawn = await self.config.channel(ctx.channel).pokemon()
        if pokemonspawn is not None:
            names = self.get_pokemon_name(pokemonspawn)
            names.add(
                pokemonspawn["name"]["english"].translate(str.maketrans("", "", PUNCT)).lower()
            )
            if pokemonspawn.get("alias"):
                names.add(pokemonspawn["alias"].lower())
            if pokemon.lower() not in names:
                return await ctx.send(_("That's not the correct pokemon"))
            if await self.config.channel(ctx.channel).pokemon() is not None:
                await self.config.channel(ctx.channel).pokemon.clear()
            else:
                await ctx.send("No pokemon is ready to be caught.")
                return
            lvl = random.randint(1, 13)
            pokename = self.get_name(pokemonspawn["name"], ctx.author)
            variant = f'{pokemonspawn.get("variant")} ' if pokemonspawn.get("variant") else ""
            msg = _(
                "Congratulations {user}! You've caught a level {lvl} {variant}{pokename}!"
            ).format(
                user=ctx.author.mention,
                lvl=lvl,
                variant=variant,
                pokename=pokename,
            )

            if random.randint(1, 10) == 1:  # Always true for testing
                try:
                    user_conf = await self.user_is_global(ctx.author)
                    incienso_count = await user_conf.incienso_count()
                    new_incienso_count = incienso_count + 1
                    await user_conf.incienso_count.set(new_incienso_count)
                    await ctx.send(_("¡Has encontrado un Incienso!"))
                except Exception as e:
                    log.error(f"Error while adding Incienso: {e}")
                    await ctx.send(_("There was an error while processing your Incienso."))

            async with conf.pokeids() as poke:
                if str(pokemonspawn["id"]) not in poke:
                    msg += _("\n{pokename} has been added to the pokédex.").format(
                        pokename=pokename
                    )

                    poke[str(pokemonspawn["id"])] = 1
                else:
                    poke[str(pokemonspawn["id"])] += 1
            pokemonspawn["level"] = lvl
            pokemonspawn["xp"] = 0
            pokemonspawn["gender"] = self.gender_choose(pokemonspawn["name"]["english"])
            pokemonspawn["ivs"] = {
                "HP": random.randint(0, 31),
                "Attack": random.randint(0, 31),
                "Defence": random.randint(0, 31),
                "Sp. Atk": random.randint(0, 31),
                "Sp. Def": random.randint(0, 31),
                "Speed": random.randint(0, 31),
            }
            await self.cursor.execute(
                query=INSERT_POKEMON,
                values={
                    "user_id": ctx.author.id,
                    "message_id": ctx.message.id,
                    "pokemon": json.dumps(pokemonspawn),
                },
            )
            # After successfully catching a pokemon
            await ctx.send(msg)  # Notify the user about the catch

            # Update badges and notify the user if they earn new ones
            new_badges = await self.update_user_badges(ctx.author.id)
            if new_badges:
                badge_names = ", ".join(new_badges)
                await ctx.send(f"Felicidades {ctx.author.mention}, has ganado nuevas medallas: {badge_names}")
            return
        await ctx.send(_("No pokemon is ready to be caught."))

    def spawn_chance(self, guildid):
        return self.maybe_spawn[guildid]["amount"] > self.maybe_spawn[guildid]["spawnchance"]

    # async def get_hash(self, pokemon):
    #     return (await self.config.hashes()).get(pokemon, None)

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if not message.guild:
            return
        if message.author.bot:
            return
        guildcache = self.guildcache.get(message.guild.id)
        if guildcache is None:
            return
        if not guildcache["toggle"]:
            return
        await self.exp_gain(message.channel, message.author)
        if guildcache["whitelist"]:
            if message.channel.id not in guildcache["whitelist"]:
                return
        elif guildcache["blacklist"]:
            if message.channel.id in guildcache["blacklist"]:
                return
        if message.guild.id not in self.maybe_spawn:
            self.maybe_spawn[message.guild.id] = {
                "amount": 1,
                "spawnchance": random.randint(self.spawnchance[0], self.spawnchance[1]),
                "time": datetime.utcnow().timestamp(),
                "author": message.author.id,
            }  # TODO: big value
        if (
            self.maybe_spawn[message.guild.id]["author"] == message.author.id
        ):  # stop spamming to spawn
            if (
                datetime.utcnow().timestamp() - self.maybe_spawn[message.guild.id]["time"]
            ) < 5:
                return
        self.maybe_spawn[message.guild.id]["amount"] += 1
        should_spawn = self.spawn_chance(message.guild.id)
        if not should_spawn:
            return
        del self.maybe_spawn[message.guild.id]
        if not guildcache["activechannels"]:
            channel = message.channel
        else:
            channel = message.guild.get_channel(int(random.choice(guildcache["activechannels"])))
            if channel is None:
                return  # TODO: Remove channel from config
        await set_contextual_locales_from_guild(self.bot, message.guild)
        await self.spawn_pokemon(channel)

    TYPE_BACKGROUND_MAPPING = {
        "Normal": ["route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Fire": ["cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],  # List of possible backgrounds
        "Water": ["beach.jpg", "water.jpg", "water_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Electric": ["cave.jpg", "cave_2.jpg", "forest.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Fighting": ["cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Grass": ["forest.jpg", "forest_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Poison": ["forest.jpg", "forest_2.jpg", "cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Ground": ["cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Rock": ["cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Flying": ["sky.jpg", "sky_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Psychic": ["forest_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Bug": ["forest.jpg", "forest_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Ghost": ["forest.jpg", "forest_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Dragon": ["cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Steel": ["cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Dark": ["forest.jpg", "forest_2.jpg", "cave.jpg", "cave_2.jpg", "route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Fairy": ["route.jpg", "route_2.jpg", "route_3.jpg", "route_4.jpg"],
        "Ice": ["ice.jpg", "ice_2.jpg", "route_3.jpg", "route_4.jpg"],
    }

    async def spawn_pokemon(self, channel, *, pokemon=None):
        if pokemon is None:
            pokemon = self.pokemon_choose()

        prefixes = await self.bot.get_valid_prefixes(guild=channel.guild)
        embed = discord.Embed(
            title=_("A wild pokémon has appeared!"),
            description=_(
                "Guess the pokémon and type {prefix}catch <pokémon> to catch it!"
            ).format(prefix=prefixes[0]),
            color=await self.bot.get_embed_color(channel),
        )

        log.debug(f"{pokemon['name']['english']} has spawned in {channel} on {channel.guild}")

        # Determine the background image based on Pokémon type
        types = pokemon['type']
        bg_images = self.determine_background(types)

        # Choose a random background image from the available options
        bg_image_path = self.choose_random_background(bg_images)
        background = Image.open(bg_image_path).resize((800, 500), Image.Resampling.LANCZOS)

        # Load pokemon image
        pokemon_image_path = (
            self.datapath
            + f'/pokemon/{pokemon["name"]["english"] if not pokemon.get("variant") else pokemon.get("alias") if pokemon.get("alias") else pokemon["name"]["english"]}.png'.replace(
                ":", ""
            )
        )
        pokemon_image = Image.open(pokemon_image_path).convert("RGBA")

        # Calculate new size for pokemon image (60% of background)
        scale_width = background.width * 0.9
        scale_height = background.height * 0.9
        # Maintaining aspect ratio
        aspect_ratio = min(scale_width / pokemon_image.width, scale_height / pokemon_image.height)
        new_width = int(pokemon_image.width * aspect_ratio)
        new_height = int(pokemon_image.height * aspect_ratio)
        pokemon_image = pokemon_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center pokemon image on background
        offset = ((background.width - new_width) // 2, (background.height - new_height) // 2)
        background.paste(pokemon_image, offset, pokemon_image)

        # Center pokemon image on background
        offset = ((background.width - new_width) // 2, (background.height - new_height) // 2)
        background.paste(pokemon_image, offset, pokemon_image)

        # Save to a BytesIO object
        img_byte_arr = io.BytesIO()
        background.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Create discord file
        _file = discord.File(fp=img_byte_arr, filename="pokemonspawn.png")

        embed.set_image(url="attachment://pokemonspawn.png")

        await channel.send(embed=embed, file=_file)
        await self.config.channel(channel).pokemon.set(pokemon)

        await asyncio.sleep(180)

        # Check if the pokemon is still there
        pokemonspawn = await self.config.channel(channel).pokemon()
        if pokemonspawn is not None:
            # If the pokemon is the same that was spawned
            if pokemonspawn["id"] == pokemon["id"]:
                await self.config.channel(channel).pokemon.clear()
                await channel.send(f"¡El Pokémon salvaje ha huído! ¡El Pokémon salvaje era {pokemon['name']['english']}!")
        
    def determine_background(self, types):
        # Determine the appropriate background(s) based on Pokémon type
        bg_images = []
        for _type in types:
            if _type in self.TYPE_BACKGROUND_MAPPING:
                bg_images.extend(self.TYPE_BACKGROUND_MAPPING[_type])
        if not bg_images:
            # If no specific backgrounds found, use the default background
            bg_images.append("route.jpg")
        return bg_images

    def choose_random_background(self, bg_images):
        # Choose a random background image from the available options
        return os.path.join(
            "/home/unitedlegacy/.local/share/Red-DiscordBot/data/Spribotito/cogs/RepoManager/repos/dreamy-cogs/pokecord/data/backgrounds",
            random.choice(bg_images),
        )
    
    def calc_xp(self, lvl):
        return 25 * lvl

    async def handle_evolution(self, user, pokemon, channel):
        # Determine if evolution is possible
        is_shiny = 'Shiny' in pokemon["name"]["english"]
        lookup_name = pokemon["name"]["english"].replace("Shiny ", "") if is_shiny else pokemon["name"]["english"]
        evolve = self.evolvedata.get(lookup_name)

        if evolve is None or (pokemon["level"] < int(evolve["level"])):
            return  # No evolution at this level

        # Evolution process starts
        original_name = self.get_name(pokemon["name"], user)
        evolved_pokemon_name = evolve["evolution"]
        if is_shiny:
            evolved_pokemon_name = "Shiny " + evolved_pokemon_name
        await channel.send(f"¡<@{user.id}>, algo pasa con tu {original_name}!")
        await asyncio.sleep(2)  # Short pause for effect
        await channel.send(f"¡{original_name} está evolucionando!")

        # Fetch evolved Pokémon data
        evolved_pokemon = next(
            (item for item in self.pokemondata if item["name"]["english"] == evolved_pokemon_name),
            None,
        )
        if evolved_pokemon is None:
            return  # Evolved pokemon data not found

        # Update pokemon data
        pokemon.update({
            "name": evolved_pokemon["name"],
            "type": evolved_pokemon["type"],
            "level": pokemon["level"],  # Keep current level
            "xp": 0,  # Reset XP
            "ivs": pokemon["ivs"],  # Keep IVs
            "gender": pokemon["gender"],  # Keep gender
            "stats": pokemon["stats"],  # Keep stats
        })

        # Create evolution embed
        embed = discord.Embed(
            title=f"¡Enhorabuena, @{user.display_name}!",
            description=f"¡Tu {original_name} ha evolucionado a {evolved_pokemon_name}!",
            color=await self.bot.get_embed_color(channel),
        )

        # Adjust image path for shiny Pokémon
        evolved_image_name = evolved_pokemon_name.replace(" ", "")
        if is_shiny:
            evolved_image_name = evolved_image_name + "_Shiny"

        background_path = "/home/unitedlegacy/.local/share/Red-DiscordBot/data/Spribotito/cogs/RepoManager/repos/dreamy-cogs/pokecord/data/backgrounds/evolution.jpg"
        background = Image.open(background_path).resize((800, 500), Image.Resampling.LANCZOS)
        evolved_pokemon_image_path = (
            self.datapath + f'/pokemon/{evolved_image_name}.png'
        )
        evolved_pokemon_image = Image.open(evolved_pokemon_image_path).convert("RGBA")

        # Calculate new size for evolved pokemon image (85% of background)
        scale_width = background.width * 0.85
        scale_height = background.height * 0.85
        aspect_ratio = min(scale_width / evolved_pokemon_image.width, scale_height / evolved_pokemon_image.height)
        new_width = int(evolved_pokemon_image.width * aspect_ratio)
        new_height = int(evolved_pokemon_image.height * aspect_ratio)
        evolved_pokemon_image = evolved_pokemon_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center evolved pokemon image on background
        offset = ((background.width - new_width) // 2, (background.height - new_height) // 2)
        background.paste(evolved_pokemon_image, offset, evolved_pokemon_image)

        # Save to a BytesIO object
        img_byte_arr = io.BytesIO()
        background.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        _file = discord.File(fp=img_byte_arr, filename="evolvedpokemon.png")
        embed.set_image(url="attachment://evolvedpokemon.png")

        await channel.send(embed=embed, file=_file)

    async def evolve_pokemon(self, user, pokemon, channel, method):
        # Placeholder for future evolution methods
        if method == "trade":
            # Logic for trade evolution
            pass
        elif method == "stone":
            # Logic for stone evolution
            pass
        # Add more methods as needed

    async def exp_gain(self, channel, user):
        userconf = self.usercache.get(user.id)
        if userconf is None:
            return
        if datetime.utcnow().timestamp() - userconf["timestamp"] < 10:
            return

        self.usercache[user.id]["timestamp"] = datetime.utcnow().timestamp()
        await self.config.user(user).timestamp.set(
            datetime.utcnow().timestamp()
        )
        await self.update_user_cache()
        result = await self.cursor.fetch_all(query=SELECT_POKEMON, values={"user_id": user.id})
        pokemons = []
        for data in result:
            pokemons.append([json.loads(data[0]), data[1]])
        if not pokemons:
            return
        index = userconf["pokeid"] - 1
        pokemon = None
        if userconf["pokeid"] > len(pokemons):
            index = 0
        if pokemons[index][0]["level"] < 100:
            pokemon = pokemons[index][0]
            msg_id = pokemons[index][1]
        else:
            for i, poke in enumerate(pokemons):
                if poke[0]["level"] < 100:
                    pokemon = poke[0]
                    msg_id = poke[1]
                    break
        if pokemon is None:
            return  # No pokemon available to lvl up
        xp = random.randint(5, 25) + (pokemon["level"] // 2)
        pokemon["xp"] += xp

        if pokemon["xp"] >= self.calc_xp(pokemon["level"]):
            pokemon["level"] += 1
            pokemon["xp"] = 0
            await self.handle_evolution(user, pokemon, channel)  # Evolution check and handling

            # Update pokemon stats and message if evolution didn't happen
            for stat in pokemon["stats"]:
                pokemon["stats"][stat] = int(pokemon["stats"][stat]) + random.randint(1, 3)
            embed = discord.Embed(
                title=_("Congratulations {user}!").format(user=user.display_name),
                description=_("Your {name} has levelled up to level {level}!").format(
                    name=self.get_name(pokemon["name"], user), level=pokemon["level"]
                ),
                color=await self.bot.get_embed_color(channel),
            )
            if self.guildcache[channel.guild.id].get("levelup_messages"):
                if channel.id in self.guildcache[channel.guild.id]["activechannels"]:
                    await channel.send(embed=embed)
                elif not self.guildcache[channel.guild.id]["activechannels"]:
                    await channel.send(embed=embed)

        await self.cursor.execute(
            query=UPDATE_POKEMON,
            values={"user_id": user.id, "message_id": msg_id, "pokemon": json.dumps(pokemon)},
        )
        # task = functools.partial(self.safe_write, UPDATE_POKEMON, data)
        # await self.bot.loop.run_in_executor(self._executor, task)

    @commands.command(hidden=True)
    async def pokesim(self, ctx, amount: int = 1000000):
        """Sim pokemon spawning - This is blocking."""
        a = {}
        for _ in range(amount):
            pokemon = self.pokemon_choose()
            variant = pokemon.get("variant", "Normal")
            if variant not in a:
                a[variant] = 1
            else:
                a[variant] += 1
        await ctx.send(a)

    @commands.command()
    @commands.is_owner()  # Ensures that only the bot owner can use this command
    async def createspawn(self, ctx):
        """Creates a test Pokemon spawn in the active channel."""
        # Check if the guild is in the guild cache
        guildcache = self.guildcache.get(ctx.guild.id)
        if not guildcache or not guildcache["activechannels"]:
            await ctx.send("No active channels found for spawning.")
            return

        # Choose a random active channel
        channel_id = random.choice(guildcache["activechannels"])
        channel = ctx.guild.get_channel(int(channel_id))
        if channel is None:
            await ctx.send("Selected channel is not valid.")
            return

        # Choose a random Pokemon to spawn
        pokemon = self.pokemon_choose()  # Assuming you have a method to select a random Pokemon

        # Spawn the Pokemon in the selected channel
        await ctx.send(f"A test Pokémon spawn has been created in {channel.mention}.")
        await self.spawn_pokemon(channel, pokemon=pokemon)

    @commands.command()
    async def incienso(self, ctx):
        try:
            user_conf = await self.user_is_global(ctx.author)
            incienso_count = await user_conf.incienso_count()

            if incienso_count <= 0:
                await ctx.send(_("¡No te quedan inciensos!"))
                return

            new_incienso_count = incienso_count - 1
            await user_conf.incienso_count.set(new_incienso_count)

            await ctx.send(_("Has usado un incienso. Ha aparecido un Pokémon salvaje..."))
            await self.spawn_pokemon(ctx.channel)  # Assuming this method spawns a Pokémon

        except Exception as e:
            log.error(f"Error updating incienso count for user {ctx.author}: {e}")
            await ctx.send(_("Error updating incienso count. Please try again later."))
            return  # Ensure command execution stops here if an error occurs

    async def update_user_badges(self, user_id):
        user_conf = await self.user_is_global(user_id)
        user_pokemons = await user_conf.pokeids()

        # Count Pokémon by type
        type_counts = self.count_pokemon_by_type(user_pokemons)

        # Determine which badges to award
        new_badges = self.determine_badges(type_counts)

        # Update the user's badges
        current_badges = await user_conf.badges()
        awarded_badges = []  # List to keep track of newly awarded badges
        for badge in new_badges:
            if badge not in current_badges:
                current_badges.append(badge)
                awarded_badges.append(badge)  # Add to awarded badges list

        await user_conf.badges.set(current_badges)
        return awarded_badges  # Return the list of newly awarded badges

    def count_pokemon_by_type(self, user_pokemons):
        type_counts = {type_name: 0 for type_name in TYPE_BADGES.keys()}

        for poke_id in user_pokemons:
            pokemon = self.pokemondata[int(poke_id)]  # Retrieve Pokémon data by ID
            pokemon_types = pokemon['type']  # Assuming each Pokémon data has a 'types' field

            for type_name in pokemon_types:
                if type_name in type_counts:
                    type_counts[type_name] += 1

        return type_counts

    def determine_badges(self, type_counts):
        new_badges = []

        for type_name, count in type_counts.items():
            total_in_type = self.count_total_pokemon_in_type(type_name)
            if count >= total_in_type / 2:
                badge_name = TYPE_BADGES[type_name]
                new_badges.append(badge_name)

        return new_badges
    
    @commands.command()
    async def updatebadges(self, ctx):
        new_badges = await self.update_user_badges(ctx.author.id)
        if new_badges:
            badge_names = ", ".join(new_badges)
            await ctx.send(f"Felicidades {ctx.author.mention}, has ganado nuevas medallas: {badge_names}")
        else:
            await ctx.send("No hay nuevas medallas esta vez.")

    def count_total_pokemon_in_type(self, type_name):
        # Count the total number of Pokémon in the given type
        return sum(1 for pokemon in self.pokemondata if type_name in pokemon['type'])

    @commands.command()
    async def badgecountdown(self, ctx):
        """Displays the countdown for all types of Pokémon badges."""
        user_conf = await self.user_is_global(ctx.author)
        user_pokemons = await user_conf.pokeids()

        embed = discord.Embed(title="Pokémon Badge Countdown", color=discord.Color.blue())

        for spanish_type, english_type in SPANISH_TO_ENGLISH_TYPES.items():
            # Count Pokémon of the specified type
            type_count = self.count_pokemon_of_type(user_pokemons, english_type)

            # Determine the total required for the badge
            total_required = self.count_total_pokemon_in_type(english_type) // 2
            remaining = max(total_required - type_count, 0)

            badge_name = TYPE_BADGES_SPANISH[spanish_type]
            embed.add_field(name=f"{badge_name} ({spanish_type})", 
                            value=f"Tienes {type_count}. Necesitas {remaining} más para conseguir la medalla.",
                            inline=False)

        await ctx.send(embed=embed)

    def count_pokemon_of_type(self, user_pokemons, pokemon_type):
        """Counts the number of Pokémon of a specific type the user has."""
        count = 0
        for poke_id in user_pokemons:
            pokemon = self.pokemondata[int(poke_id)]  # Retrieve Pokémon data by ID
            if pokemon_type in pokemon['type']:  # Assuming each Pokémon has a 'types' field
                count += 1

        return count
    
    @commands.command()
    async def shinylist(self, ctx):
        """Lists all the shiny Pokémon a user has."""
        user_conf = await self.user_is_global(ctx.author)
        result = await self.cursor.fetch_all(query=SELECT_POKEMON, values={"user_id": ctx.author.id})
        shiny_pokemons = []

        for i, data in enumerate(result, start=1):
            pokemon = json.loads(data[0])
            if isinstance(pokemon, dict) and pokemon.get("variant") == "Shiny":
                pokemon["sid"] = i  # Assign a unique sequential ID to each Pokémon
                shiny_pokemons.append(pokemon)

        if shiny_pokemons:
            shiny_list = [f"{pokemon['name']['english']} (ID: {pokemon['sid']})" for pokemon in shiny_pokemons]
            message = _("¡Has encontrado un total de {count} shinies!\n{shinies}").format(
                count=len(shiny_pokemons), 
                shinies=", ".join(shiny_list)
            )
        else:
            message = _("No tienes ningún Pokémon shiny.")

        await ctx.send(message)
    
    @commands.command()
    async def trainercard(self, ctx):
        """Display your trainer card with various information."""
        user_conf = await self.user_is_global(ctx.author)
        result = await self.cursor.fetch_all(query=SELECT_POKEMON, values={"user_id": ctx.author.id})

        shiny_count = 0
        for data in result:
            pokemon = json.loads(data[0])
            if isinstance(pokemon, dict) and pokemon.get("variant") == "Shiny":
                shiny_count += 1

        # Fetching user's Pokédex count, Inciensos count, and current Pokémon index
        pokedex = await user_conf.pokeids()  # Dictionary of pokemon IDs and their counts
        pokedex_count = len(pokedex)  # Total number of different pokemons caught
        total_pokedex = len(self.pokemonlist)  
        incienso_count = await user_conf.incienso_count()
        current_pokemon_index = await user_conf.pokeid() - 1  # Adjusting index to 0-based

        # Fetching current Pokémon based on its index
        result = await self.cursor.fetch_all(query=SELECT_POKEMON, values={"user_id": ctx.author.id})
        pokemons = [json.loads(data[0]) for data in result]
        current_pokemon = pokemons[current_pokemon_index]["name"]["english"] if current_pokemon_index < len(pokemons) else "None"

        # Fetch badges
        badges = await user_conf.badges()

        # Creating the embed
        embed = discord.Embed(title=f"{ctx.author.display_name}'s Trainer Card", color=await self.bot.get_embed_color(ctx.channel))
        embed.set_thumbnail(url=ctx.author.avatar.url)  # Updated to use avatar.url
        embed.add_field(name="Pokédex", value=f"{pokedex_count}/{total_pokedex}", inline=False)
        embed.add_field(name="Shinies", value=str(shiny_count), inline=False)
        embed.add_field(name="Inciensos", value=str(incienso_count), inline=False)
        embed.add_field(name="Acompañante", value=current_pokemon, inline=False)
        # Formatting the badge field
        if badges:
            badge_field_value = f"{len(badges)}/18 ({', '.join(badges)})"
        else:
            badge_field_value = "0/18"

        # Adding badges to the embed
        embed.add_field(name="Medallas", value=badge_field_value, inline=False)

        # Sending the embed
        await ctx.send(embed=embed)