"""
Velocity control and odometry of Raspberry Pi Mouse.

:class:`Drive` takes body velocity commands (like ``cmd_vel`` in ROS),
converts them to wheel step frequencies, ramps the motors to them and keeps
an odometry estimate. A background control loop does the work; it starts on
the first call of :meth:`Drive.set_velocity` or :meth:`Drive.odometry`.
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging
import math
import threading
import time
from typing import Protocol

from .config import DriveConfig
from .devices.motor import Motors
from .exceptions import DeviceError
from .kinematics import (
    integrate_pose,
    limit_wheel_frequencies,
    Pose2D,
    velocity_to_wheel_frequencies,
    wheel_frequencies_to_velocity,
)

_logger = logging.getLogger(__name__)


class SignedCounter(Protocol):
    """Anything with ``read_signed()``, e.g. a :class:`PulseCounter`."""

    def read_signed(self) -> int:
        """Return the signed pulse count."""


@dataclass(frozen=True)
class Odometry:
    """Pose [m, rad] and body velocity [m/s, rad/s] in the odometry frame."""

    x: float
    y: float
    theta: float
    linear: float
    angular: float


def _approach(current: float, goal: float, max_step: float) -> float:
    if abs(goal - current) <= max_step:
        return goal
    return current + math.copysign(max_step, goal - current)


class Drive:
    """
    Drive Raspberry Pi Mouse by velocity commands.

    * :meth:`set_velocity` sets the target; the wheels ramp to it within
      ``max_wheel_acceleration_hz_s`` and never exceed ``max_wheel_frequency_hz``.
    * If no command arrives for ``command_timeout_s``, the robot slows down to
      a stop. Send commands repeatedly (e.g. at 10 Hz) while moving.
    * :meth:`odometry` integrates the pulse counters, or the commanded
      frequencies when there are no counters.

    The motor power is not switched here: turn it on with ``MotorPower.on()``.
    While the control loop runs, do not command the motors directly.
    Thread safe.
    """

    def __init__(self, motors: Motors, config: DriveConfig,
                 left_counter: SignedCounter | None = None,
                 right_counter: SignedCounter | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 auto_start: bool = True) -> None:
        """
        Create the controller.

        :param left_counter: pulse counter of the left wheel, or None to
            estimate odometry from the commanded frequencies (both or neither).
        :param clock: monotonic time source [s] (for tests).
        :param auto_start: start the background control loop on first use.
            With False, call :meth:`update` yourself.
        """
        if (left_counter is None) != (right_counter is None):
            raise ValueError('give both pulse counters or neither')
        self._motors = motors
        self._config = config
        self._counters = (left_counter, right_counter) if left_counter else None
        self._clock = clock
        self._auto_start = auto_start
        self._lock = threading.RLock()
        self._target = (0.0, 0.0)
        self._last_command: float | None = None
        self._applied = (0.0, 0.0)
        self._last_update: float | None = None
        self._last_counts: tuple[int, int] | None = None
        self._pose = Pose2D(0.0, 0.0, 0.0)
        self._velocity = (0.0, 0.0)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._closed = False

    def set_velocity(self, linear: float, angular: float = 0.0) -> None:
        """
        Set the target velocity.

        :param linear: forward velocity [m/s].
        :param angular: counterclockwise angular velocity [rad/s].
        """
        with self._lock:
            self._check_open()
            self._target = (float(linear), float(angular))
            self._last_command = self._clock()
        self._ensure_started()

    def stop(self) -> None:
        """Slow down to a stop, like setting a zero velocity."""
        self.set_velocity(0.0, 0.0)

    @property
    def target_velocity(self) -> tuple[float, float]:
        """Return the target (linear, angular) velocity."""
        with self._lock:
            return self._target

    @property
    def wheel_frequencies(self) -> tuple[float, float]:
        """Return the (left, right) wheel frequencies [Hz] sent to the motors."""
        with self._lock:
            return self._applied

    def odometry(self) -> Odometry:
        """Return the current odometry."""
        self._ensure_started()
        with self._lock:
            return Odometry(*self._pose, *self._velocity)

    def reset_odometry(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0) -> None:
        """Set the current pose."""
        with self._lock:
            self._pose = Pose2D(x, y, theta)

    def update(self) -> None:
        """
        Run one control cycle: watchdog, ramp, motor command and odometry.

        Called by the background loop; call it yourself with ``auto_start=False``.
        """
        with self._lock:
            if self._closed:
                return
            now = self._clock()
            dt = 0.0 if self._last_update is None else max(0.0, now - self._last_update)
            self._last_update = now
            previous = self._applied
            self._apply_watchdog(now)
            goal = limit_wheel_frequencies(
                *velocity_to_wheel_frequencies(*self._target, self._config),
                self._config.max_wheel_frequency_hz)
            step = self._config.max_wheel_acceleration_hz_s * dt
            applied = (_approach(previous[0], goal[0], step),
                       _approach(previous[1], goal[1], step))
            if applied != previous:
                self._motors.set_frequency(*applied)
                self._applied = applied
            self._update_odometry(dt, previous)

    def close(self) -> None:
        """Stop the control loop and the motors at once. Calling this more than once is allowed."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._stop_event.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=1.0)
        with self._lock:
            if self._applied != (0.0, 0.0):
                self._motors.stop()
                self._applied = (0.0, 0.0)

    def _apply_watchdog(self, now: float) -> None:
        timeout = self._config.command_timeout_s
        if (timeout > 0 and self._last_command is not None
                and now - self._last_command > timeout and self._target != (0.0, 0.0)):
            _logger.warning('no velocity command for %.2f s; stopping', timeout)
            self._target = (0.0, 0.0)

    def _update_odometry(self, dt: float, previous: tuple[float, float]) -> None:
        if self._counters is not None:
            counts = (self._counters[0].read_signed(), self._counters[1].read_signed())
            if self._last_counts is None:
                self._last_counts = counts
                return
            pulses = (counts[0] - self._last_counts[0], counts[1] - self._last_counts[1])
            self._last_counts = counts
        else:
            # Pulses sent during the last interval at the frequencies set then.
            pulses = (previous[0] * dt, previous[1] * dt)
        self._pose = integrate_pose(self._pose, *pulses, self._config)
        if dt > 0:
            self._velocity = wheel_frequencies_to_velocity(
                pulses[0] / dt, pulses[1] / dt, self._config)

    def _ensure_started(self) -> None:
        with self._lock:
            if not self._auto_start or self._thread is not None or self._closed:
                return
            self._thread = threading.Thread(
                target=self._run, name='raspimouse-drive', daemon=True)
            self._thread.start()

    def _run(self) -> None:
        period = 1.0 / self._config.control_rate_hz
        while not self._stop_event.wait(period):
            try:
                self.update()
            except Exception:
                _logger.exception('drive control cycle failed')

    def _check_open(self) -> None:
        if self._closed:
            raise DeviceError('drive is already closed')
