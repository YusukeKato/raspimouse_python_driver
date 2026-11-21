import pytest

from raspimouse_python_driver.board import is_raspberry_pi4


@pytest.mark.hardware
def test_running_on_raspberry_pi4():
    assert is_raspberry_pi4()
