from __future__ import annotations

import asyncio
import datetime
import functools
from logging import getLogger
from typing import Callable, Optional, TypeVar, Dict, Union, Type

from .cooldown_times_per import CooldownTimesPer
from .persistence import State, _pickle_cooldown, _unpickle_cooldown
from .exceptions import NonExistent

from .utils import (
    MaybeCoro,
    maybe_coro,
    default_check,
    COOLDOWN_ID,
)
from . import CooldownBucket, utils
from .buckets import _HashableArguments
from .protocols import CooldownBucketProtocol

logger = getLogger(__name__)

T = TypeVar("T", bound=_HashableArguments)
TP = TypeVar("TP", bound=CooldownTimesPer)


def cooldown(
    limit: int,
    time_period: Union[float, datetime.timedelta],
    bucket: CooldownBucketProtocol,
    check: Optional[MaybeCoro] = default_check,
    *,
    cooldown_id: Optional[COOLDOWN_ID] = None,
):
    """
    Wrap this Callable in a cooldown.

    Parameters
    ----------
    limit: int
        How many call's can be made in the time
        period specified by ``time_period``
    time_period: Union[float, datetime.timedelta]
        The time period related to ``limit``. This is seconds.
    bucket: CooldownBucketProtocol
        The :class:`Bucket` implementation to use
        as a bucket to separate cooldown buckets.
    check: Optional[MaybeCoro]
        A Callable which dictates whether
        to apply the cooldown on current invoke.

        If this Callable returns a truthy value,
        then the cooldown will be used for the current call.

        I.e. If you wished to bypass cooldowns, you
        would return False if you invoked the Callable.

        .. note::

            This check will be given the same arguments as
            the item you are applying the cooldown to.

    cooldown_id: Optional[Union[int, str]]
        Useful for resetting individual stacked cooldowns.
        This should be unique globally,
        behaviour is not guaranteed if not unique.

    Raises
    ------
    RuntimeError
        Expected the decorated function to be a coroutine
    CallableOnCooldown
        This call resulted in a cooldown being put into effect
    """
    _cooldown: Cooldown = Cooldown(limit, time_period, bucket, cooldown_id=cooldown_id)

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


