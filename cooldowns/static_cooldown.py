import asyncio
import datetime
import functools
from typing import List, Callable, Optional, Union

from . import Cooldown, CooldownBucketProtocol, utils
from .buckets import _HashableArguments
from .cooldown import TP
from .exceptions import NonExistent
from .static_times_per import StaticTimesPer
from .utils import MaybeCoro, default_check, COOLDOWN_ID, maybe_coro


def static_cooldown(
    limit: int,
    reset_times: Union[datetime.time, List[datetime.time]],
    bucket: CooldownBucketProtocol,
    check: Optional[MaybeCoro] = default_check,
    *,
    cooldown_id: Optional[COOLDOWN_ID] = None,
):
    """
    Parameters
    ----------
    limit: int
        How many call's can be made in the time
        period specified by ``time_period``
    reset_times: Union[datetime.time, List[datetime.time]]
        A time or list of the possible
        times in the day to reset cooldowns at
    bucket: Optional[CooldownBucketProtocol]
        The :class:`Bucket` implementation to use
        as a bucket to separate cooldown buckets.

        Defaults to :class:`CooldownBucket.all`
    func: Optional[Callable]
        The function this cooldown is attached to
    cooldown_id: Optional[Union[int, str]]
        Useful for resetting individual stacked cooldowns.
        This should be unique globally,
        behaviour is not guaranteed if not unique.

    Other Parameters
    ----------------
    check: Optional[MaybeCoro]
        The check used to validate calls to this Cooldown.

        This is not used here, however, its required as an
        implementation detail for shared cooldowns and can
        be safely ignored as a parameter.

        .. note::

            This check will be given the same arguments as
            the item you are applying the cooldown to.

    Notes
    -----
    All times are internally handled based off UTC.

    Raises
    ------
    RuntimeError
        Expected the decorated function to be a coroutine
    CallableOnCooldown
        This call resulted in a cooldown being put into effect
    """
    _cooldown: Cooldown = StaticCooldown(
        limit, reset_times, bucket, cooldown_id=cooldown_id
    )

    if cooldown_id:
        utils.shared_cooldown_refs[cooldown_id] = _cooldown

    def decorator(func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            raise RuntimeError(
                f"Expected `func` to be a coroutine, "
                f"found {func} of type {func.__class__.__name__!r} instead"  # noqa
            )

        _cooldown._func = func
        attached_cooldowns = getattr(func, "_cooldowns", [])
        attached_cooldowns.append(_cooldown)
        setattr(func, "_cooldowns", attached_cooldowns)

        @functools.wraps(func)
        async def inner(*args, **kwargs):
            use_cooldown = await maybe_coro(check, *args, **kwargs)
            if not use_cooldown:
                return await maybe_coro(func, *args, **kwargs)

            self_arg = None
            if "self" in kwargs:
                self_arg = kwargs.pop("self")

            async with _cooldown(*args, **kwargs):
                if self_arg:
                    kwargs["self"] = self_arg
                    result = await func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)

            return result

        return inner

    return decorator


class StaticCooldown(Cooldown):
    """A cooldown which implements a set amount of cooldown reset times per day."""

    def __init__(
        self,
        limit: int,
        reset_times: Union[datetime.time, List[datetime.time]],
        bucket: Optional[CooldownBucketProtocol] = None,
        func: Optional[Callable] = None,
        *,
        cooldown_id: Optional[Union[int, str]] = None,
        check: Optional[MaybeCoro] = default_check,
    ) -> None:
        """
        Parameters
        ----------
        limit: int
            How many call's can be made in the time
            period specified by ``time_period``
        reset_times: Union[datetime.time, List[datetime.time]]
            A time or list of the possible
            times in the day to reset cooldowns at
        bucket: Optional[CooldownBucketProtocol]
            The :class:`Bucket` implementation to use
            as a bucket to separate cooldown buckets.

            Defaults to :class:`CooldownBucket.all`
        func: Optional[Callable]
            The function this cooldown is attached to
        cooldown_id: Optional[Union[int, str]]
            Useful for resetting individual stacked cooldowns.
            This should be unique globally,
            behaviour is not guaranteed if not unique.

        Other Parameters
        ----------------
        check: Optional[MaybeCoro]
            The check used to validate calls to this Cooldown.

            This is not used here, however, its required as an
            implementation detail for shared cooldowns and can
            be safely ignored as a parameter.

            .. note::

                This check will be given the same arguments as
                the item you are applying the cooldown to.

        Notes
        -----
        All times are internally handled based off UTC.
        """
        super().__init__(
            limit=limit,
            time_period=0,
            bucket=bucket,
            func=func,
            cooldown_id=cooldown_id,
            check=check,
        )
        self._reset_times: List[datetime.time] = (
            reset_times if isinstance(reset_times, list) else [reset_times]
        )

    def __repr__(self) -> str:
        return f"StaticCooldown(limit={self.limit}, resets_at=[...], func={self._func})"

    def _get_cooldown_for_bucket(
        self, bucket: _HashableArguments, *, raise_on_create: bool = False
    ) -> TP:
        try:
            return self._cache[bucket]
        except KeyError:
            if raise_on_create:
                raise NonExistent

            _bucket: TP = StaticTimesPer(self.limit, self._reset_times, self)
            self._cache[bucket] = _bucket
            return _bucket
