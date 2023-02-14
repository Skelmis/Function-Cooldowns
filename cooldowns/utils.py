from __future__ import annotations

import asyncio
import datetime
from typing import Callable, Any, Coroutine, List, TYPE_CHECKING, Union, Dict, Optional

from cooldowns.exceptions import (
    NoRegisteredCooldowns,
    NonExistent,
    CooldownAlreadyExists,
)

if TYPE_CHECKING:
    from cooldowns import Cooldown, CooldownBucketProtocol, StaticCooldown

    CooldownT = Union[Cooldown, StaticCooldown]

# hA! Hey you, come say hi :O
COOLDOWN_ID = Union[int, str]
# A 'global state' of sorts
shared_cooldown_refs: Dict[COOLDOWN_ID, CooldownT] = {}
MaybeCoro = Callable[[Any, Any], Coroutine[Any, Any, Any]]


def default_check(*args, **kwargs):
    return True


async def maybe_coro(func: MaybeCoro, *args, **kwargs):
    """Call the given func, awaiting if required."""
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    return func(*args, **kwargs)


def _get_cooldowns_or_raise(func: MaybeCoro) -> List[CooldownT]:
    cooldowns: List[CooldownT] = getattr(func, "_cooldowns")
    if not cooldowns:
        raise NoRegisteredCooldowns

    return cooldowns


def get_remaining_calls(func: MaybeCoro, *args, **kwargs) -> int:
    """
    Given a `Callable`, return the amount of remaining
    available calls before these arguments will result
    in the callable being rate-limited.

    Parameters
    ----------
    func: MaybeCoro
        The `Callable` you want to check.
    args
        Any arguments you will pass.
    kwargs
        Any key-word arguments you will pass.

    Returns
    -------
    int
        How many more times this `Callable`
        can be called without being rate-limited.

    Raises
    ------
    NoRegisteredCooldowns
        The given `Callable` has no cooldowns.

    Notes
    -----
    This aggregates all attached cooldowns
    and returns the lowest remaining amount.
    """
    cooldowns: List[CooldownT] = _get_cooldowns_or_raise(func)

    remaining: List[int] = [
        cooldown.remaining_calls(*args, **kwargs) for cooldown in cooldowns
    ]
    return min(remaining)


