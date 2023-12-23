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
            ("Un fuerte aplauso. 👏 ¡Y felices fiestas! ⛄", 60.00),
            ("1 fondo navideño para el perfil.", 15.00),
            ("1 fondo personalizado para el perfil.", 1.00),
            ("1 incienso (Pokécord).", 8.00),
            ("10 inciensos (Pokécord).", 5.00),
            ("1 incienso shiny (Pokécord).", 3.00),
            ("1 incienso singular (Te permitirá invocar al Pokémon que escojas)", 5.00),
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
        try:
            user_gifts = await self.config.user(ctx.author).gifts()
            if user_gifts > 0:
                await self.config.user(ctx.author).gifts.set(user_gifts - 1)
                prize = await self.get_prize()
                await ctx.send(f"¡Enhorabuena! Te ha tocado {prize}.")
            else:
                await ctx.send("No tienes mystery gifts disponibles.")
        except Exception as e:
            await ctx.send("An error occurred: {}".format(e))
            # Here you can add more detailed logging if necessary

    async def get_prize(self):
        try:
            won_limited_prizes = await self.config.won_limited_prizes()
            filtered_prizes = []

            for prize_entry in self.prizes:
                # Check if prize_entry has the expected number of elements
                if len(prize_entry) < 2:
                    print(f"Invalid prize entry: {prize_entry}")
                    continue

                item, weight = prize_entry[:2]
                prize_key = prize_entry[2] if len(prize_entry) > 2 else None
                if not prize_key or won_limited_prizes.get(prize_key, 0) < self.limited_prizes_counts.get(prize_key, 0):
                    filtered_prizes.append((item, weight))

            total = sum(weight for item, weight in filtered_prizes)
            if total == 0:
                return "Lo siento, no hay más premios disponibles en este momento."

            r = random.uniform(0, total)
            upto = 0
            for prize_entry in filtered_prizes:
                item, weight = prize_entry
                upto += weight
                if upto >= r:
                    # Check if the prize is a limited prize and update accordingly
                    prize_key = None
                    for original_entry in self.prizes:
                        if item == original_entry[0]:
                            if len(original_entry) > 2:
                                prize_key = original_entry[2]
                                break

                    if prize_key:
                        won_limited_prizes[prize_key] = won_limited_prizes.get(prize_key, 0) + 1
                        await self.config.won_limited_prizes.set(won_limited_prizes)
                    return item

        except Exception as e:
            print(f"Error in get_prize: {e}")
            raise

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

    @commands.is_owner()
    @commands.command()
    async def checklimitedprizes(self, ctx):
        """Check the remaining quantity of each restricted gift."""
        try:
            won_limited_prizes = await self.config.won_limited_prizes()
            remaining_prizes = {}

            for prize_key, max_count in self.limited_prizes_counts.items():
                won_count = won_limited_prizes.get(prize_key, 0)
                remaining_prizes[prize_key] = max_count - won_count

            message = ["Remaining Restricted Gifts:"]
            for prize_key, remaining in remaining_prizes.items():
                message.append(f"{prize_key}: {remaining} left")

            await ctx.send("\n".join(message))
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            # You can add more detailed logging here if necessary