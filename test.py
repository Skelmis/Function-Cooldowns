import asyncio


def func():
    pass


if not asyncio.iscoroutinefunction(func):
    raise RuntimeError(
        f"Expected `{func.__name__}` to be a coroutine, found {func.__class__.__name__!r} instead"
    )
