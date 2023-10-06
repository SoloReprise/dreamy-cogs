from .nekoactions import actions

async def setup(bot):
    await bot.add_cog(actions(bot))