"""Do not touch the switches while this runs: all must read released."""

import pytest

from raspimouse_python_driver import RaspiMouse


@pytest.mark.hardware
def test_switches_read_released_when_untouched():
    with RaspiMouse() as mouse:
        for _ in range(100):
            assert [sw.is_pressed() for sw in mouse.switches] == [False, False, False]
