import asyncio
from typing import Callable, Any, Coroutine

MaybeCoro = Callable[[Any, Any], Coroutine[Any, Any, Any]]


async def maybe_coro(func: MaybeCoro, *args, **kwargs):
    """Call the given func, awaiting if required."""
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)

    return func(*args, **kwargs)
