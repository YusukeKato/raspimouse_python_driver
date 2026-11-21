import os

import pytest


@pytest.fixture(autouse=True)
def _require_hardware():
    if os.environ.get('RASPIMOUSE_HARDWARE_TEST') != '1':
        pytest.skip('set RASPIMOUSE_HARDWARE_TEST=1 to run tests on a real Raspberry Pi Mouse')
