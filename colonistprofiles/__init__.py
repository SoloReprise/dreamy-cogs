from .colonistprofiles import ColonistProfiles


async def setup(bot):
    await bot.add_cog(ColonistProfiles(bot))
