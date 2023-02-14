from __future__ import annotations

import datetime
from typing import Callable, TYPE_CHECKING, Optional

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


class CooldownAlreadyExists(BaseCooldownException):
    """A Cooldown with this ID already exists."""


class UnknownBucket(BaseCooldownException):
    """Failed to process the bucket."""


class NoRegisteredCooldowns(BaseCooldownException):
    """
    This `Callable` has no attached cooldown's.
    """

    def __init__(self):
        super().__init__(self.__doc__)


class CallableOnCooldown(BaseCooldownException):
    """
    This `Callable` is currently on cooldown.

    Attributes
    ==========
    func: Callable
        The `Callable` which is currently rate-limited
    cooldown: Cooldown
        The :class:`Cooldown` which applies to the current cooldown
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
        """How many seconds before you can retry the `Callable`

        Returns
        -------
        float
            How many seconds before you can retry this

            .. note::

                This will be 0 if you can retry now
        """
        now = datetime.datetime.utcnow()
        if now > self.resets_at:
            return 0

        gap: datetime.timedelta = self.resets_at - now
        return gap.total_seconds()
