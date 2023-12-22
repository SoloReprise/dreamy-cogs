from .voicedecorator import VoiceDecorator

async def setup(bot):
    await bot.add_cog(VoiceDecorator(bot))
