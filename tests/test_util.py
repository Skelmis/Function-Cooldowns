import pytest

from cooldowns import cooldown, CooldownBucket, utils, Cooldown
from cooldowns.exceptions import CallableOnCooldown, NoRegisteredCooldowns


@pytest.mark.asyncio
async def test_remaining_singluar():
    @cooldown(1, 1, CooldownBucket.all)
    async def test():
        pass

    assert utils.get_remaining_calls(test) == 1
    await test()
    assert utils.get_remaining_calls(test) == 0
    with pytest.raises(CallableOnCooldown):
        await test()

    @cooldown(5, 1, CooldownBucket.all)
    async def test_2():
        pass

    assert utils.get_remaining_calls(test_2) == 5
    await test_2()
    assert utils.get_remaining_calls(test_2) == 4


@pytest.mark.asyncio
async def test_remaining_multiple():
    @cooldown(3, 5, CooldownBucket.all)
    @cooldown(5, 10, CooldownBucket.all)
    async def test():
        pass

    assert utils.get_remaining_calls(test) == 3


@pytest.mark.asyncio
async def test_reset_cooldowns():
    @cooldown(1, 30, CooldownBucket.all)
    async def test():
        pass

    _cooldown: Cooldown = getattr(test, "_cooldowns")[0]

    await test()
    assert _cooldown._cache
    assert utils.get_remaining_calls(test) == 0

    utils.reset_cooldowns(test)
    assert not _cooldown._cache


@pytest.mark.asyncio
async def test_reset_buckets():
    @cooldown(1, 30, CooldownBucket.args)
    async def test(var):
        pass

    _cooldown: Cooldown = getattr(test, "_cooldowns")[0]

    await test(1)
    await test(2)

    assert len(_cooldown._cache.keys()) == 2

    bucket_1 = _cooldown.get_bucket(1)
    bucket_2 = _cooldown.get_bucket(2)
    assert bucket_1 in _cooldown._cache
    assert bucket_2 in _cooldown._cache

    utils.reset_bucket(test, 2)

    assert bucket_1 in _cooldown._cache
    assert bucket_2 not in _cooldown._cache


@pytest.mark.asyncio
async def test_reset_cooldown():
    @cooldown(1, 30, CooldownBucket.args, cooldown_id=2)
    @cooldown(1, 30, CooldownBucket.kwargs, cooldown_id=1)
    async def test(var, *, bar):
        pass

    _cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]
    _cooldown_2: Cooldown = getattr(test, "_cooldowns")[1]

    assert _cooldown_1.cooldown_id == 1
    assert _cooldown_2.cooldown_id == 2

    await test(1, bar=2)

    assert _cooldown_1._cache
    assert _cooldown_2._cache

    utils.reset_cooldown(test, 2)

    assert _cooldown_1._cache
    assert not _cooldown_2._cache
