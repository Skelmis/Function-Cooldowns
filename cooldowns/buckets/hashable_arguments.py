import math


class _HashableArguments:
    """An implementation class, you don't need to create these yourself."""

    # An internal class defined such that we can
    # use *args and **kwargs as keys. We need to
    # do this as mutable items are not hashable,
    # therefore are not suitable for usage as
    # dictionary keys. Thus this wraps those
    # arguments with the hash strategy layed out
    # in __hash__
    def __init__(self, *args, **kwargs):
        self.args: tuple = args
        self.kwargs: dict = kwargs

    def __repr__(self):
        return f"_HashableArguments(args={self.args}, kwargs={self.kwargs})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False

        return self.args == other.args and self.kwargs == other.kwargs

    def __hash__(self) -> int:
        """
        Hashing strategy.

        If we are wrapping nothing, well, -_-
        return the hash of a constant.

        If we are hashing *args, we can simply
        return the hash of the containing tuple
        and let python deal with it.

        If we are hashing **kwargs we hash
        a tuple of tuples, in the form
        ((key, value), ...)

        For *args and **kwargs we combine
        both approaches for the format:
        (*args, (key, value), ...)
        """
        has_args: bool = bool(self.args)
        has_kwargs: bool = bool(self.kwargs)
        if not has_args and not has_kwargs:
            # I'd like a better solution / constant
            return hash(math.pi)

        if has_args and not has_kwargs:
            # Hash the tuple and let python deal with it
            return hash(self.args)

        if not has_args and has_kwargs:
            # Hash kwargs as a tuple of tuples
            rolling_hash = []
            for k, v in self.kwargs.items():
                rolling_hash.append((k, v))

            return hash(tuple(rolling_hash))

        # Same as for kwargs, but with args in it
        rolling_hash = [*self.args]
        for k, v in self.kwargs.items():
            rolling_hash.append((k, v))

        return hash(tuple(rolling_hash))
