from collections import namedtuple

from .buckets import CooldownBucket, SlashBucket
from .protocols import CooldownBucketProtocol
from .cooldown import Cooldown, cooldown, shared_cooldown
from .static_cooldown import StaticCooldown, static_cooldown
from .cooldown_times_per import CooldownTimesPer
from .static_times_per import StaticTimesPer
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
    get_shared_cooldown,
    define_shared_static_cooldown,
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
    "get_shared_cooldown",
    "StaticTimesPer",
    "StaticCooldown",
    "static_cooldown",
    "define_shared_static_cooldown",
)

__version__ = "1.7.0"
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(major=1, minor=7, micro=0, releaselevel="final", serial=0)
