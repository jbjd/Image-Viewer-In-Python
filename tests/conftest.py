import os

import pytest


@pytest.fixture
def working_dir() -> str:
    return os.path.dirname(__file__)
