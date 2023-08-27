from .partiditas import Partiditas


async def setup(bot):
    await bot.add_cog(Partiditas(bot))