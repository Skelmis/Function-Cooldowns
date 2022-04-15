import asyncio

import pytest

from cooldowns import CooldownTimesPer, Cooldown


@pytest.mark.asyncio
async def test_next_reset():
    cooldown_times_per: CooldownTimesPer = CooldownTimesPer(1, 1, Cooldown(1, 1))
    assert cooldown_times_per.next_reset is None

    async with cooldown_times_per:
        pass

    assert cooldown_times_per.next_reset is not None
    assert cooldown_times_per.next_reset is not None  # Check it doesnt pop

    await asyncio.sleep(1.1)

    assert cooldown_times_per.next_reset is None
