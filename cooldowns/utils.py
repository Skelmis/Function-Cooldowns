from __future__ import annotations

import asyncio
from typing import Callable, Any, Coroutine, List, TYPE_CHECKING

from cooldowns.exceptions import NoRegisteredCooldowns

if TYPE_CHECKING:
    from cooldowns import Cooldown

MaybeCoro = Callable[[Any, Any], Coroutine[Any, Any, Any]]


async def maybe_coro(func: MaybeCoro, *args, **kwargs):
    """Call the given func, awaiting if required."""
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    return func(*args, **kwargs)


def get_remaining_calls(func: MaybeCoro, *args, **kwargs) -> int:
    """
    Given a :type:`Callable`, return the amount of remaining
    available calls before these arguments will result
    in the callable being rate-limited.

    Parameters
    ----------
    func: MaybeCoro
        The :type:`Callable` you want to check.
    args
        Any arguments you will pass.
    kwargs
        Any key-word arguments you will pass.

    Returns
    -------
    int
        How many more times this :type:`Callable`
        can be called without being rate-limited.

    Raises
    ------
    NoRegisteredCooldowns
        The given :type:`Callable` has no cooldowns.

    Notes
    -----
    This aggregates all attached cooldowns
    and returns the lowest remaining amount.
    """
    cooldowns: List[Cooldown] = getattr(func, "_cooldowns")
    if not cooldowns:
        raise NoRegisteredCooldowns

    remaining: List[int] = [
        cooldown.remaining_calls(*args, **kwargs) for cooldown in cooldowns
    ]
    return min(remaining)
