from __future__ import annotations

import datetime
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


class NonExistent(BaseCooldownException):
    """There doesnt already exist a bucket for this."""


class NoRegisteredCooldowns(BaseCooldownException):
    """
    This :type:`Callable` has no attached cooldown's.
    """

    def __init__(self):
        super().__init__(self.__doc__)


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
    resets_at: datetime.datetime
        The exact datetime this cooldown resets.
    """

    def __init__(
        self,
        func: Callable,
        cooldown: Cooldown,
        resets_at: datetime.datetime,
    ) -> None:
        self.func: Callable = func
        self.cooldown: Cooldown = cooldown
        self.resets_at: datetime.datetime = resets_at
        super().__init__(
            "This function is being rate-limited. "
            f"Please try again in {self.retry_after} seconds."
        )

    @property
    def retry_after(self) -> float:
        now = datetime.datetime.utcnow()
        gap: datetime.timedelta = now - self.resets_at
        return gap.seconds
