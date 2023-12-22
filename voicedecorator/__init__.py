from .voicedecorators import VoiceDecorators

async def setup(bot):
    await bot.add_cog(VoiceDecorators(bot))
