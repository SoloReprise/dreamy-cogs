from .nekoactions import ActionCog

async def setup(bot):
    await bot.add_cog(ActionCog(bot))