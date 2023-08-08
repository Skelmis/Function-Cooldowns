import asyncio

import pytest
from freezegun import freeze_time

from cooldowns import cooldown, CooldownBucket, Cooldown, CallableOnCooldown
from cooldowns.date_util import _utc_now


@pytest.mark.asyncio
async def test_get_cooldown_state():
    @cooldown(1, 15, CooldownBucket.args, cooldown_id=2)
    @cooldown(1, 30, CooldownBucket.kwargs, cooldown_id=1)
    async def test(var, *, bar=None):
        pass

    _cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]

    state = _cooldown_1.get_state()
    assert state == {
        "limit": 1,
        "time_period": 30,
        "pending_reset": False,
        "cooldown_id": 1,
        "cache": {},
    }

    async with _cooldown_1(1):
        pass

    state_2 = _cooldown_1.get_state()
    assert state_2
    assert state_2["cache"]
    for v in state_2["cache"].values():
        assert len(v["next_reset"]) == 1


@pytest.mark.asyncio
async def test_expired_epochs():
    @cooldown(1, 15, CooldownBucket.args, cooldown_id=2)
    @cooldown(1, 30, CooldownBucket.kwargs, cooldown_id=1)
    async def test(var, *, bar=None):
        pass

    _cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]
    _cooldown_1.time_period = 0.1

    state = _cooldown_1.get_state()
    assert state == {
        "limit": 1,
        "time_period": 0.1,
        "pending_reset": False,
        "cooldown_id": 1,
        "cache": {},
    }

    async with _cooldown_1(1):
        pass

    await asyncio.sleep(0.2)

    state_2 = _cooldown_1.get_state()
    assert state_2
    assert state_2["cache"]
    for v in state_2["cache"].values():
        # Assert that old epochs which would have expired
        # by now don't count towards the total
        assert v["current"] == v["limit"]
        assert len(v["next_reset"]) == 0


@pytest.mark.asyncio
async def test_loading():
    @cooldown(1, 15, CooldownBucket.args, cooldown_id=2)
    @cooldown(1, 30, CooldownBucket.kwargs, cooldown_id=1)
    async def test(var, *, bar=None):
        pass

    _cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]
    saved_state = {
        "limit": 2,
        "time_period": 70,
        "pending_reset": True,
        "cooldown_id": 1,
        "cache": {},
    }

    assert _cooldown_1.limit == 1
    assert _cooldown_1.time_period == 30
    assert _cooldown_1.pending_reset is False
    assert _cooldown_1.cooldown_id == 1

    _cooldown_1.load_from_state(saved_state)

    assert _cooldown_1.limit == 2
    assert _cooldown_1.time_period == 70
    assert _cooldown_1.pending_reset is True
    assert _cooldown_1.cooldown_id == 1


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_later_eviction():
    """Tests that later state items get evicted at the correct time"""

    @cooldown(1, 1, CooldownBucket.all, cooldown_id=1)
    async def test(var, *, bar=None):
        pass

    _cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]
    _cooldown_1.load_from_state(
        {
            "cache": {
                "ccopy_reg\n_reconstructor\np0\n(ccooldowns.buckets.hashable_arguments\n_HashableArguments\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nVargs\np6\n(tsVkwargs\np7\n(dp8\nsb.": {
                    "current": 0,
                    "limit": 1,
                    "next_reset": [_utc_now().timestamp() + 0.25],
                    "time_period": 1,
                }
            },
            "cooldown_id": 1,
            "limit": 1,
            "pending_reset": False,
            "time_period": 1,
        }
    )
    assert _cooldown_1._cache != {}, "Test entry should have a cache entry"
    assert _cooldown_1._clean_task is None

    with pytest.raises(CallableOnCooldown):
        async with _cooldown_1():
            pass

    await asyncio.sleep(0.5)
    assert _cooldown_1._clean_task is not None

    async with _cooldown_1():
        pass
