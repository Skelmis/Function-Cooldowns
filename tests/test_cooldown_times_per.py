import asyncio

import pytest

from cooldowns import CooldownTimesPer, Cooldown


@pytest.mark.asyncio
async def test_next_reset():
    cooldown_times_per: CooldownTimesPer = CooldownTimesPer(1, 0.25, Cooldown(1, 0.25))
    assert cooldown_times_per.next_reset is None

    async with cooldown_times_per:
        pass

    assert cooldown_times_per.next_reset is not None
    assert cooldown_times_per.next_reset is not None  # Check it doesnt pop

    await asyncio.sleep(0.3)

    assert cooldown_times_per.next_reset is None


@pytest.mark.asyncio
async def test_next_reset_timer():
    cooldown_times_per: CooldownTimesPer = CooldownTimesPer(1, 0.25, Cooldown(1, 0.25))
    assert cooldown_times_per.next_reset is None

    async with cooldown_times_per:
        pass

    r_1 = cooldown_times_per.next_reset
    await asyncio.sleep(0.1)
    assert cooldown_times_per.next_reset == r_1

    await asyncio.sleep(0.3)

    assert cooldown_times_per.next_reset is None
