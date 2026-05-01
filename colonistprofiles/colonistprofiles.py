import random
from urllib.parse import quote

import discord
from redbot.core import app_commands, commands


class ColonistProfiles(commands.Cog):
    """Generate mocked Colonist.io profile embeds for testing."""

    PROFILE_COLOR = discord.Color(0x177FDE)
    PROFILE_IMAGE_URLS = (
        "https://images.weserv.nl/?url=cdn.colonist.io/dist/assets/icon_mummy.7990e9ab2e51f4c57a1b.svg&output=png",
        "https://images.weserv.nl/?url=cdn.colonist.io/dist/assets/icon_cactus.2f57f6570b80f25c42f2.svg&output=png",
        "https://images.weserv.nl/?url=cdn.colonist.io/dist/assets/icon_player.823fcffb830b912c3bc5.svg&output=png",
        "https://images.weserv.nl/?url=cdn.colonist.io/dist/assets/icon_founder.c5030be56a7e8b60a995.svg&output=png",
    )

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.hybrid_command(
        name="profile",
        aliases=["colonistprofile", "colonist"],
        description="Show a mocked Colonist.io profile.",
    )
    @app_commands.describe(username="Colonist.io username to look up.")
    async def profile(self, ctx: commands.Context, username: str):
        """Show a mocked Colonist.io profile for testing."""

        username = username.strip()
        if not username:
            await ctx.send("Please tell me which Colonist.io username to look up.")
            return

        profile_url = f"https://colonist.io/profile/{quote(username)}"
        safe_username = discord.utils.escape_markdown(username)

        embed = discord.Embed(
            title=safe_username,
            description=(
                "You're looking at Colonist.io profile of "
                f"[{safe_username}]({profile_url}). Here's what we've got!"
            ),
            color=self.PROFILE_COLOR,
            url=profile_url,
        )

        information = "\n".join(
            (
                f"\U0001f48e **Premium Member:** {self._random_yes_no()}",
                f"\U0001f3a5 **Content Creator:** {self._random_yes_no()}",
                f"\U0001f3f0 **Colonist Guild:** {self._random_yes_no()}",
            )
        )
        overview = "\n".join(
            (
                f"\U0001f3b2 **Total games:** {random.randint(10, 900)}",
                f"\U0001f3c6 **Win %:** {random.randint(0, 100)}%",
                f"\U00002b50 **Karma:** {random.randint(0, 20)}/20",
                f"\U0001f4c8 **Point/Game:** {random.uniform(5.55, 9.70):.2f}",
                f"\U0001f4af **Points:** {random.randint(20, 800)}",
            )
        )

        embed.add_field(
            name="\U0001f4d6 Information",
            value=f"{information}\n\n\U0001f4ca **Overview**\n{overview}",
            inline=False,
        )
        embed.set_thumbnail(url=random.choice(self.PROFILE_IMAGE_URLS))

        await ctx.send(embed=embed)

    @staticmethod
    def _random_yes_no():
        return random.choice(("Yes", "No"))
