from __future__ import annotations
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from cooldowns import Cooldown


class BaseCooldownException(Exception):
    """A base exception handler."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = self.__doc__

    def __str__(self):
        return self.message


class InteractionBucketFailure(BaseCooldownException):
    """
    You attempted to apply an Interaction based cooldown
    to a Callable which does not take Interaction as the
    first parameter.
    """


class CallableOnCooldown(BaseCooldownException):
    """
    This :type:`Callable` is currently on cooldown.

    Attributes
    ==========
    func: Callable
        The :type:`Callable` which is currently rate-limited
    cooldown: Cooldown
        The :class:`Cooldown` which applies to the current cooldown
    retry_after: float
        How many seconds before you can retry the :type:`Callable`
    """

    def __init__(
        self,
        func: Callable,
        cooldown: Cooldown,
        retry_after: float,
    ) -> None:
        self.func: Callable = func
        self.cooldown: Cooldown = cooldown
        self.retry_after: float = retry_after
