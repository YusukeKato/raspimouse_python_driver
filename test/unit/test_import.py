import importlib
from pathlib import Path
import pkgutil
import subprocess
import sys

import raspimouse_python_driver

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def test_all_modules_import():
    for module in pkgutil.walk_packages(raspimouse_python_driver.__path__,
                                        prefix='raspimouse_python_driver.'):
        importlib.import_module(module.name)


def test_no_ros_and_no_hardware_modules_imported():
    # Importing the package must not require ROS or the hardware libraries.
    # Checked in a fresh interpreter so that pytest plugins do not interfere.
    code = (
        'import sys, raspimouse_python_driver, raspimouse_python_driver.hal.linux;'
        "print(' '.join(n for n in ('rclpy', 'ament_index_python', 'lgpio')"
        ' if n in sys.modules))'
    )
    result = subprocess.run([sys.executable, '-c', code], cwd=PACKAGE_ROOT,
                            capture_output=True, text=True, check=True)
    assert result.stdout.strip() == ''
