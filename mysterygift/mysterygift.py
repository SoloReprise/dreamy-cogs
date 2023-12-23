from redbot.core import commands, Config
import discord
import random

class MysteryGift(commands.Cog):
    """Mystery Gift Cog for Red Discord-Bot"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_user(gifts=0)
        self.config.register_global(won_limited_prizes={})
        self.prizes = [
            ("Un fuerte aplauso. 👏 ¡Y felices fiestas! ⛄", 50.00),
            ("1 fondo navideño para el perfil.", 10.00),
            ("1 fondo personalizado para el perfil.", 1.00),
            ("1 incienso (Pokécord).", 7.00),
            ("10 inciensos (Pokécord).", 3.00),
            ("1 incienso shiny (Pokécord).", 2.00),
            ("1 incienso singular (Te permitirá invocar al Pokémon que escojas)", 4.00),
            ("1 rol con color personalizado (limitado a 1 ganador)", 1.00, "custom_role"),
            ("Un mes de Discord Nitro Basic (limitado a 1 ganador)", 1.00, "nitro_basic"),
            ("Un mes de Discord Nitro (limitado a 1 ganador)", 1.00, "nitro"),
            ("Shiny Zeraora (limitado a 1 ganador)", 1.50, "shiny_zeraora"),
            ("Shiny Eternatus (limitado a 3 ganadores)", 1.50, "shiny_eternatus"),
            ("Trío de shiny starters Paldea (limitado a 1 ganador)", 2.00, "shiny_starters"),
            ("Attackers Shiny Pack (limitado a 1 ganador)", 3.00, "attackers_pack"),
            ("Defenders Shiny Pack (limitado a 1 ganador)", 3.00, "defenders_pack"),
            ("Supporters Shiny Pack (limitado a 1 ganador)", 3.00, "supporters_pack"),
            ("All-Rounders Shiny Pack (limitado a 1 ganador)", 3.00, "allrounders_pack"),
            ("Speedsters Shiny Pack (limitado a 1 ganador)", 3.00, "speedsters_pack"),
        ]
        self.limited_prizes_counts = {
            "custom_role": 1,
            "nitro_basic": 1,
            "nitro": 1,
            "shiny_zeraora": 1,
            "shiny_eternatus": 3,
            "shiny_starters": 1,
            "attackers_pack": 1,
            "defenders_pack": 1,
            "supporters_pack": 1,
            "allrounders_pack": 1,
            "speedsters_pack": 1
        }

    @commands.command(aliases=['mg'])
    async def mysterygift(self, ctx):
        """Use a mystery gift to receive a prize."""
        user_gifts = await self.config.user(ctx.author).gifts()
        if user_gifts > 0:
            await self.config.user(ctx.author).gifts.set(user_gifts - 1)
            prize = await self.get_prize()
            await ctx.send(f"¡Enhorabuena! Te ha tocado {prize}.")
        else:
            await ctx.send("No tienes mystery gifts disponibles.")

    async def get_prize(self):
        won_limited_prizes = await self.config.won_limited_prizes()
        filtered_prizes = [
            (item, weight) if len(prize) == 2 or won_limited_prizes.get(prize[2], 0) < self.limited_prizes_counts.get(prize[2], 0)
            else (item, 0) for item, weight, *prize in self.prizes
        ]
        
        # Check if total weight is not zero to avoid division by zero error
        total = sum(weight for item, weight in filtered_prizes)
        if total == 0:
            return "Lo siento, no hay más premios disponibles en este momento."
        
        r = random.uniform(0, total)
        upto = 0
        for item, weight, *prize in filtered_prizes:
            if upto + weight >= r:
                if prize:
                    prize_key = prize[0]
                    won_limited_prizes[prize_key] = won_limited_prizes.get(prize_key, 0) + 1
                    await self.config.won_limited_prizes.set(won_limited_prizes)
                return item
            upto += weight

    @commands.is_owner()
    @commands.command()
    async def addgift(self, ctx, user: discord.Member, amount: int):
        """Add mystery gifts to a user."""
        current_gifts = await self.config.user(user).gifts()
        await self.config.user(user).gifts.set(current_gifts + amount)
        await ctx.send(f"Added {amount} mystery gifts to {user.display_name}.")

    @commands.is_owner()
    @commands.command()
    async def removegift(self, ctx, user: discord.Member, amount: int):
        """Remove mystery gifts from a user."""
        current_gifts = await self.config.user(user).gifts()
        new_amount = max(current_gifts - amount, 0)
        await self.config.user(user).gifts.set(new_amount)
        await ctx.send(f"Removed {amount} mystery gifts from {user.display_name}.")

    @commands.is_owner()
    @commands.command()
    async def resetlimitedprizes(self, ctx):
        """Reset the count of all limited prizes."""
        await self.config.won_limited_prizes.clear()
        await ctx.send("All limited prizes have been reset and are available again.")

    @commands.is_owner()
    @commands.command()
    async def checkgifts(self, ctx):
        """Check the number of gifts given to each user."""
        all_users = await self.config.all_users()

        if not all_users:
            await ctx.send("No gifts have been given yet.")
            return

        message = ["Gifts given:"]
        for user_id, data in all_users.items():
            member = ctx.guild.get_member(user_id)
            if member:
                message.append(f"{member.display_name}: {data['gifts']} gifts")
            else:
                message.append(f"User ID {user_id}: {data['gifts']} gifts")

        await ctx.send("\n".join(message))
