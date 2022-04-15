from enum import Enum

from cooldowns.exceptions import UnknownBucket


class SlashBucket(Enum):
    """
    A collection of generic cooldown bucket's for usage
    with nextcord slash commands which take ``Interaction``

    Attributes
    ==========
    author
        Rate-limits the command per person.
    guild
        Rate-limits the command per guild.
    channel
        Rate-limits the command per channel
    command
        Rate-limits the entire command as one.
    """

    author = 0
    guild = 1
    channel = 2
    command = 3

    def process(self, *args, **kwargs):
        from nextcord import Interaction

        # Delayed import to not care if not using nextcord

        # Handle cogs
        inter: Interaction = args[0] if isinstance(args[0], Interaction) else args[1]
        if self is SlashBucket.author:
            return inter.user.id

        elif self is SlashBucket.guild:
            return inter.guild_id

        elif self is SlashBucket.channel:
            return inter.channel_id

        elif self is SlashBucket.command:
            return inter.application_id

        raise UnknownBucket
