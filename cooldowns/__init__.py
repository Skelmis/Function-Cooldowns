from collections import namedtuple

from .buckets import CooldownBucket, SlashBucket
from .protocols import CooldownBucketProtocol
from .cooldown import Cooldown, cooldown, shared_cooldown
from .cooldown_times_per import CooldownTimesPer
from .exceptions import (
    CallableOnCooldown,
    NoRegisteredCooldowns,
    UnknownBucket,
    CooldownAlreadyExists,
)
from .utils import (
    get_remaining_calls,
    reset_cooldown,
    reset_cooldowns,
    reset_bucket,
    get_cooldown,
    define_shared_cooldown,
)

__all__ = (
    "CooldownBucket",
    "SlashBucket",
    "Cooldown",
    "cooldown",
    "shared_cooldown",
    "CooldownTimesPer",
    "CooldownBucketProtocol",
    "CallableOnCooldown",
    "NoRegisteredCooldowns",
    "CooldownAlreadyExists",
    "get_remaining_calls",
    "UnknownBucket",
    "reset_cooldowns",
    "reset_bucket",
    "reset_cooldown",
    "get_cooldown",
    "define_shared_cooldown",
)
__version__ = "1.3.1"
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(major=1, minor=3, micro=1, releaselevel="final", serial=0)
