from .unitecog import UniteCog
from unidecode import unidecode

async def setup(bot):
    await bot.add_cog(UniteCog(bot))