import asyncio
import datetime
from enum import Enum

import pytest
from freezegun import freeze_time

from cooldowns import (
    StaticCooldown,
    CooldownBucket,
    StaticTimesPer,
    define_shared_static_cooldown,
    static_cooldown,
    shared_cooldown,
    define_shared_cooldown,
)
from cooldowns.buckets import _HashableArguments
from cooldowns.exceptions import CallableOnCooldown, NonExistent, CooldownAlreadyExists


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_static_cooldown():
    cooldown = StaticCooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        CooldownBucket.args,
    )

    async with cooldown:
        with pytest.raises(CallableOnCooldown):
            async with cooldown:
                pass

        await asyncio.sleep(1.1)  # Cooldown 'length'
        # This tests that cooldowns get reset
        async with cooldown:
            pass


@pytest.mark.asyncio
async def test_get_static_bucket():
    cooldown = StaticCooldown(1, datetime.time())
    hashed_args = await cooldown.get_bucket(1, 2, three=3, four=4)
    assert hashed_args == _HashableArguments(1, 2, three=3, four=4)


@pytest.mark.asyncio
async def test_static_cooldown_decor_simple():
    # Can be called once every second
    # Default bucket is ALL arguments
    @static_cooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        bucket=CooldownBucket.all,
    )
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs

    # Call it once, so its on cooldown after this
    data = await test_func(1, two=2)
    assert data == ((1,), {"two": 2})

    with pytest.raises(CallableOnCooldown):
        # Since this uses the same arguments
        # as the previous call, it comes under
        # the same bucket, and thus gets rate-limited
        await test_func(1, two=2)

    # Shouldn't error as it comes under the
    # bucket _HashableArguments(1) rather then
    # the bucket _HashableArguments(1, two=2)
    # which are completely different
    await test_func(1)


@pytest.mark.asyncio
async def test_static_cooldown_args():
    @static_cooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        bucket=CooldownBucket.args,
    )
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs

    data = await test_func(1, two=2)
    assert data == ((1,), {"two": 2})

    with pytest.raises(CallableOnCooldown):
        await test_func(1)

    await test_func(2)


@pytest.mark.asyncio
async def test_static_cooldown_kwargs():
    @static_cooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        bucket=CooldownBucket.kwargs,
    )
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs

    data = await test_func(1, two=2)
    assert data == ((1,), {"two": 2})

    with pytest.raises(CallableOnCooldown):
        await test_func(two=2)

    await test_func(two=3)


@pytest.mark.asyncio
async def test_static_custom_buckets():
    class CustomBucket(Enum):
        first_arg = 1

        def process(self, *args, **kwargs):
            if self is CustomBucket.first_arg:
                # This bucket is based ONLY off
                # of the first argument passed
                return args[0]

    @static_cooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        bucket=CustomBucket.first_arg,
    )
    async def test_func(*args, **kwargs):
        pass

    await test_func(1, 2, 3)

    with pytest.raises(CallableOnCooldown):
        await test_func(1)

    await test_func(2)


@pytest.mark.asyncio
async def test_static_stacked_cooldowns():
    # Can call ONCE time_period second using the same args
    # Can call TWICE time_period second using the same kwargs
    @static_cooldown(
        1, datetime.time(hour=3, minute=30, second=1), bucket=CooldownBucket.args
    )
    @static_cooldown(
        2, datetime.time(hour=3, minute=30, second=3), bucket=CooldownBucket.kwargs
    )
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs

    await test_func(2, one=1)
    with pytest.raises(CallableOnCooldown):
        await test_func(2)

    # Args don't matter, its a kwargs based CooldownBucketProtocol
    await test_func(1, two=2)
    await test_func(two=2)
    with pytest.raises(CallableOnCooldown):
        await test_func(two=2)


def test_sync_static_cooldowns():
    with pytest.raises(RuntimeError):
        # Cant use sync functions
        @static_cooldown(
            1,
            datetime.time(hour=3, minute=30, second=1),
            bucket=CooldownBucket.args,
        )
        def test_func(*args, **kwargs) -> (tuple, dict):
            return args, kwargs


@pytest.mark.asyncio
async def test_static_checks():
    """Ensures the check works as expected"""

    # Only apply cooldowns if the first arg is 1
    @static_cooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        bucket=CooldownBucket.args,
        check=lambda *args, **kwargs: args[0] == 1,
    )
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs

    await test_func(1, two=2)
    await test_func(2)
    await test_func(tuple())
    with pytest.raises(CallableOnCooldown):
        await test_func(1)


