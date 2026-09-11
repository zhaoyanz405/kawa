# tests/conftest.py
from contextlib import chdir

import pytest


@pytest.fixture
def tmp_cwd(tmp_path):
    with chdir(tmp_path):
        yield tmp_path
