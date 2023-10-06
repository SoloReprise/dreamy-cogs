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

    async def get_input(self, ctx, question: str):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send(question)
        msg = await self.bot.wait_for('message', check=check)
        return msg.content

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def actionset(self, ctx):
        """Manage actions."""
        pass

    @actionset.command(name="create")
    async def actionset_create(self, ctx, action_name: str):
        """Creates a new action"""

        text = await self.get_input(ctx, "Please provide the text for the action (use {user} for the user and {mention} for the mentioned user).")
        image_urls = await self.get_input(ctx, "Please provide image URLs for the action separated by spaces.")
        count_text = await self.get_input(ctx, "Please provide the text for counting action occurrences (use {user}, {mention}, and {count} as placeholders).")

        async with self.config.guild(ctx.guild).actions() as actions:
            actions[action_name] = {"text": text, "images": image_urls.split(), "counts": {}, "count_text": count_text}

        await ctx.send(f"'{action_name}' action has been created.")

    @actionset.command(name="edit")
    async def actionset_edit(self, ctx, action_name: str):
        """Edit an existing action"""

        async with self.config.guild(ctx.guild).actions() as actions:
            if action_name not in actions:
                await ctx.send(f"No action named '{action_name}' found.")
                return
            
            # Example: Update text or image URLs or count text
            new_text = await self.get_input(ctx, f"Current text for '{action_name}' is: {actions[action_name]['text']}\nProvide new text or type 'skip' to keep the current.")
            if new_text.lower() != 'skip':
                actions[action_name]['text'] = new_text

            new_image_urls = await self.get_input(ctx, f"Current image URLs for '{action_name}' are: {' '.join(actions[action_name]['images'])}\nProvide new image URLs separated by spaces or type 'skip' to keep the current.")
            if new_image_urls.lower() != 'skip':
                actions[action_name]['images'] = new_image_urls.split()

            new_count_text = await self.get_input(ctx, f"Current count text for '{action_name}' is: {actions[action_name]['count_text']}\nProvide new count text or type 'skip' to keep the current.")
            if new_count_text.lower() != 'skip':
                actions[action_name]['count_text'] = new_count_text

            await ctx.send(f"'{action_name}' action has been updated.")

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

            count_key = f"{mentioned_user.id}"
            action["counts"][count_key] = action["counts"].get(count_key, 0) + 1

            text = action["text"].format(user=message.author.display_name, mention=mentioned_user.display_name)
            count_text = action["count_text"].format(user=message.author.display_name, mention=mentioned_user.display_name, count=action["counts"][count_key])
            
            embed = Embed(description=f"{text}\n{count_text}")
            embed.set_image(url=random.choice(action["images"]))

            await message.channel.send(embed=embed)

            await self.config.guild(message.guild).set_raw('actions', action_name, value=action)

def setup(bot):
    bot.add_cog(ActionCog(bot))
