import asyncio

import pytest

from cooldowns import cooldown, CooldownBucket, Cooldown


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
