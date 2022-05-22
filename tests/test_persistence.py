import pytest

from cooldowns import cooldown, CooldownBucket, Cooldown, get_cooldown_state


@pytest.mark.asyncio
async def test_get_cooldown_state():
    @cooldown(1, 15, CooldownBucket.args, cooldown_id=2)
    @cooldown(1, 30, CooldownBucket.kwargs, cooldown_id=1)
    async def test(var, *, bar=None):
        pass

    _cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]

    state = get_cooldown_state(test)
    assert len(state) == 2
    assert state[0] == {
        "limit": 1,
        "time_period": 30,
        "check": "ccooldowns.utils\ndefault_check\np0\n.",
        "cooldown_id": 1,
        "bucket": "ccooldowns.buckets.main\nCooldownBucket\np0\n(I2\ntp1\nRp2\n.",
        "pending_reset": False,
        "last_bucket": "N.",
        "cache": "(dp0\n.",
    }

    await test(1)

    # Tests the tasks are rebuilt as expected
    state_2 = get_cooldown_state(test)
    assert len(state_2) == 2