def reset_cooldowns(func: MaybeCoro):
    """
    Reset all cooldown's on this `Callable`
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
    cooldowns: List[CooldownT] = _get_cooldowns_or_raise(func)
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
    cooldowns: List[CooldownT] = _get_cooldowns_or_raise(func)
    for cooldown in cooldowns:
        bucket = cooldown.get_bucket(*args, **kwargs)
        try:
            cooldown._get_cooldown_for_bucket(bucket, raise_on_create=True)
        except NonExistent:
            continue
        else:
            cooldown.clear(bucket, force_evict=True)


def reset_cooldown(cooldown_id: COOLDOWN_ID):
    """
    Reset the cooldown denoted by cooldown_id.

    Parameters
    ----------
    cooldown_id: Union[int, str]
        The id of the cooldown we wish to reset

    Raises
    ------
    NonExistent
        Cannot find a cooldown with this id.
    """
    try:
        shared_cooldown_refs[cooldown_id].clear(force_evict=True)
    except KeyError:
        raise NonExistent(
            f"Cannot find a cooldown with the id '{cooldown_id}'."
        ) from None


def get_cooldown(func: MaybeCoro, cooldown_id: COOLDOWN_ID) -> CooldownT:
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
    cooldowns: List[CooldownT] = _get_cooldowns_or_raise(func)
    for cooldown in cooldowns:
        if cooldown.cooldown_id == cooldown_id:
            return cooldown

    raise NonExistent(
        f"Cannot find a cooldown with the id '{cooldown_id}' on {func.__name__}."
    )


def get_all_cooldowns(
    func: MaybeCoro,
) -> List[CooldownT]:
    """
    Get all the :py:class:`Cooldown` objects from the func provided.

    Parameters
    ----------
    func: MaybeCoro
        The func with this cooldown.

    Returns
    -------
    List[Cooldown]
        The associated cooldowns

    Raises
    ------
    NoRegisteredCooldowns
        No cooldowns on this func
    """
    return _get_cooldowns_or_raise(func)


def define_shared_cooldown(
    limit: int,
    time_period: float,
    bucket: CooldownBucketProtocol,
    cooldown_id: COOLDOWN_ID,
    *,
    check: Optional[MaybeCoro] = default_check,
):
    """
    Define a global cooldown which can be used to ratelimit
    1 or more callables under the same situations.

    View the examples for how to use this.

    Parameters
    ----------
    limit: int
        How many call's can be made in the time
        period specified by ``time_period``
    time_period: float
        The time period related to ``limit``
    bucket: CooldownBucketProtocol
        The :class:`Bucket` implementation to use
        as a bucket to separate cooldown buckets.
    cooldown_id: Union[int, str]
        The ID used to refer to this when defining a shared_cooldown

        This should be unique globally,
        behaviour is not guaranteed if not unique.
    check: Optional[MaybeCoro]
        A Callable which dictates whether or not
        to apply the cooldown on current invoke.

        If this Callable returns a truthy value,
        then the cooldown will be used for the current call.

        I.e. If you wished to bypass cooldowns, you
        would return False if you invoked the Callable.

    Raises
    ------
    CooldownAlreadyExists
        A Cooldown with this ID already exists.

    Notes
    -----
    All times are internally handled based off UTC.
    """
    if cooldown_id in shared_cooldown_refs:
        raise CooldownAlreadyExists

    from .cooldown import Cooldown

    cooldown: Cooldown = Cooldown(
        check=check,
        limit=limit,
        bucket=bucket,
        cooldown_id=cooldown_id,
        time_period=time_period,
    )
    shared_cooldown_refs[cooldown_id] = cooldown


def define_shared_static_cooldown(
    limit: int,
    reset_times: Union[datetime.time, List[datetime.time]],
    bucket: CooldownBucketProtocol,
    cooldown_id: COOLDOWN_ID,
    *,
    check: Optional[MaybeCoro] = default_check,
):
    """
    Define a global cooldown which can be used to ratelimit
    1 or more callables under the same situations.

    View the examples for how to use this.

    Parameters
    ----------
    limit: int
        How many call's can be made in the time
        period specified by ``time_period``
    reset_times: Union[datetime.time, List[datetime.time]]
        A time or list of the possible
        times in the day to reset cooldowns at
    bucket: CooldownBucketProtocol
        The :class:`Bucket` implementation to use
        as a bucket to separate cooldown buckets.
    cooldown_id: Union[int, str]
        The ID used to refer to this when defining a shared_cooldown

        This should be unique globally,
        behaviour is not guaranteed if not unique.
    check: Optional[MaybeCoro]
        A Callable which dictates whether or not
        to apply the cooldown on current invoke.

        If this Callable returns a truthy value,
        then the cooldown will be used for the current call.

        I.e. If you wished to bypass cooldowns, you
        would return False if you invoked the Callable.

    Raises
    ------
    CooldownAlreadyExists
        A Cooldown with this ID already exists.
    """
    if cooldown_id in shared_cooldown_refs:
        raise CooldownAlreadyExists

    from .static_cooldown import StaticCooldown

    cooldown: StaticCooldown = StaticCooldown(
        check=check,
        limit=limit,
        bucket=bucket,
        cooldown_id=cooldown_id,
        reset_times=reset_times,
    )
    shared_cooldown_refs[cooldown_id] = cooldown


def get_shared_cooldown(cooldown_id: COOLDOWN_ID) -> CooldownT:
    """Retrieve a shared :py:class:`Cooldown` or :py:class:`StaticCooldown` object.

    Parameters
    ----------
    cooldown_id: Union[int, str]
        The id of the cooldown we wish to get

    Returns
    -------
    Cooldown
        The associated cooldown

    Raises
    ------
    NonExistent
        Failed to find that cooldown
    """
    cooldown: Optional[CooldownT] = shared_cooldown_refs.get(cooldown_id)
    if not cooldown:
        raise NonExistent(f"Cannot find a cooldown with the id '{cooldown_id}'.")

    return cooldown
