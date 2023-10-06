from discord.ext import commands
from discord import Embed
import random
from redbot.core import Config, commands

class ActionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

        default_guild = {
            "actions": {}
        }

        self.config.register_guild(**default_guild)

    @commands.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def actionset(self, ctx, action_name: str):
        """Creates a new action"""

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("Please provide the text for the action (use {user} for the user and {mention} for the mentioned user).")
        text_msg = await self.bot.wait_for('message', check=check)
        text = text_msg.content

        await ctx.send("Please provide image URLs for the action separated by spaces.")
        image_msg = await self.bot.wait_for('message', check=check)
        image_urls = image_msg.content.split()

        async with self.config.guild(ctx.guild).actions() as actions:
            actions[action_name] = {"text": text, "images": image_urls, "counts": {}}

        await ctx.send(f"'{action_name}' action has been created.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content
        action_name = content.split()[0][1:]  # Removing the prefix '!'

        actions = await self.config.guild(message.guild).actions()
        if action_name in actions:
            action = actions[action_name]

            mentioned_users = message.mentions
            if not mentioned_users:
                return
            mentioned_user = mentioned_users[0]

            count_key = f"{message.author.id}_{mentioned_user.id}"
            action["counts"][count_key] = action["counts"].get(count_key, 0) + 1

            embed = Embed(description=action["text"].format(user=message.author.display_name, mention=mentioned_user.display_name))
            embed.add_field(name="Count", value=f"{message.author.display_name} and {mentioned_user.display_name} have done this action {action['counts'][count_key]} times.")
            embed.set_image(url=random.choice(action["images"]))

            await message.channel.send(embed=embed)

            await self.config.guild(message.guild).set_raw('actions', action_name, value=action)

def setup(bot):
    bot.add_cog(ActionCog(bot))