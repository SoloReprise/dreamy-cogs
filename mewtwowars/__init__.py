from .mewtwowars import MewtwoWars

async def setup(bot):
    await bot.add_cog(MewtwoWars(bot))
