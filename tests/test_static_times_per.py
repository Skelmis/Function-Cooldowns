import asyncio
import datetime

import pytest
from freezegun import freeze_time

from cooldowns import StaticTimesPer, StaticCooldown, CallableOnCooldown
from cooldowns.date_util import _utc_now


@pytest.mark.asyncio
# Freeze time for timed based testing instead of dynamic testing
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_next_reset():
    cooldown_times_per: StaticTimesPer = StaticTimesPer(
        1,
        [datetime.time(hour=3, minute=30, second=1)],
        StaticCooldown(1, datetime.time(hour=3, minute=30, second=1)),
    )
    assert cooldown_times_per.next_reset is None

    async with cooldown_times_per:
        pass

    assert cooldown_times_per.next_reset is not None
    assert cooldown_times_per.next_reset is not None  # Check it doesnt pop

    await asyncio.sleep(1.1)
    assert cooldown_times_per.next_reset is None


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_next_reset_timer():
    cooldown_times_per: StaticTimesPer = StaticTimesPer(
        1,
        [datetime.time(hour=3, minute=30, second=1)],
        StaticCooldown(1, datetime.time(hour=3, minute=30, second=1)),
    )
    assert cooldown_times_per.next_reset is None

    async with cooldown_times_per:
        pass

    r_1 = cooldown_times_per.next_reset
    await asyncio.sleep(0.1)
    assert cooldown_times_per.next_reset == r_1

    await asyncio.sleep(1)
    assert cooldown_times_per.next_reset is None


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_fully_reset_existence():
    cooldown_times_per: StaticTimesPer = StaticTimesPer(
        1,
        [datetime.time(hour=3, minute=30, second=1)],
        StaticCooldown(1, datetime.time(hour=3, minute=30, second=1)),
    )
    assert cooldown_times_per.fully_reset_at is None

    async with cooldown_times_per:
        pass

    assert cooldown_times_per.fully_reset_at is not None


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_fully_reset_usage():
    cooldown_times_per: StaticTimesPer = StaticTimesPer(
        2,
        [datetime.time(hour=3, minute=30, second=1)],
        StaticCooldown(2, datetime.time(hour=3, minute=30, second=1)),
    )
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


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_multiple_current_resets():
    cooldown_times_per: StaticTimesPer = StaticTimesPer(
        2,
        [datetime.time(hour=3, minute=30, second=1)],
        StaticCooldown(2, datetime.time(hour=3, minute=30, second=1)),
    )
    reset_at = cooldown_times_per.get_next_reset(_utc_now())
    assert cooldown_times_per.fully_reset_at is None

    async with cooldown_times_per:
        pass

    r_1 = cooldown_times_per.fully_reset_at
    assert r_1 == reset_at

    async with cooldown_times_per:
        pass

    # Both queued cooldowns should reset at the same time
    r_2 = cooldown_times_per.fully_reset_at
    assert r_2 == reset_at
    assert r_1 is not r_2


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_multiple_reset_times():
    """Tests the static times per picks the correct next time"""
    cooldown_times_per: StaticTimesPer = StaticTimesPer(
        2,
        [
            datetime.time(hour=3, minute=30, second=1),
            datetime.time(hour=3, minute=30, second=3),
        ],
        StaticCooldown(
            2,
            [
                datetime.time(hour=3, minute=30, second=1),
                datetime.time(hour=3, minute=30, second=3),
            ],
        ),
    )
    reset_at_1 = cooldown_times_per.get_next_reset(_utc_now())
    assert cooldown_times_per.fully_reset_at is None

    async with cooldown_times_per:
        pass

    r_1 = cooldown_times_per.fully_reset_at
    assert r_1 == reset_at_1

    await asyncio.sleep(1)
    reset_at_2 = cooldown_times_per.get_next_reset(_utc_now())
    assert reset_at_1 != reset_at_2 and reset_at_1 is not reset_at_2

    async with cooldown_times_per:
        pass

    r_2 = cooldown_times_per.fully_reset_at
    assert r_2 != reset_at_1
    assert r_2 == reset_at_2


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_static_errors():
    cooldown_times_per: StaticTimesPer = StaticTimesPer(
        1,
        [
            datetime.time(hour=3, minute=30, second=1),
            datetime.time(hour=3, minute=30, second=3),  # For second test stage
        ],
        StaticCooldown(2, datetime.time(hour=3, minute=30, second=2)),
    )
    async with cooldown_times_per:
        pass

    try:
        async with cooldown_times_per:
            pass

        assert 1 == 2, "This should never be called."
    except CallableOnCooldown as e:
        assert e.retry_after is not None
        assert round(e.retry_after) in [1, 2]
        assert cooldown_times_per.next_reset is not None

    await asyncio.sleep(1)
    assert cooldown_times_per.next_reset is None

    async with cooldown_times_per:
        pass

    try:
        async with cooldown_times_per:
            pass

        assert 1 == 2, "This should never be called."
    except CallableOnCooldown as e:
        r_1 = e.retry_after
        assert r_1 is not None
        assert round(r_1) in [1, 2], "Sanity catch to avoid long sleep times"
        assert cooldown_times_per.next_reset is not None
        await asyncio.sleep(r_1)
        assert cooldown_times_per.next_reset is None
        async with cooldown_times_per:
            pass
