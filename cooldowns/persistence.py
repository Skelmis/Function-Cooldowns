from __future__ import annotations

import pickle
import typing
from asyncio import Queue
import datetime
from typing import TypedDict, Union, Optional, Dict, List

if typing.TYPE_CHECKING:
    from cooldowns import Cooldown, CooldownTimesPer


class CTPState(TypedDict):
    limit: int
    time_period: float
    current: int
    next_reset: List[float]  # List of epoch timestamps


class State(TypedDict):
    limit: int
    time_period: float
    cooldown_id: Optional[Union[int, str]]
    pending_reset: bool
    cache: Dict[str, CTPState]


def _pickle_cooldown(cooldown: Cooldown) -> State:
    cache: Dict[str, CTPState] = {}
    for k, v in cooldown._cache.items():
        next_reset: List[float] = []
        new_queue: Queue = Queue()
        while not v._next_reset.empty():
            item = v._next_reset.get_nowait()
            next_reset.append(item.timestamp())
            new_queue.put_nowait(item)

        v._next_reset = new_queue

        cache[pickle.dumps(k, 0).decode()] = CTPState(
            limit=v.limit,
            time_period=v.time_period,
            current=v.current,
            next_reset=next_reset,
        )

    state: State = {
        "limit": cooldown.limit,
        "time_period": cooldown.time_period,
        "pending_reset": cooldown.pending_reset,
        "cooldown_id": cooldown.cooldown_id,
        "cache": cache,
    }
    return state


def _check_expired(time: datetime.datetime) -> bool:
    """Returns `True` if in the past, `False` otherwise"""
    return datetime.datetime.utcnow() > time


def _unpickle_cooldown(cooldown: Cooldown, state: State) -> None:
    from cooldowns import CooldownTimesPer

    cooldown.limit = state["limit"]
    cooldown.cooldown_id = state["cooldown_id"]
    cooldown.time_period = state["time_period"]
    cooldown.pending_reset = state["pending_reset"]

    cache = {}
    for k, v in state["cache"].items():
        v = typing.cast(CTPState, v)
        hashable_arguments = pickle.loads(k.encode())
        cooldown_times_per = CooldownTimesPer(
            limit=v["limit"],
            time_period=v["time_period"],
            _cooldown=cooldown,
        )
        cooldown_times_per.current = v["current"]

        for epoch in v["next_reset"]:
            epoch_time = datetime.datetime.fromtimestamp(
                epoch,  # tz=datetime.timezone.utc
            )
            if _check_expired(epoch_time):
                # No longer relevant
                cooldown_times_per.current += 1
                continue

            cooldown_times_per._next_reset.put_nowait(epoch_time)

        cache[hashable_arguments] = cooldown_times_per

    cooldown._cache = cache
