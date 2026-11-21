"""
Differential drive kinematics of Raspberry Pi Mouse.

Pure functions without hardware access, so they can also be used on their
own (e.g. in a ROS 2 node or a simulator). Units: m, m/s, rad, rad/s, Hz.
Frequencies are step pulse frequencies of the wheels; positive is forward.
"""

import math
from typing import NamedTuple

from .config import DriveConfig


class Pose2D(NamedTuple):
    """Position [m] and heading [rad, -pi..pi] in the odometry frame."""

    x: float
    y: float
    theta: float


def meters_per_pulse(config: DriveConfig) -> float:
    """Return the distance a wheel travels per step pulse [m]."""
    return math.pi * config.wheel_diameter_m / config.pulses_per_revolution


def velocity_to_wheel_frequencies(linear: float, angular: float,
                                  config: DriveConfig) -> tuple[float, float]:
    """
    Return the (left, right) wheel frequencies [Hz] for a body velocity.

    :param linear: forward velocity [m/s].
    :param angular: counterclockwise angular velocity [rad/s].
    """
    half_tread_speed = angular * config.wheel_tread_m / 2.0
    mpp = meters_per_pulse(config)
    return (linear - half_tread_speed) / mpp, (linear + half_tread_speed) / mpp


def wheel_frequencies_to_velocity(left_hz: float, right_hz: float,
                                  config: DriveConfig) -> tuple[float, float]:
    """Return the (linear [m/s], angular [rad/s]) body velocity for wheel frequencies."""
    mpp = meters_per_pulse(config)
    left, right = left_hz * mpp, right_hz * mpp
    return (left + right) / 2.0, (right - left) / config.wheel_tread_m


def limit_wheel_frequencies(left_hz: float, right_hz: float,
                            max_hz: float) -> tuple[float, float]:
    """Scale both frequencies down together so that neither exceeds ``max_hz``."""
    fastest = max(abs(left_hz), abs(right_hz))
    if fastest <= max_hz:
        return left_hz, right_hz
    scale = max_hz / fastest
    return left_hz * scale, right_hz * scale


def normalize_angle(angle: float) -> float:
    """Wrap an angle to -pi..pi."""
    return math.atan2(math.sin(angle), math.cos(angle))


def integrate_pose(pose: Pose2D, left_pulses: float, right_pulses: float,
                   config: DriveConfig) -> Pose2D:
    """
    Move ``pose`` by the signed pulses the wheels made since the last update.

    Uses the heading in the middle of the step, which is more accurate on
    curves than the heading at its end (rt-net/raspimouse2).
    """
    mpp = meters_per_pulse(config)
    left = left_pulses * mpp * config.odometry_scale_left
    right = right_pulses * mpp * config.odometry_scale_right
    distance = (left + right) / 2.0
    rotation = (right - left) / config.wheel_tread_m
    heading = pose.theta + rotation / 2.0
    return Pose2D(pose.x + distance * math.cos(heading),
                  pose.y + distance * math.sin(heading),
                  normalize_angle(pose.theta + rotation))
