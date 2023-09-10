from .randombuild import RandomBuild


async def setup(bot):
    await bot.add_cog(RandomBuild(bot))