def shared_cooldown(
    cooldown_id: Optional[COOLDOWN_ID],
):
    """
    Wrap this Callable in a shared cooldown.

    Use :py:meth:`define_shared_cooldown` before this.

    Parameters
    ----------
    cooldown_id: Optional[Union[int, str]]
        The cooldown for the registered shared cooldown.

    Raises
    ------
    RuntimeError
        Expected the decorated function to be a coroutine
    CallableOnCooldown
        This call resulted in a cooldown being put into effect
    NonExistent
        Could not find a cooldown with this ID registered.
    """
    try:
        _cooldown: Cooldown = utils.shared_cooldown_refs[cooldown_id]
    except KeyError:
        raise NonExistent(
            "Did you forget to define a shared cooldown with this ID? I can't find one."
        ) from None

    def decorator(func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            raise RuntimeError("Expected `func` to be a coroutine")

        _cooldown._func = func
        attached_cooldowns = getattr(func, "_cooldowns", [])
        attached_cooldowns.append(_cooldown)
        setattr(func, "_cooldowns", attached_cooldowns)

        @functools.wraps(func)
        async def inner(*args, **kwargs):
            use_cooldown = await maybe_coro(_cooldown.check, *args, **kwargs)
            if not use_cooldown:
                return await maybe_coro(func, *args, **kwargs)

            async with _cooldown(*args, **kwargs):
                result = await func(*args, **kwargs)

            return result

        return inner

    return decorator


class Cooldown:
    """Represents a cooldown for any given :type:`Callable`."""

    def __init__(
        self,
        limit: int,
        time_period: Union[float, datetime.timedelta],
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
        time_period: Union[float, datetime.timedelta]
            The time period related to ``limit``. This is seconds.
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
        """
        bucket = bucket or CooldownBucket.all
        self.limit: int = limit
        self.time_period: float = (
            time_period
            if isinstance(time_period, (float, int))
            else time_period.total_seconds()
        )
        self.check: MaybeCoro = check
        self.cooldown_id: Optional[Union[int, str]] = cooldown_id

        self._func: Optional[Callable] = func
        self._bucket: CooldownBucketProtocol = bucket
        self.pending_reset: bool = False
        self._last_bucket: Optional[_HashableArguments] = None

        self._cache: Dict[_HashableArguments, TP] = {}

        # How long to sleep between attempt cache clean calls
        self._cache_clean_eagerness: int = 250
        self._clean_task: Optional[asyncio.Task] = None
        # self._clean_task = asyncio.create_task(self._keep_buckets_clear())

        if cooldown_id:
            utils.shared_cooldown_refs[cooldown_id] = self

    async def __aenter__(self) -> "Cooldown":
        if not self._clean_task:
            self._clean_task = asyncio.create_task(self._keep_buckets_clear())

        bucket: TP = self._get_cooldown_for_bucket(self._last_bucket)
        async with bucket:
            return self

    async def __aexit__(self, *_) -> None:
        ...

    def __call__(self, *args, **kwargs):
        self._last_bucket = self.get_bucket(*args, **kwargs)
        return self

    def _get_cooldown_for_bucket(
        self, bucket: _HashableArguments, *, raise_on_create: bool = False
    ) -> TP:
        try:
            return self._cache[bucket]
        except KeyError:
            if raise_on_create:
                raise NonExistent

            _bucket: TP = CooldownTimesPer(self.limit, self.time_period, self)
            self._cache[bucket] = _bucket
            return _bucket

    def get_cooldown_times_per(self, bucket: _HashableArguments) -> Optional[TP]:
        """
        Return the relevant CooldownTimesPer object for
        this bucket, returns None if one does not currently exist.

        Parameters
        ----------
        bucket: _HashableArguments
            The bucket you wish to receive against.
            Get this using :py:meth:`Cooldown.get_bucket`

        Returns
        -------
        Optional[CooldownTimesPer]
            The internal :py:class:`CooldownTimesPer` object
        """
        try:
            return self._get_cooldown_for_bucket(bucket, raise_on_create=True)
        except NonExistent:
            return None

    def get_bucket(self, *args, **kwargs) -> _HashableArguments:
        """
        Return the given bucket for some given arguments.

        This uses the underlying :class:`CooldownBucket`
        and will return a :class:`_HashableArguments`
        instance which is inline with how Cooldown's function.

        Parameters
        ----------
        args: Any
            The arguments to get a bucket for
        kwargs: Any
            The keyword arguments to get a bucket for

        Returns
        -------
        _HashableArguments
            An internally correct representation
            of a bucket for the given arguments.

            This can then be used in :meth:`Cooldown.clear` calls.
        """
        data = self._bucket.process(*args, **kwargs)
        if self._bucket is CooldownBucket.all:
            return _HashableArguments(*data[0], **data[1])

        elif self._bucket is CooldownBucket.args:
            return _HashableArguments(*data)

        elif self._bucket is CooldownBucket.kwargs:
            return _HashableArguments(**data)

        return _HashableArguments(data)

    async def _keep_buckets_clear(self):
        while True:
            self.clear()
            await asyncio.sleep(self._cache_clean_eagerness)

    def clear(
        self, bucket: Optional[_HashableArguments] = None, *, force_evict: bool = False
    ) -> None:
        """
        Remove all un-needed buckets, this maintains buckets
        which are currently tracking cooldown's.

        Parameters
        ----------
        bucket: Optional[_HashableArguments]
            The bucket we wish to reset
        force_evict: bool
            If ``True``, delete all tracked cooldown's
            regardless of whether or not they are needed.

            I.e. reset this back to a fresh state.

        Notes
        -----
        You can get :py:class:`_HashableArguments` by
        using the :meth:`Cooldown.get_bucket` method.
        """
        if not bucket:
            # Reset all buckets
            for bucket_key in list(self._cache.keys()):
                if bucket_key is None:
                    # This shouldn't be None..
                    self._cache.pop(bucket_key, None)  # type: ignore
                    continue

                self.clear(bucket_key, force_evict=force_evict)

        try:
            # Evict item from cache only if it
            # is not tracking anything
            _bucket: TP = self._cache[bucket]
            if not _bucket.has_cooldown or force_evict:
                del self._cache[bucket]
        except KeyError:
            pass

    def remaining_calls(self, *args, **kwargs) -> int:
        """
        Given a :type:`Callable`, return the amount of remaining
        available calls before these arguments will result
        in the callable being rate-limited.

        Parameters
        ----------
        args
        Any arguments you will pass.
        kwargs
            Any key-word arguments you will pass.

        Returns
        -------
        int
            How many more times this :type:`Callable`
            can be called without being rate-limited.
        """
        bucket: _HashableArguments = self.get_bucket(*args, **kwargs)
        try:
            cooldown_times_per: TP = self._get_cooldown_for_bucket(
                bucket, raise_on_create=True
            )
        except NonExistent:
            return self.limit

        return cooldown_times_per.current

    def get_state(self) -> State:
        """Return the state of this cooldown as a dictionary
        in order to be able to persist it.

        Returns
        -------
        State
            This cooldown as a dictionary
        """
        return _pickle_cooldown(self)

    def load_from_state(self, state: State) -> None:
        """Load this cooldown as per `state`

        Parameters
        ----------
        state: State
            The state you wish to set this cooldown to

        Notes
        -----
        state should be the output of :py:meth:`Cooldown.get_state`
        and remain unmodified in order for this operation to work.
        """
        _unpickle_cooldown(self, state)

    def __repr__(self) -> str:
        return f"Cooldown(limit={self.limit}, time_period={self.time_period}, func={self._func})"

    @property
    def bucket(self) -> CooldownBucketProtocol:
        """Returns the underlying bucket to process cooldowns against."""
        return self._bucket

    @property
    def func(self) -> Optional[Callable]:
        """Returns the wrapped function."""
        return self._func
