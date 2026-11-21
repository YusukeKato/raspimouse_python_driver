"""
Hardware configuration of Raspberry Pi Mouse on Raspberry Pi 4.

Default values follow the wiring of Raspberry Pi Mouse. All pin numbers are
BCM GPIO numbers (line offsets of the GPIO chip).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LightSensorChannel:
    """One light sensor: an emitter LED driven by GPIO and an MCP3204 ADC channel."""

    emitter_pin: int
    adc_channel: int


@dataclass(frozen=True)
class LightSensorConfig:
    """Light sensors (4 channels) read through the MCP3204 on SPI."""

    right_front: LightSensorChannel = LightSensorChannel(emitter_pin=27, adc_channel=2)
    right: LightSensorChannel = LightSensorChannel(emitter_pin=22, adc_channel=3)
    left: LightSensorChannel = LightSensorChannel(emitter_pin=4, adc_channel=0)
    left_front: LightSensorChannel = LightSensorChannel(emitter_pin=17, adc_channel=1)
    # Time to wait after turning on an emitter before sampling the ADC [s].
    settle_time_s: float = 30e-6
    spi_bus: int = 0
    spi_chip_select: int = 0
    spi_max_speed_hz: int = 1_000_000


@dataclass(frozen=True)
class MotorChannelConfig:
    """One stepper motor driver channel."""

    # Channel number of the sysfs PWM chip that generates step pulses.
    pwm_channel: int
    # GPIO muxed to the PWM peripheral by the device tree overlay (informational).
    clock_pin: int
    direction_pin: int
    # Level of the direction pin when the frequency is positive (forward).
    forward_level: bool


@dataclass(frozen=True)
class MotorConfig:
    """Left and right stepper motors and the shared motor power (enable) pin."""

    left: MotorChannelConfig = MotorChannelConfig(
        pwm_channel=0, clock_pin=12, direction_pin=16, forward_level=False)
    right: MotorChannelConfig = MotorChannelConfig(
        pwm_channel=1, clock_pin=13, direction_pin=6, forward_level=True)
    enable_pin: int = 5
    pwm_chip: int = 0
    # Frequencies whose absolute value is below this are treated as 0 (stop) [Hz].
    min_frequency_hz: int = 5
    max_frequency_hz: int = 10_000


@dataclass(frozen=True)
class BuzzerConfig:
    """
    Buzzer driven by software PWM.

    GPIO19 shares the hardware PWM channel with GPIO13 (right motor) on
    BCM2711, so it is used as a plain GPIO with software PWM instead.
    """

    pin: int = 19
    # Upper limit of lgpio software PWM.
    max_frequency_hz: int = 10_000


@dataclass(frozen=True)
class PulseCounterConfig:
    """Pulse counters of Raspberry Pi Mouse V3 on I2C (16 bit, one per motor)."""

    i2c_bus: int = 1
    left_address: int = 0x10
    right_address: int = 0x11
    msb_register: int = 0x10
    lsb_register: int = 0x11


@dataclass(frozen=True)
class BatteryConfig:
    """
    Battery voltage monitor of Raspberry Pi Mouse V3.

    The input voltage after the main switch (the battery, or the AC adapter
    when powered from it) is divided by R1 (51 kOhm) and R2 (10 kOhm) and read
    by the A/D converter (MCP3208) on the light sensor SPI bus.
    """

    adc_channel: int = 4
    # (R1 + R2) / R2
    divider_ratio: float = (51.0 + 10.0) / 10.0
    # Reference voltage of the A/D converter (the 3.3 V rail).
    reference_voltage: float = 3.3


@dataclass(frozen=True)
class DriveConfig:
    """
    Differential drive: geometry, limits and control loop.

    The geometry defaults are those of rt-net/raspimouse2. With them one
    pulse moves a wheel 0.377 mm, so 1 m/s is about 2653 Hz.
    """

    wheel_diameter_m: float = 0.048
    wheel_tread_m: float = 0.0925
    pulses_per_revolution: float = 400.0
    # Corrections of the travelled distance per wheel, used for odometry only.
    odometry_scale_left: float = 1.0
    odometry_scale_right: float = 1.0
    # No wheel goes faster than this; both are scaled down together so that
    # the path keeps its curvature. 1000 Hz is about 0.38 m/s.
    max_wheel_frequency_hz: float = 1000.0
    # How fast a wheel frequency may change. Larger steps make stepper motors lose steps.
    max_wheel_acceleration_hz_s: float = 2000.0
    # Slow down to a stop when no velocity command arrives for this long; 0 disables.
    command_timeout_s: float = 0.5
    control_rate_hz: float = 50.0


@dataclass(frozen=True)
class RaspiMouseConfig:
    """Complete hardware configuration."""

    # GPIO chip number (/dev/gpiochipN).
    gpio_chip: int = 0
    led_pins: tuple[int, ...] = (25, 24, 23, 18)
    # Switches 0-2 (rtswitch0-2 of the kernel driver). Pulled up; pressed reads low.
    switch_pins: tuple[int, ...] = (20, 26, 21)
    light_sensors: LightSensorConfig = field(default_factory=LightSensorConfig)
    motors: MotorConfig = field(default_factory=MotorConfig)
    buzzer: BuzzerConfig = field(default_factory=BuzzerConfig)
    pulse_counters: PulseCounterConfig = field(default_factory=PulseCounterConfig)
    # Set False on models without pulse counters (before V3).
    has_pulse_counters: bool = True
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    # Set False on models without the battery voltage monitor (before V3).
    has_battery_monitor: bool = True
    drive: DriveConfig = field(default_factory=DriveConfig)
