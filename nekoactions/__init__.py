from .nekoactions import Actions

async def setup(bot):
    await bot.add_cog(Actions(bot))