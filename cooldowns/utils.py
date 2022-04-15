from __future__ import annotations

import asyncio
from typing import Callable, Any, Coroutine, List, TYPE_CHECKING, Union

from cooldowns.exceptions import NoRegisteredCooldowns, NonExistent

if TYPE_CHECKING:
    from cooldowns import Cooldown, CooldownBucket, CooldownTimesPer

MaybeCoro = Callable[[Any, Any], Coroutine[Any, Any, Any]]


async def maybe_coro(func: MaybeCoro, *args, **kwargs):
    """Call the given func, awaiting if required."""
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    return func(*args, **kwargs)


def _get_cooldowns_or_raise(func: MaybeCoro) -> List[Cooldown]:
    cooldowns: List[Cooldown] = getattr(func, "_cooldowns")
    if not cooldowns:
        raise NoRegisteredCooldowns

    return cooldowns


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
    cooldowns: List[Cooldown] = _get_cooldowns_or_raise(func)

    remaining: List[int] = [
        cooldown.remaining_calls(*args, **kwargs) for cooldown in cooldowns
    ]
    return min(remaining)


def reset_cooldowns(func: MaybeCoro):
    """
    Reset all cooldown's on this :type:`Callable`
    back to default settings.


    Parameters
    ----------
    func: MaybeCoro
        The func with cooldowns we should reset.

    Raises
    ------
    NoRegisteredCooldowns
        The func has no cooldown's attached.
    """
    cooldowns: List[Cooldown] = _get_cooldowns_or_raise(func)
    for cooldown in cooldowns:
        cooldown.clear(force_evict=True)


def reset_bucket(func: MaybeCoro, *args, **kwargs):
    """
    Reset all buckets matching the provided arguments.

    Parameters
    ----------
    func: MaybeCoro
        The func with cooldowns we should reset.
    args
        Any arguments you will pass.
    kwargs
        Any key-word arguments you will pass.

    Notes
    -----
    Does nothing if it resets nothing.
    """
    cooldowns: List[Cooldown] = _get_cooldowns_or_raise(func)
    for cooldown in cooldowns:
        bucket = cooldown.get_bucket(*args, **kwargs)
        try:
            cooldown._get_cooldown_for_bucket(bucket, raise_on_create=True)
        except NonExistent:
            continue
        else:
            cooldown.clear(bucket, force_evict=True)


def reset_cooldown(func: MaybeCoro, cooldown_id: Union[int, str]):
    """
    Reset the cooldown denoted by cooldown_id.

    Parameters
    ----------
    func: MaybeCoro
        The func with cooldowns we should reset.
    cooldown_id: Union[int, str]
        The id of the cooldown we wish to reset

    Raises
    ------
    NonExistent
        Cannot find a cooldown with this id.
    """
    cooldowns: List[Cooldown] = _get_cooldowns_or_raise(func)
    for cooldown in cooldowns:
        if cooldown.cooldown_id == cooldown_id:
            cooldown.clear(force_evict=True)
            return

    raise NonExistent(
        f"Cannot find a cooldown with the id '{cooldown_id}' on {func.__name__}."
    )


def get_cooldown(func: MaybeCoro, cooldown_id: Union[int, str]) -> Cooldown:
    """
    Get the :py:class:`Cooldown` object from the func
    with the provided cooldown id.

    Parameters
    ----------
    func: MaybeCoro
        The func with this cooldown.
    cooldown_id: Union[int, str]
        The id of the cooldown we wish to get

    Returns
    -------
    Cooldown
        The associated cooldown

    Raises
    ------
    NonExistent
        Failed to find that cooldown on this func.
    """
    cooldowns: List[Cooldown] = _get_cooldowns_or_raise(func)
    for cooldown in cooldowns:
        if cooldown.cooldown_id == cooldown_id:
            return cooldown

    raise NonExistent(
        f"Cannot find a cooldown with the id '{cooldown_id}' on {func.__name__}."
    )
