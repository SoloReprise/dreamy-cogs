from .unitecog import UniteCog

async def setup(bot):
    await bot.add_cog(UniteCog(bot))