import asyncio

import pytest

from cooldowns import (
    CooldownBucket,
    TriggerCooldown,
    get_cooldown
)
from cooldowns.exceptions import CallableOnCooldown


@pytest.mark.asyncio
async def test_trigger_cooldown():
    my_trigger_cooldown = TriggerCooldown(1, 0.3, CooldownBucket.all)

    @my_trigger_cooldown
    async def test_1(trigger_test = False):
        if trigger_test:
            await my_trigger_cooldown.trigger(20)
        return 1

    assert await test_1() == 1

    with pytest.raises(CallableOnCooldown):
        await test_1()

    await asyncio.sleep(0.4)

    assert await test_1(trigger_test = True)

    await asyncio.sleep(0.4)
    with pytest.raises(CallableOnCooldown):
        await test_1()

@pytest.mark.asyncio
async def test_shared_trigger_cooldown():
    my_shared_trigger_cooldown = TriggerCooldown(1, 0.3, CooldownBucket.all)

    @my_shared_trigger_cooldown
    async def test_1(*args, **kwargs):
        return 1

    @my_shared_trigger_cooldown
    async def test_2(*args, **kwargs):
        return 2

    assert await test_1() == 1

    with pytest.raises(CallableOnCooldown):
        await test_1()

    with pytest.raises(CallableOnCooldown):
        await test_2()

@pytest.mark.asyncio
async def test_trigger_cooldown_with_id():
    my_trigger_cooldown = TriggerCooldown(1, 0.3, CooldownBucket.all,
                                          cooldown_id= "normal_cooldown_id",
                                          trigger_cooldown_id= "trigger_cooldown_id")

    @my_trigger_cooldown
    async def test_1(*args, **kwargs):
        try:
            get_cooldown(test_1, "normal_cooldown_id")
            get_cooldown(test_1, "trigger_cooldown_id")
            return 1
        except Exception:
            return 0

    assert await test_1() == 1

    with pytest.raises(CallableOnCooldown):
        await test_1()
