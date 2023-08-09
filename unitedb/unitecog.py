import discord
from redbot.core import commands
import sqlite3
import asyncio
import unicodedata
from unidecode import unidecode

unitetext = f"""
Placeholder
"""
excluded_keywords = ["Absol", "Aegislash", "Azumarill", "Blastoise", "Blaziken", "Blissey", "Buzzwole", "Chandelure", "Charizard", "Cinderace", 
                  "Clefable", "Comfey", "Cramorant", "Decidueye", "Delphox", "Dodrio", "Dragapult", "Dragonite", "Duraludon", "Eldegoss", "Espeon", 
                  "Garchomp", "Gardevoir", "Gengar", "Glaceon", "Goodra", "Greedent", "Greninja", "Hoopa", "Inteleon", "Lapras", "Leafeon", "Lucario", 
                  "Machamp", "Mamoswine", "Meowscarada", "Metagross", "Mew", "Mewtwo X", "Mewtwo Y", "Mimikyu", "Mr Mime", "Ninetales", "Pikachu", 
                  "Sableye", "Scizor", "Scyther", "Slowbro", "Snorlax", "Sylveon", "Talonflame", "Trevenant", "Tsareena", "Tyranitar", "Umbreon", 
                  "Urshifu", "Venusaur", "Wigglytuff","Zacian", "Zeraora", "Zoroark"]  # Add other excluded words here

unitedbtext = f"""
Placeholder
"""


class UniteCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def connect(self):
        try:
            conn = sqlite3.connect(f"/home/unitedlegacy/.local/share/Red-DiscordBot/data/Spribotito/cogs/CogManager/cogs/unitedb/callers.db")
            curs = conn.cursor()
            run = "CREATE TABLE IF NOT EXISTS callers (name varchar, category varchar, text varchar, image varchar);"
            curs.execute(run)
            conn.commit()
            return conn, curs
        except Exception as exc:
            print(exc)
            return None
        

    @commands.command()
    async def unite(self, ctx, *, args=None):
        """
        Busca por pokemon/emblem/move/hold-item/battle-item
        """
        cats = ["pokemon", "emblem", "move", "hold-item", "battle-item"]

        if args is not None:
            if args.lower().startswith("help"):
                emb = discord.Embed(title="Unite Help", description=unitetext, colour=discord.Colour.blue())
                await ctx.reply(embed=emb)
                return

        try:
            parts = args.split(" ")
            category = parts[0].lower()
            name_keywords = " ".join(parts[1:])
        except Exception as exc:
            emb = discord.Embed(title="Unite Help", description=unitetext, colour=discord.Colour.blue())
            await ctx.reply(embed=emb)
            return

        if category not in cats:
            await ctx.reply("Invalid category")
            return

        result = UniteCog.connect(self)
        if result is None:
            return

        conn, curs = result
        query = f"""SELECT * FROM callers WHERE category='{category}'"""
        curs.execute(query)
        all_records = curs.fetchall()
        conn.close()

        normalized_keywords = unidecode(name_keywords).lower()

        matching_records = []

        for record in all_records:
            record_name = record[0]
            normalized_record_name = unidecode(record_name).lower()
            if normalized_keywords == normalized_record_name:
                matching_records = [record]
                break
            elif normalized_keywords in normalized_record_name:
                matching_records.append(record)

        if len(matching_records) == 0:
            await ctx.reply("A caller with this name and category does not exist.")
            return

        name, category, text, image = matching_records[0]
        name = name.replace("''", "'")

        # Construct the embed title without excluded keywords (if they exist)
        embed_title = name
        for excluded_keyword in excluded_keywords:
            if excluded_keyword in name_keywords:
                embed_title = embed_title.replace(excluded_keyword, "")

        emb = discord.Embed(title=embed_title, description=text, colour=discord.Colour.green())
        emb.set_thumbnail(url=image)
        await ctx.reply(embed=emb)
        return

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def unitedb(self, ctx, action = None, *, args = None):
        if action is None:
            emb = discord.Embed(title="UniteDB Help", description=unitedbtext, colour=discord.Colour.blue())
            await ctx.reply(embed=emb)
            return
        
        action = action.lower()
        cats = ["pokemon", "emblem", "move", "hold-item", "battle-item"]

        def checker(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            if action == "create":
                try:
                    parts = args.split(" ")
                    category = parts[0].lower()
                    name = ""
                    for p in parts[1:]:
                        if name == "":
                            name = name + p
                        else:
                            name = name + f" {p}"
                except Exception as exc:
                    emb = discord.Embed(title="UniteDB Help", description=unitedbtext, colour=discord.Colour.blue())
                    await ctx.reply(embed=emb)
                    return
                
                if category not in cats:
                    await ctx.reply("Invalid category")
                    return
                
                await ctx.reply("Please reply with the caller text")
                
                try:
                    result = await self.bot.wait_for("message", check=checker, timeout=300)
                except asyncio.TimeoutError:
                    await ctx.send("Creating of caller was cancelled, please try again.")
                    return
                
                text = result.content
                if len(text) == 0:
                    await result.reply("Invalid text for caller, cancelled")
                    return

                result1 = UniteCog.connect(self)
                if result1 is None:
                    return
                
                name = name.replace("'", "''")
                
                conn, curs = result1
                query = f"""SELECT * FROM callers WHERE name='{name}' COLLATE NOCASE AND category='{category}'"""
                curs.execute(query)
                records = curs.fetchall()
                
                if len(records) > 0:
                    await result.reply("A caller with this name and category already exists.")
                    return

                text = text.replace("'", "''")

                image = None
                for i in ctx.message.attachments:
                    if ".png" or ".jpg" or ".jpeg" or ".webp" in i.proxy_url:
                        image = i.proxy_url
                        break

                if image is None:
                    image = ""
                
                query = f"""INSERT INTO callers(name, category, text, image) VALUES('{name}', '{category}', '{text}', '{image}')"""
                curs.execute(query)
                conn.commit()
                conn.close()

                name = name.replace("''", "'")
                text = text.replace("''", "'")

                emb = discord.Embed(title="Caller Created", colour=discord.Colour.green())
                emb.set_thumbnail(url=image)
                emb.add_field(name="Name", value=name, inline=False)
                emb.add_field(name="Category", value=category.capitalize(), inline=False)
                emb.add_field(name="Reply Text", value=text, inline=False)
                await result.reply(embed=emb)
                return
            
            elif action == "edit":
                try:
                    parts = args.split(" ")
                    category = parts[0].lower()
                    name = ""
                    for p in parts[1:]:
                        if name == "":
                            name = name + p
                        else:
                            name = name + f" {p}"
                except Exception as exc:
                    emb = discord.Embed(title="UniteDB Help", description=unitedbtext, colour=discord.Colour.blue())
                    await ctx.reply(embed=emb)
                    return
                
                if category not in cats:
                    await ctx.reply("Invalid category")
                    return
                
                result = UniteCog.connect(self)
                if result is None:
                    return
                
                name = name.replace("'", "''")
                
                conn, curs = result
                query = f"""SELECT * FROM callers WHERE name='{name}' COLLATE NOCASE AND category='{category}'"""
                curs.execute(query)
                records = curs.fetchall()

                if len(records) == 0:
                    await ctx.reply(f"No caller with this name and category exists")
                    return
                
                await ctx.reply("Please reply with the new caller text")
                
                try:
                    result = await self.bot.wait_for("message", check=checker, timeout=300)
                except asyncio.TimeoutError:
                    await ctx.send("Editing of caller was cancelled, please try again.")
                    return
                
                text = result.content
                if len(text) == 0:
                    await result.reply("Invalid text for caller, cancelled")
                    return
                
                text = text.replace("'", "''")
                
                query = f"""UPDATE callers SET (text) = ('{text}') WHERE name='{name}' COLLATE NOCASE AND category='{category}'"""
                curs.execute(query)
                conn.commit()
                conn.close()

                name = name.replace("''", "'")
                text = text.replace("''", "'")

                emb = discord.Embed(title="Caller Edited", colour=discord.Colour.green())
                emb.add_field(name="Name", value=name, inline=False)
                emb.add_field(name="Category", value=category.capitalize(), inline=False)
                emb.add_field(name="Reply Text", value=text, inline=False)
                await result.reply(embed=emb)
                return
            
            elif action == "delete":
                try:
                    parts = args.split(" ")
                    category = parts[0].lower()
                    name = ""
                    for p in parts[1:]:
                        if name == "":
                            name = name + p
                        else:
                            name = name + f" {p}"
                except Exception as exc:
                    emb = discord.Embed(title="UniteDB Help", description=unitedbtext, colour=discord.Colour.blue())
                    await ctx.reply(embed=emb)
                    return
                
                if category not in cats:
                    await ctx.reply("Invalid category")
                    return
                
                result = UniteCog.connect(self)
                if result is None:
                    return
                
                name = name.replace("'", "''")
                
                conn, curs = result
                query = f"""SELECT * FROM callers WHERE name='{name}' COLLATE NOCASE AND category='{category}'"""
                curs.execute(query)
                records = curs.fetchall()

                if len(records) == 0:
                    await ctx.reply(f"No caller with this name and category exists")
                    return
                
                text = records[0][2]
                
                query = f"""DELETE FROM callers WHERE name='{name}' COLLATE NOCASE AND category='{category}'"""
                curs.execute(query)
                conn.commit()
                conn.close()

                name = name.replace("''", "'")

                emb = discord.Embed(title="Caller Deleted", colour=discord.Colour.red())
                emb.add_field(name="Name", value=name, inline=False)
                emb.add_field(name="Category", value=category.capitalize(), inline=False)
                emb.add_field(name="Reply Text", value=text, inline=False)
                await ctx.reply(embed=emb)
                return
            
            else:
                emb = discord.Embed(title="UniteDB Help", description=unitedbtext, colour=discord.Colour.blue())
                await ctx.reply(embed=emb)
                return
        except Exception as exc:
            print(exc)