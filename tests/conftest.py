import pytest

from cooldowns import utils


@pytest.fixture(autouse=True, scope="function")
def reset_refs():
    utils.shared_cooldown_refs = {}
