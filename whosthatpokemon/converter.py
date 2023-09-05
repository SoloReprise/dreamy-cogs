from random import randint
from redbot.core import commands

class Generation(commands.Converter):
    """
    A converter for the RedBot that converts Pokémon generation strings to 
    a random number within that generation's range of Pokémon.
    """
    
    GEN_MAP = {
        "gen1": (1, 151),
        "gen2": (152, 251),
        "gen3": (252, 386),
        "gen4": (387, 493),
        "gen5": (494, 649),
        "gen6": (650, 721),
        "gen7": (722, 809),
        "gen8": (810, 898),
        "arceus": (899, 905),
        "gen9": (906, 1010),
    }

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        argument = argument.lower()
        
        if argument not in self.GEN_MAP:
            ctx.command.reset_cooldown(ctx)
            raise commands.BadArgument(
                "Only `gen1` to `gen10`, and `arceus` values are allowed."
            )
        
        start, end = self.GEN_MAP[argument]
        return randint(start, end)