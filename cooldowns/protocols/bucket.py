from typing import Any, Protocol


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
