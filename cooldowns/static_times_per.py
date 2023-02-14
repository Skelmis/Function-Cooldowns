from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List

from .cooldown_times_per import CooldownTimesPer
from .exceptions import CallableOnCooldown

if TYPE_CHECKING:
    from cooldowns import Cooldown


class StaticTimesPer(CooldownTimesPer):
    """A cooldown which implements a set amount of cooldown reset times."""

    def __init__(
        self,
        limit: int,
        reset_times: List[datetime.time],
        _cooldown: Cooldown,
    ) -> None:
        """

        Parameters
        ----------
        limit: int
            How many items are allowed
        reset_times: List[datetime.time]
            A list of the possible times in the day
            to reset cooldowns at
        _cooldown: Cooldown
            A backref to the parent cooldown manager.

        Notes
        -----
        This is an internal object.
        You do not need to construct it yourself.
        """
        super().__init__(limit, 0, _cooldown)
        self._reset_times = reset_times

    def __repr__(self):
        return f"<StaticTimesPer(limit={self.limit}, current={self.current}, resets_at=[...])>"

    @staticmethod
    def next_datetime(
        current: datetime.datetime, time: datetime.time
    ) -> datetime.datetime:
        repl = current.replace(
            hour=time.hour,
            minute=time.minute,
            second=time.second,
            microsecond=time.microsecond,
        )
        while repl <= current:
            repl = repl + datetime.timedelta(days=1)

        return repl

    def get_next_reset(self, now: datetime.datetime) -> datetime.datetime:
        """Fetches the next possible reset."""
        possible_options = [self.next_datetime(now, t) for t in self._reset_times]
        return min(possible_options)

    async def __aenter__(self) -> StaticTimesPer:
        if self.current == 0:
            raise CallableOnCooldown(
                self._cooldown.func, self._cooldown, self.next_reset
            )

        self.current -= 1

        now = datetime.datetime.utcnow()
        reset: datetime.datetime = self.get_next_reset(now)

        self._next_reset.put_nowait(reset)
        self.loop.call_later((reset - now).total_seconds(), self._reset_invoke)

        return self
