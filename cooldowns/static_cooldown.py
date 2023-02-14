import datetime
from typing import List, Callable, Optional, Union

from . import Cooldown, CooldownBucketProtocol
from .buckets import _HashableArguments
from .cooldown import TP
from .exceptions import NonExistent
from .static_times_per import StaticTimesPer
from .utils import MaybeCoro, default_check


class StaticCooldown(Cooldown):
    """A cooldown which implements a set amount of cooldown reset times per day."""

    def __init__(
        self,
        limit: int,
        reset_times: List[datetime.time],
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
        reset_times: List[datetime.time]
            A list of the possible times in the day
            to reset cooldowns at
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
        super().__init__(
            limit=limit,
            time_period=0,
            bucket=bucket,
            func=func,
            cooldown_id=cooldown_id,
            check=check,
        )
        self._reset_times: List[datetime.time] = reset_times

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
