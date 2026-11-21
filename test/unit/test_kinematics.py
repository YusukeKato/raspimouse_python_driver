import math

import pytest

from raspimouse_python_driver.config import DriveConfig
from raspimouse_python_driver.kinematics import (
    integrate_pose,
    limit_wheel_frequencies,
    meters_per_pulse,
    normalize_angle,
    Pose2D,
    velocity_to_wheel_frequencies,
    wheel_frequencies_to_velocity,
)

CONFIG = DriveConfig()
HZ_PER_M_S = 400 / (math.pi * 0.048)  # about 2653 Hz for 1 m/s


def test_meters_per_pulse():
    assert meters_per_pulse(CONFIG) == pytest.approx(0.000377, abs=1e-6)


def test_matches_rt_net_raspimouse2_formula():
    # vel_wheel = (v -/+ w * tread / 2) / (D / 2); freq = vel_wheel / (2 pi) * 400
    v, w = 0.2, 1.5
    left = (v - w * 0.0925 / 2) / (0.048 / 2) / (2 * math.pi) * 400
    right = (v + w * 0.0925 / 2) / (0.048 / 2) / (2 * math.pi) * 400
    assert velocity_to_wheel_frequencies(v, w, CONFIG) == pytest.approx((left, right))


def test_forward_and_spin():
    assert velocity_to_wheel_frequencies(0.1, 0, CONFIG) == pytest.approx(
        (0.1 * HZ_PER_M_S, 0.1 * HZ_PER_M_S))
    left, right = velocity_to_wheel_frequencies(0, 1.0, CONFIG)
    assert left == pytest.approx(-right)
    assert right > 0  # counterclockwise: the right wheel goes forward


def test_round_trip():
    assert wheel_frequencies_to_velocity(
        *velocity_to_wheel_frequencies(0.15, -0.7, CONFIG), CONFIG) == pytest.approx((0.15, -0.7))


def test_limit_keeps_the_ratio():
    assert limit_wheel_frequencies(2000, 1000, 1000) == (1000, 500)
    assert limit_wheel_frequencies(-500, 300, 1000) == (-500, 300)


def test_integrate_straight():
    pose = integrate_pose(Pose2D(0, 0, 0), 400, 400, CONFIG)
    assert pose == pytest.approx((math.pi * 0.048, 0, 0))


def test_integrate_quarter_turn_in_place():
    pulses = (math.pi / 2) * (0.0925 / 2) / meters_per_pulse(CONFIG)
    pose = integrate_pose(Pose2D(0, 0, 0), -pulses, pulses, CONFIG)
    assert pose == pytest.approx((0, 0, math.pi / 2))


def test_integrate_uses_the_heading():
    pose = integrate_pose(Pose2D(1, 2, math.pi / 2), 400, 400, CONFIG)
    assert pose == pytest.approx((1, 2 + math.pi * 0.048, math.pi / 2))


def test_odometry_scale():
    config = DriveConfig(odometry_scale_left=1.1, odometry_scale_right=1.1)
    assert integrate_pose(Pose2D(0, 0, 0), 400, 400, config).x == pytest.approx(
        1.1 * math.pi * 0.048)


def test_normalize_angle():
    assert normalize_angle(3 * math.pi / 2) == pytest.approx(-math.pi / 2)
