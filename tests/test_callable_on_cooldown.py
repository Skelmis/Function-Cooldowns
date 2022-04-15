import asyncio

import pytest

from cooldowns import CooldownTimesPer, Cooldown
from cooldowns.exceptions import CallableOnCooldown


@pytest.mark.asyncio
async def test_retry_after():
    cooldown_times_per: CooldownTimesPer = CooldownTimesPer(1, 15, Cooldown(1, 15))
    assert cooldown_times_per.next_reset is None
    async with cooldown_times_per:
        pass

    try:
        async with cooldown_times_per:
            pass

        assert 1 == 2, "This should never be called."
    except CallableOnCooldown as e:
        assert e.retry_after == 15
        assert cooldown_times_per.next_reset is not None

    await asyncio.sleep(1)
    try:
        async with cooldown_times_per:
            pass

        assert 1 == 2, "This should never be called."
    except CallableOnCooldown as e:
        # Should be less then 14, i.e. going down now
        assert e.retry_after < 15