import pytest

from cooldowns import cooldown, CooldownBucket, utils, Cooldown
from cooldowns.exceptions import (
    CallableOnCooldown,
    NoRegisteredCooldowns,
    NonExistent,
    CooldownAlreadyExists,
)
from cooldowns.utils import (
    shared_cooldown_refs,
    define_shared_cooldown,
    get_shared_cooldown,
)


@pytest.mark.asyncio
async def test_remaining_singluar():
    @cooldown(1, 1, CooldownBucket.all)
    async def test():
        pass

    assert await utils.get_remaining_calls(test) == 1
    await test()
    assert await utils.get_remaining_calls(test) == 0
    with pytest.raises(CallableOnCooldown):
        await test()

    @cooldown(5, 1, CooldownBucket.all)
    async def test_2():
        pass

    assert await utils.get_remaining_calls(test_2) == 5
    await test_2()
    assert await utils.get_remaining_calls(test_2) == 4


@pytest.mark.asyncio
async def test_remaining_multiple():
    @cooldown(3, 5, CooldownBucket.all)
    @cooldown(5, 10, CooldownBucket.all)
    async def test():
        pass

    assert await utils.get_remaining_calls(test) == 3


@pytest.mark.asyncio
async def test_reset_cooldowns():
    @cooldown(1, 30, CooldownBucket.all)
    async def test():
        pass

    _cooldown: Cooldown = getattr(test, "_cooldowns")[0]

    await test()
    assert _cooldown._cache
    assert await utils.get_remaining_calls(test) == 0

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

    bucket_1 = await _cooldown.get_bucket(1)
    bucket_2 = await _cooldown.get_bucket(2)
    assert bucket_1 in _cooldown._cache
    assert bucket_2 in _cooldown._cache

    await utils.reset_bucket(test, 2)

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

    utils.reset_cooldown(2)

    assert _cooldown_1._cache
    assert not _cooldown_2._cache

    with pytest.raises(NonExistent):
        utils.reset_cooldown(3)


@pytest.mark.asyncio
async def test_get_cooldown():
    @cooldown(1, 30, CooldownBucket.args, cooldown_id=2)
    @cooldown(1, 30, CooldownBucket.kwargs, cooldown_id=1)
    async def test(var, *, bar):
        pass

    _cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]
    _cooldown_2: Cooldown = getattr(test, "_cooldowns")[1]

    r_1 = utils.get_cooldown(test, 1)
    assert r_1 is _cooldown_1

    r_2 = utils.get_cooldown(test, 2)
    assert r_2 is _cooldown_2

    with pytest.raises(NonExistent):
        utils.get_cooldown(test, 3)


def test_define_cooldown():
    assert not utils.shared_cooldown_refs
    define_shared_cooldown(1, 1, CooldownBucket.all, cooldown_id="r_1")
    assert utils.shared_cooldown_refs

    with pytest.raises(CooldownAlreadyExists):
        define_shared_cooldown(1, 2, CooldownBucket.args, cooldown_id="r_1")


def test_get_shared_cooldown():
    define_shared_cooldown(1, 1, CooldownBucket.all, cooldown_id="r_1")

    r_1 = get_shared_cooldown("r_1")
    assert isinstance(r_1, Cooldown)
    assert r_1.cooldown_id == "r_1"


def test_missing_get_shared_cooldown():
    with pytest.raises(NonExistent):
        get_shared_cooldown("r_2")
