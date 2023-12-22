from redbot.core import commands, Config
import discord

from redbot.core import commands
import discord

class VoiceDecorators(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        # Check if it's a voice channel and if the name change is relevant
        if isinstance(after, discord.VoiceChannel) and not after.name.startswith("◇║"):
            new_name = f"◇║{after.name}"
            await after.edit(name=new_name)

def setup(bot):
    bot.add_cog(VoiceRename(bot))

def teardown(bot):
    bot.remove_cog("VoiceDecorators")
