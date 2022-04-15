from collections import namedtuple

from .buckets import CooldownBucket
from .protocols import CooldownBucketProtocol
from .cooldown import Cooldown, cooldown
from .cooldown_times_per import CooldownTimesPer

__all__ = (
    "CooldownBucket",
    "Cooldown",
    "cooldown",
    "CooldownTimesPer",
    "CooldownBucketProtocol",
)
__version__ = "0.1.0"
VersionInfo = namedtuple("VersionInfo", "major minor micro releaselevel serial")
version_info = VersionInfo(major=0, minor=1, micro=0, releaselevel="final", serial=0)
