import datetime


def _utc_now() -> datetime.datetime:
    """https://github.com/Skelmis/Function-Cooldowns/issues/15"""
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _utc_from_timestamp(timestamp) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
