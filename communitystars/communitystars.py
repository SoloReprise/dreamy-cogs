from redbot.core import commands, Config
import discord

class CommunityStars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1235567890)
        self.config.register_global(reactions={})

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "🌟" and not reaction.message.pinned:
            channel = reaction.message.channel
            message_id = reaction.message.id

            reactions = await self.config.reactions()
            if message_id not in reactions:
                reactions[message_id] = []

            if user.id not in reactions[message_id]:
                reactions[message_id].append(user.id)
                await self.config.reactions.set(reactions)

                if len(reactions[message_id]) >= 1:
                    await reaction.message.pin()
