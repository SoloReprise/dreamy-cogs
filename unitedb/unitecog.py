import discord
from redbot.core import commands
import sqlite3
import asyncio

unitetext = "Placeholder"
unitedbtext = "Placeholder"

class UniteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def connect(self):
        try:
            conn = sqlite3.connect(
                "/home/unitedlegacy/.local/share/Red-DiscordBot/data/Spribotito/cogs/CogManager/cogs/unitedb/callers.db"
            )
            curs = conn.cursor()
            run = "CREATE TABLE IF NOT EXISTS callers (name varchar PRIMARY KEY, category varchar, text varchar, image varchar);"
            curs.execute(run)
            conn.commit()
            return conn, curs
        except Exception as exc:
            print(exc)
            return None

    def fetch_caller(self, category, name):
        conn, curs = self.connect()
        if conn is None:
            return None

        name = name.replace("'", "''")
        query = f"""SELECT * FROM callers WHERE name=? COLLATE NOCASE AND category=?"""
        curs.execute(query, (name, category))
        records = curs.fetchall()
        conn.close()

        return records

    @commands.command()
    async def unite(self, ctx, *, args=None):
        cats = ["pokemon", "emblem", "move", "hold-item", "battle-item"]

        if args is not None:
            if args.lower().startswith("help"):
                emb = discord.Embed(
                    title="Unite Help", description=unitetext, colour=discord.Colour.blue()
                )
                await ctx.reply(embed=emb)
                return

        try:
            parts = args.split(" ")
            category = parts[0].lower()
            name = " ".join(parts[1:])
        except Exception as exc:
            emb = discord.Embed(
                title="Unite Help", description=unitetext, colour=discord.Colour.blue()
            )
            await ctx.reply(embed=emb)
            return

        if category not in cats:
            await ctx.reply("Invalid category")
            return

        records = self.fetch_caller(category, name)
        if not records:
            await ctx.reply("A caller with this name and category does not exist.")
            return

        name, category, text, image = records[0]
        name = name.replace("''", "'")

        emb = discord.Embed(description=text, colour=discord.Colour.green())
        emb.set_thumbnail(url=image)
        await ctx.reply(embed=emb)

    @commands.command()
    @commands.has_guild_permissions(administrator=True)
    async def unitedb(self, ctx, action=None, *, args=None):
        if action is None:
            emb = discord.Embed(
                title="UniteDB Help", description=unitedbtext, colour=discord.Colour.blue()
            )
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
                    name = " ".join(parts[1:])
                except Exception as exc:
                    emb = discord.Embed(
                        title="UniteDB Help",
                        description=unitedbtext,
                        colour=discord.Colour.blue(),
                    )
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
                if not text:
                    await result.reply("Invalid text for caller, cancelled")
                    return

                result1 = self.fetch_caller(category, name)
                if result1:
                    await result.reply("A caller with this name and category already exists.")
                    return

                text = text.replace("'", "''")

                image = next(
                    (i.proxy_url for i in ctx.message.attachments if i.proxy_url.endswith((".png", ".jpg", ".jpeg", ".webp"))),
                    "",
                )

                conn, curs = self.connect()
                if not conn:
                    return

                try:
                    query = f"""INSERT INTO callers (name, category, text, image) VALUES (?, ?, ?, ?)"""
                    curs.execute(query, (name, category, text, image))
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

                except sqlite3.IntegrityError:
                    await result.reply("A caller with this name and category already exists.")
                finally:
                    conn.close()

            elif action == "edit":
                try:
                    parts = args.split(" ")
                    category = parts[0].lower()
                    name = " ".join(parts[1:])
                except Exception as exc:
                    emb = discord.Embed(
                        title="UniteDB Help",
                        description=unitedbtext,
                        colour=discord.Colour.blue(),
                    )
                    await ctx.reply(embed=emb)
                    return

                if category not in cats:
                    await ctx.reply("Invalid category")
                    return

                records = self.fetch_caller(category, name)
                if not records:
                    await ctx.reply(f"No caller with this name and category exists")
                    return

                await ctx.reply("Please reply with the new caller text")

                try:
                    result = await self.bot.wait_for("message", check=checker, timeout=300)
                except asyncio.TimeoutError:
                    await ctx.send("Editing of caller was cancelled, please try again.")
                    return

                text = result.content
                if not text:
                    await result.reply("Invalid text for caller, cancelled")
                    return

                text = text.replace("'", "''")

                conn, curs = self.connect()
                if not conn:
                    return

                try:
                    query = f"""UPDATE callers SET text=? WHERE name=? COLLATE NOCASE AND category=?"""
                    curs.execute(query, (text, name, category))
                    conn.commit()
                    conn.close()

                    name = name.replace("''", "'")
                    text = text.replace("''", "'")

                    emb = discord.Embed(title="Caller Edited", colour=discord.Colour.green())
                    emb.add_field(name="Name", value=name, inline=False)
                    emb.add_field(name="Category", value=category.capitalize(), inline=False)
                    emb.add_field(name="Reply Text", value=text, inline=False)
                    await result.reply(embed=emb)

                except sqlite3.IntegrityError:
                    await result.reply("A caller with this name and category already exists.")
                finally:
                    conn.close()

            elif action == "delete":
                try:
                    parts = args.split(" ")
                    category = parts[0].lower()
                    name = " ".join(parts[1:])
                except Exception as exc:
                    emb = discord.Embed(
                        title="UniteDB Help",
                        description=unitedbtext,
                        colour=discord.Colour.blue(),
                    )
                    await ctx.reply(embed=emb)
                    return

                if category not in cats:
                    await ctx.reply("Invalid category")
                    return

                records = self.fetch_caller(category, name)
                if not records:
                    await ctx.reply(f"No caller with this name and category exists")
                    return

                text = records[0][2]

                conn, curs = self.connect()
                if not conn:
                    return

                try:
                    query = f"""DELETE FROM callers WHERE name=? COLLATE NOCASE AND category=?"""
                    curs.execute(query, (name, category))
                    conn.commit()
                    conn.close()

                    name = name.replace("''", "'")

                    emb = discord.Embed(title="Caller Deleted", colour=discord.Colour.red())
                    emb.add_field(name="Name", value=name, inline=False)
                    emb.add_field(name="Category", value=category.capitalize(), inline=False)
                    emb.add_field(name="Reply Text", value=text, inline=False)
                    await ctx.reply(embed=emb)

                except Exception as exc:
                    print(exc)
                finally:
                    conn.close()

            else:
                emb = discord.Embed(
                    title="UniteDB Help", description=unitedbtext, colour=discord.Colour.blue()
                )
                await ctx.reply(embed=emb)

        except Exception as exc:
            print(exc)
