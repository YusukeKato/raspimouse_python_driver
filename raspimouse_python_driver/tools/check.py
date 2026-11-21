"""
Check that the Raspberry Pi is set up for this driver.

Only reads the system and prints how to fix each problem; it never changes
anything. Run as ``raspimouse-cli check``.
"""

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import re

from ..board import is_raspberry_pi4, read_model

OK = 'OK'
WARN = 'WARN'
FAIL = 'FAIL'

PWM_OVERLAY = 'dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4'
UDEV_RULE = '99-raspimouse-pwm.rules'


@dataclass(frozen=True)
class CheckResult:
    """Result of one check. ``fix`` tells the user what to run."""

    level: str
    message: str
    fix: str = ''


def _active_lines(text: str) -> list[str]:
    """Return the config.txt lines that are not comments."""
    return [s for s in (line.strip() for line in text.splitlines())
            if s and not s.startswith('#')]


def _lgpio_installed() -> bool:
    return importlib.util.find_spec('lgpio') is not None


def check_board(root: Path) -> CheckResult:
    """Check that the board is a Raspberry Pi 4, the only supported board."""
    model = read_model(root / 'proc/device-tree/model')
    if is_raspberry_pi4(model):
        return CheckResult(OK, model)
    return CheckResult(FAIL, f'not a Raspberry Pi 4: {model or "unknown board"}',
                       'This driver supports Raspberry Pi 4 only.')


def check_lgpio() -> CheckResult:
    """Check that lgpio, the only Python dependency, is installed."""
    if _lgpio_installed():
        return CheckResult(OK, 'python3-lgpio is installed')
    return CheckResult(FAIL, 'python3-lgpio is not installed', 'sudo apt install python3-lgpio')


def check_rtmouse_module(root: Path) -> CheckResult:
    """Check that the official kernel module, which drives the same hardware, is not loaded."""
    if (root / 'sys/module/rtmouse').exists():
        return CheckResult(
            FAIL, 'the rtmouse kernel module is loaded (it uses the same hardware)',
            'sudo rmmod rtmouse   # and do not run its build_install.bash again')
    return CheckResult(OK, 'the rtmouse kernel module is not loaded')


def check_config_txt(path: Path) -> list[CheckResult]:
    """Check the settings in /boot/firmware/config.txt."""
    try:
        lines = _active_lines(path.read_text())
    except OSError as e:
        return [CheckResult(FAIL, f'cannot read {path}: {e}')]
    results = []
    reboot = '\nsudo reboot'

    anyspi = [line for line in lines if re.match(r'dtoverlay=anyspi:.*mcp320', line)]
    if anyspi:
        results.append(CheckResult(
            FAIL, f'{path}: "{anyspi[0]}" (set up for the rtmouse kernel module) '
                  'keeps /dev/spidev0.0 from being created',
            f"sudo sed -i 's/^dtoverlay=anyspi:spi0-0/#&/' {path}{reboot}"))
    else:
        results.append(CheckResult(OK, f'{path}: no anyspi overlay for the rtmouse module'))

    for setting, purpose in (('dtparam=spi=on', 'SPI (light sensors)'),
                             ('dtparam=i2c_arm=on', 'I2C (pulse counters)')):
        if setting in lines:
            results.append(CheckResult(OK, f'{path}: {setting}'))
        else:
            results.append(CheckResult(
                FAIL, f'{path}: {setting} is missing ({purpose})',
                f"echo '{setting}' | sudo tee -a {path}{reboot}"))

    pwm = [line for line in lines if line.startswith('dtoverlay=pwm-2chan')]
    if any('pin=12' in line and 'pin2=13' in line for line in pwm):
        results.append(CheckResult(OK, f'{path}: pwm-2chan overlay on GPIO12/13'))
    else:
        results.append(CheckResult(
            FAIL, f'{path}: pwm-2chan overlay on GPIO12/13 is missing (motors)',
            f"echo '{PWM_OVERLAY}' | sudo tee -a {path}{reboot}"))

    if 'dtparam=i2c_baudrate=62500' in lines:
        results.append(CheckResult(OK, f'{path}: dtparam=i2c_baudrate=62500'))
    else:
        results.append(CheckResult(
            WARN, f'{path}: dtparam=i2c_baudrate=62500 is recommended for the pulse counters',
            f"echo 'dtparam=i2c_baudrate=62500' | sudo tee -a {path}{reboot}"))
    return results


def check_devices(root: Path) -> list[CheckResult]:
    """Check the device files used through lgpio."""
    results = []
    for name, purpose, missing_fix in (
            ('dev/gpiochip0', 'GPIO', ''),
            ('dev/spidev0.0', 'SPI',
             'enable dtparam=spi=on and comment out the anyspi overlay, then reboot'),
            ('dev/i2c-1', 'I2C', 'enable dtparam=i2c_arm=on, then reboot')):
        path = root / name
        device = f'/{name}'
        if not path.exists():
            results.append(CheckResult(FAIL, f'{device} ({purpose}) does not exist', missing_fix))
        elif not os.access(path, os.R_OK | os.W_OK):
            results.append(CheckResult(
                FAIL, f'{device} ({purpose}) is not accessible without root',
                'sudo usermod -aG dialout $USER   # then log in again'))
        else:
            results.append(CheckResult(OK, f'{device} ({purpose}) is accessible'))
    return results


def check_pwm(root: Path) -> list[CheckResult]:
    """Check hardware PWM for the motors."""
    chip = root / 'sys/class/pwm/pwmchip0'
    if not chip.is_dir():
        return [CheckResult(FAIL, '/sys/class/pwm/pwmchip0 does not exist (motors)',
                            f'add {PWM_OVERLAY} to config.txt, then reboot')]
    if not os.access(chip / 'export', os.W_OK):
        return [CheckResult(
            FAIL, '/sys/class/pwm/pwmchip0 is not writable without root (motors)',
            f'sudo cp config/{UDEV_RULE} /etc/udev/rules.d/\n'
            'sudo udevadm control --reload-rules && sudo udevadm trigger\n'
            'sudo usermod -aG gpio $USER   # if not a member, then log in again')]
    return [CheckResult(OK, '/sys/class/pwm/pwmchip0 is writable')]


def run_checks(root: Path = Path('/'),
               config_txt: Path = Path('/boot/firmware/config.txt')) -> list[CheckResult]:
    """Run every check. ``root`` is prefixed to /proc, /sys and /dev (for tests)."""
    return [
        check_board(root),
        check_lgpio(),
        check_rtmouse_module(root),
        *check_config_txt(config_txt),
        *check_devices(root),
        *check_pwm(root),
    ]


def format_results(results: list[CheckResult]) -> str:
    """Format results for the terminal, with fixes indented below problems."""
    lines = []
    for result in results:
        lines.append(f'[{result.level:^4}] {result.message}')
        for fix_line in result.fix.splitlines():
            lines.append(f'       {fix_line}')
    failures = sum(r.level == FAIL for r in results)
    warnings = sum(r.level == WARN for r in results)
    if failures or warnings:
        lines.append(f'\n{failures} problem(s), {warnings} warning(s). '
                     'Run the commands above, then check again.')
    else:
        lines.append('\nAll checks passed.')
    return '\n'.join(lines)