@pytest.mark.asyncio
async def test_static_async_checks():
    """Ensures the check works as expected with async methods"""

    # Only apply cooldowns if the first arg is 1
    async def mock_db_check(*args, **kwargs):
        # You can do database calls here or anything
        # since this is an async context
        return args[0] == 1

    @static_cooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        bucket=CooldownBucket.args,
        check=mock_db_check,
    )
    async def test_func(*args, **kwargs) -> (tuple, dict):
        return args, kwargs

    await test_func(1, two=2)
    await test_func(2)
    await test_func(tuple())
    with pytest.raises(CallableOnCooldown):
        await test_func(1)


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_static_cooldown_clearing():
    cooldown: StaticCooldown = StaticCooldown(
        1, datetime.time(second=1), CooldownBucket.all
    )

    assert not cooldown._cache

    r_1 = await cooldown.get_bucket(1, 1)
    assert isinstance(r_1, _HashableArguments)

    # Test both specific and global clearing
    _bucket: StaticTimesPer = cooldown._get_cooldown_for_bucket(r_1)
    assert isinstance(_bucket, StaticTimesPer)
    assert cooldown._cache

    cooldown.clear(r_1)
    assert not cooldown._cache

    _bucket_2: StaticTimesPer = cooldown._get_cooldown_for_bucket(r_1)
    assert isinstance(_bucket_2, StaticTimesPer)
    assert cooldown._cache

    cooldown.clear()
    assert not cooldown._cache

    # Test 'in-use' buckets arent cleared
    _bucket_3: StaticTimesPer = cooldown._get_cooldown_for_bucket(r_1)
    assert isinstance(_bucket_3, StaticTimesPer)
    assert cooldown._cache

    assert not _bucket_3.has_cooldown
    _bucket_3.current -= 1
    assert _bucket_3.has_cooldown

    cooldown.clear()
    assert cooldown._cache


@pytest.mark.asyncio
async def test_static_remaining():
    @static_cooldown(2, datetime.time(hour=3, minute=30, second=1), CooldownBucket.all)
    async def test():
        pass

    _cooldown: StaticCooldown = getattr(test, "_cooldowns")[0]
    assert await _cooldown.remaining_calls() == 2
    await test()
    assert await _cooldown.remaining_calls() == 1
    await test()
    assert await _cooldown.remaining_calls() == 0
    with pytest.raises(CallableOnCooldown):
        await test()


@pytest.mark.asyncio
@freeze_time("2023-02-14 03:30:00", tick=True)
async def test_static_bucket_cleaner():
    # We have like 5 seconds to get this right
    @static_cooldown(2, datetime.time(hour=3, minute=30, second=1), CooldownBucket.all)
    async def test():
        pass

    _cooldown: StaticCooldown = getattr(test, "_cooldowns")[0]
    _cooldown._cache_clean_eagerness = 1
    assert not _cooldown._cache
    await test()
    assert _cooldown._cache
    await asyncio.sleep(2)
    assert not _cooldown._cache


@pytest.mark.asyncio
async def test_static_shared_cooldowns():
    define_shared_static_cooldown(
        1,
        datetime.time(hour=3, minute=30, second=1),
        CooldownBucket.all,
        cooldown_id="r_1",
    )

    @shared_cooldown("r_1")
    async def test_1(*args, **kwargs):
        return 1

    @shared_cooldown("r_1")
    async def test_2(*args, **kwargs):
        return 2

    assert await test_1(1, 2) == 1
    assert await test_2(2, 1) == 2

    with pytest.raises(CallableOnCooldown):
        await test_1(2, 1)

    with pytest.raises(CallableOnCooldown):
        await test_1(1, 2)

    with pytest.raises(CallableOnCooldown):
        await test_2(1, 2)

    @shared_cooldown("r_1")
    async def test_3(*args, **kwargs):
        return 3

    with pytest.raises(CallableOnCooldown):
        await test_3(1, 2)

    with pytest.raises(NonExistent):

        @shared_cooldown("r_2")
        async def test_4():
            pass


@pytest.mark.asyncio
async def test_get_static_times_per():
    @static_cooldown(2, datetime.time(hour=3, minute=30, second=1), CooldownBucket.all)
    async def test():
        pass

    _cooldown: StaticCooldown = getattr(test, "_cooldowns")[0]

    assert _cooldown.get_cooldown_times_per(await _cooldown.get_bucket()) is None
    await test()
    assert _cooldown.get_cooldown_times_per(await _cooldown.get_bucket()) is not None


def test_shared_crossover():
    define_shared_static_cooldown(
        1, datetime.time(second=1), CooldownBucket.all, cooldown_id="test"
    )

    with pytest.raises(CooldownAlreadyExists):
        define_shared_static_cooldown(
            2, datetime.time(second=1), CooldownBucket.all, cooldown_id="test"
        )

    define_shared_static_cooldown(
        1, datetime.time(second=1), CooldownBucket.all, cooldown_id="test2"
    )

    define_shared_cooldown(1, 1, CooldownBucket.all, cooldown_id="test3")

    with pytest.raises(CooldownAlreadyExists):
        define_shared_cooldown(1, 1, CooldownBucket.all, cooldown_id="test")

    with pytest.raises(CooldownAlreadyExists):
        define_shared_cooldown(1, 1, CooldownBucket.all, cooldown_id="test3")
