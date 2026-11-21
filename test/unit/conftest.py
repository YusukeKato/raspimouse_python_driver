"""Shared fixtures for unit tests."""

import sys
import types

import pytest

CHIP_HANDLE = 7


class FakeLgpioError(Exception):
    pass


class FakeLgpio(types.ModuleType):
    """Implements the part of the lgpio API used by the backend."""

    error = FakeLgpioError
    chip_handle = CHIP_HANDLE
    SET_PULL_UP = 32

    def __init__(self):
        super().__init__('lgpio')
        self.calls = []
        self.busy_pins = set()
        # Levels returned by gpio_read(); unknown pins read high (pulled up).
        self.levels = {}
        # GPIOs with running software PWM.
        self.pwm_active = set()

    def gpiochip_open(self, gpiochip):
        self.calls.append(('gpiochip_open', gpiochip))
        return CHIP_HANDLE

    def gpiochip_close(self, handle):
        self.calls.append(('gpiochip_close', handle))
        return 0

    def gpio_claim_output(self, handle, gpio, level=0, lFlags=0):
        if gpio in self.busy_pins:
            raise FakeLgpioError("'GPIO busy'")
        self.calls.append(('gpio_claim_output', handle, gpio, level))
        return 0

    def gpio_claim_input(self, handle, gpio, lFlags=0):
        if gpio in self.busy_pins:
            raise FakeLgpioError("'GPIO busy'")
        self.calls.append(('gpio_claim_input', handle, gpio, lFlags))
        return 0

    def gpio_read(self, handle, gpio):
        return self.levels.get(gpio, 1)

    def tx_pwm(self, handle, gpio, pwm_frequency, pwm_duty_cycle,
               pulse_offset=0, pulse_cycles=0):
        # Like lgpio 0.2: "off" for a GPIO without active PWM is an error.
        if pwm_frequency == 0 and gpio not in self.pwm_active:
            raise FakeLgpioError("'bad PWM micros'")
        self.calls.append(('tx_pwm', handle, gpio, pwm_frequency, pwm_duty_cycle))
        if pwm_frequency == 0:
            self.pwm_active.discard(gpio)
        else:
            self.pwm_active.add(gpio)
        return 0

    def gpio_write(self, handle, gpio, level):
        self.calls.append(('gpio_write', handle, gpio, level))
        return 0

    def gpio_free(self, handle, gpio):
        self.calls.append(('gpio_free', handle, gpio))
        return 0


@pytest.fixture
def lgpio(monkeypatch):
    fake = FakeLgpio()
    monkeypatch.setitem(sys.modules, 'lgpio', fake)
    return fake
