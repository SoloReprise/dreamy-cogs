from abc import ABC

from redbot.core import Config, commands
from redbot.core.bot import Red


class MixinMeta(ABC):
    """
    Typehinting stuff.
    """

    def __init__(self, *args):
        self.config: Config
        self.bot: Red


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """More typehinting stuff."""
