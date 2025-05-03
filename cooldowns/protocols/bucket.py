from typing import Any, Protocol, Callable, Coroutine

CallableT = Callable[..., Any] | Coroutine[Any, Any, Any]


class CooldownBucketProtocol(Protocol):
    """CooldownBucketProtocol implementation Protocol."""

    def process(self, *args, **kwargs) -> Any:
        """

        Returns
        -------
        Any
            The values returned from this method
            will be used to represent a bucket.
        """
        ...


class AsyncCooldownBucketProtocol(Protocol):
    """AsyncCooldownBucketProtocol implementation Protocol."""

    async def process(self, *args, **kwargs) -> Any:
        """

        Returns
        -------
        Any
            The values returned from this method
            will be used to represent a bucket.
        """
        ...
