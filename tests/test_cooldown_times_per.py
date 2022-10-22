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


@pytest.mark.asyncio
async def test_fully_reset_existence():
    cooldown_times_per: CooldownTimesPer = CooldownTimesPer(1, 0.25, Cooldown(1, 0.25))
    assert cooldown_times_per.fully_reset_at is None

    async with cooldown_times_per:
        pass

    assert cooldown_times_per.fully_reset_at is not None


@pytest.mark.asyncio
async def test_fully_reset_usage():
    cooldown_times_per: CooldownTimesPer = CooldownTimesPer(2, 0.25, Cooldown(2, 0.25))
    assert cooldown_times_per.fully_reset_at is None

    async with cooldown_times_per:
        pass

    r_1 = cooldown_times_per.fully_reset_at
    assert r_1 is not None

    async with cooldown_times_per:
        pass

    r_2 = cooldown_times_per.fully_reset_at
    assert r_2 is not None

    assert r_1 is not r_2
