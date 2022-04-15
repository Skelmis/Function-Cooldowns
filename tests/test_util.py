import pytest

from cooldowns import cooldown, CooldownBucket, utils
from cooldowns.exceptions import CallableOnCooldown


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
