from collections import namedtuple

from .buckets import CooldownBucket, SlashBucket
from .protocols import CooldownBucketProtocol
from .cooldown import Cooldown, cooldown
from .cooldown_times_per import CooldownTimesPer
from .exceptions import CallableOnCooldown, NoRegisteredCooldowns, UnknownBucket
from .utils import get_remaining_calls

__all__ = (
    "CooldownBucket",
    "SlashBucket",
    "Cooldown",
    "cooldown",
    "CooldownTimesPer",
    "CooldownBucketProtocol",
    "CallableOnCooldown",
    "NoRegisteredCooldowns",
    "get_remaining_calls",
    "UnknownBucket",
)
__version__ = "1.2.1"
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(major=1, minor=2, micro=1, releaselevel="final", serial=0)
