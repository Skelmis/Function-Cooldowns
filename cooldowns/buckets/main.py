from enum import Enum

from cooldowns.exceptions import UnknownBucket


class CooldownBucket(Enum):
    """
    A collection of generic CooldownBucket's for usage in cooldown's.

    See :py:class:`cooldowns.protocols.bucket.CooldownBucketProtocol`

    Attributes
    ==========
    all
        The buckets are defined using all
        arguments passed to the `Callable`
    args
        The buckets are defined using all
        non-keyword arguments passed to the `Callable`
    kwargs
        The buckets are defined using all
        keyword arguments passed to the `Callable`
    """

    all = 0
    args = 1
    kwargs = 2

    def process(self, *args, **kwargs):
        if self is CooldownBucket.all:
            return args, kwargs

        elif self is CooldownBucket.args:
            return args

        elif self is CooldownBucket.kwargs:
            return kwargs

        raise UnknownBucket
