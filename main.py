from cooldowns import (
    get_cooldown_state,
    cooldown,
    CooldownBucket,
    load_cooldown_state,
    Cooldown,
    CooldownTimesPer,
)
from cooldowns.buckets import _HashableArguments


@cooldown(1, 1, bucket=CooldownBucket.all)
@cooldown(1, 5, bucket=CooldownBucket.args)
async def test():
    pass


_cooldown_1: Cooldown = getattr(test, "_cooldowns")[0]
bucket = _cooldown_1.get_bucket(1)
_cooldown_1._cache[bucket] = _cooldown_1._get_cooldown_for_bucket(bucket)

ctp: CooldownTimesPer = _cooldown_1._cache[bucket]
ctp.current = "lol"


async def load_to():
    pass


state = get_cooldown_state(test)
print(state)
load_cooldown_state(load_to, state)

# Look at deepcopying the queue to convert to a list to pickle
# then convert back from a list and repopulate a queue
#
# Just make sure the queue order stays the same

# Also need a way to handle the call_laters
# such that they queue gets de-populated correctly on load
# In theory can clear all items from queue older then utcnow() + time_period
