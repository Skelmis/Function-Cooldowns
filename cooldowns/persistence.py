import asyncio
import pickle
import typing
from copy import deepcopy
from typing import TypedDict, Dict, List, Union, Optional

from cooldowns import Cooldown, CooldownBucketProtocol
from cooldowns.utils import MaybeCoro, COOLDOWN_ID, _get_cooldowns_or_raise


class State(TypedDict):
    limit: int
    time_period: float
    check: str  # Pickled callable
    bucket: str  # Pickled CooldownBucketProtocol
    pending_reset: bool
    last_bucket: Optional[str]  # Pickled _HashableArguments
    cache: str  # Pickled Dict[_HashableArguments, CooldownTimesPer]
    cooldown_id: Optional[Union[int, str]]


def _pickle_cooldown(cooldown: Cooldown) -> State:
    state: State = {
        "limit": cooldown.limit,
        "time_period": cooldown.time_period,
        "check": pickle.dumps(cooldown.check, 0).decode(),
        "cooldown_id": cooldown.cooldown_id,
        "bucket": pickle.dumps(cooldown._bucket, 0).decode(),
        "pending_reset": cooldown.pending_reset,
        "last_bucket": pickle.dumps(cooldown._last_bucket, 0).decode(),
        "cache": pickle.dumps(cooldown._cache, 0).decode(),
    }

    return state


def get_cooldown_state(func: MaybeCoro) -> List[State]:
    cooldowns: List[Cooldown] = _get_cooldowns_or_raise(func)
    states: List[State] = []
    for cooldown in cooldowns:
        states.append(_pickle_cooldown(cooldown))

    return states


def load_cooldown_state(func: MaybeCoro, states: List[State]) -> None:
    cooldowns: List[Cooldown] = []
    for state in states:
        state = typing.cast(State, state)
        print(type(state))
        unpick: Dict = pickle.loads(state["cache"].encode())
        print(list(unpick.values())[0])
        break


def get_global_state() -> Dict[COOLDOWN_ID, State]:
    pass


def load_global_state(
    func_mappings: Dict[COOLDOWN_ID, MaybeCoro],
    data: Dict[COOLDOWN_ID, State],
) -> None:
    pass
