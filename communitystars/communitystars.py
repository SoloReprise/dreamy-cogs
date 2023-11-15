from redbot.core import commands, Config
import discord

class CommunityStars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(reactions={})

        # Define the categories and their exceptions
        self.excluded_categories = {
            1127625556247203860: [1139134195524960276],  # Allow this channel in the category
            1127784491625234432: [1127798424864034846]  # Allow this channel in the category
        }

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        channel = reaction.message.channel
        category_id = channel.category_id
        channel_id = channel.id

        # Check if the channel's category is not in the excluded list or it's an allowed channel
        if category_id not in self.excluded_categories or channel_id in self.excluded_categories.get(category_id, []):
            # Check if the reaction is a star and the message is not already pinned
            if str(reaction.emoji) == "⭐" and not reaction.message.pinned:
                message_id = reaction.message.id

                # Load or initialize the reaction count for the message
                reactions = await self.config.reactions()
                if message_id not in reactions:
                    reactions[message_id] = []

                # Add the user to the list of reactors if not already there
                if user.id not in reactions[message_id]:
                    reactions[message_id].append(user.id)
                    await self.config.reactions.set(reactions)

                    # If 5 different users have reacted, pin the message
                    if len(reactions[message_id]) >= 1:
                        await reaction.message.pin()
