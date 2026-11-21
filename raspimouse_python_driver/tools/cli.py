"""
Command line tool to check each device by hand.

Run as ``raspimouse-cli`` or ``python3 -m raspimouse_python_driver.tools.cli``.
"""

import argparse
import math
import sys
import time

from . import check
from ..config import RaspiMouseConfig
from ..exceptions import RaspiMouseError
from ..robot import RaspiMouse


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog='raspimouse-cli', description='Check Raspberry Pi Mouse devices.')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('check', help='check the Raspberry Pi setup and print how to fix problems')

    led = sub.add_parser('led', help='turn LEDs on for a while')
    led.add_argument('index', type=int, nargs='*',
                     help='LED numbers 0-3 (default: all)')
    led.add_argument('--duration', type=float, default=1.0, help='[s] (default: 1.0)')

    switch = sub.add_parser('switch', help='print switch states')
    switch.add_argument('--watch', action='store_true',
                        help='keep printing whenever a state changes')
    switch.add_argument('--duration', type=float, default=10.0,
                        help='[s] how long to watch (default: 10.0)')
    sensor = sub.add_parser('sensor', help='print light sensor values')
    sensor.add_argument('--watch', action='store_true', help='keep printing values')
    sensor.add_argument('--duration', type=float, default=10.0,
                        help='[s] how long to watch (default: 10.0)')
    sensor.add_argument('--interval', type=float, default=0.2,
                        help='[s] time between readings when watching (default: 0.2)')

    buzzer = sub.add_parser('buzzer', help='sound the buzzer for a while')
    buzzer.add_argument('frequency', type=float, nargs='+',
                        help='[Hz] frequencies played in order (0 = rest)')
    buzzer.add_argument('--duration', type=float, default=0.5,
                        help='[s] length of each frequency (default: 0.5)')

    motor = sub.add_parser('motor', help='run the motors for a while (the robot moves!)')
    motor.add_argument('left', type=float, help='signed step frequency [Hz]')
    motor.add_argument('right', type=float, help='signed step frequency [Hz]')
    motor.add_argument('--duration', type=float, default=1.0, help='[s] (default: 1.0)')

    drive = sub.add_parser('drive', help='drive at a velocity for a while (the robot moves!)')
    drive.add_argument('linear', type=float, help='forward velocity [m/s]')
    drive.add_argument('angular', type=float, help='counterclockwise angular velocity [rad/s]')
    drive.add_argument('--duration', type=float, default=1.0, help='[s] (default: 1.0)')

    battery = sub.add_parser(
        'battery', help='print the battery (or AC adapter) voltage (V3 only)')
    battery.add_argument('--watch', action='store_true', help='keep printing values')
    battery.add_argument('--duration', type=float, default=10.0,
                         help='[s] how long to watch (default: 10.0)')
    battery.add_argument('--interval', type=float, default=1.0,
                         help='[s] time between readings when watching (default: 1.0)')

    counter = sub.add_parser('counter', help='print raw pulse counter values (V3 only)')
    counter.add_argument('--watch', action='store_true', help='keep printing values')
    counter.add_argument('--duration', type=float, default=10.0,
                         help='[s] how long to watch (default: 10.0)')
    counter.add_argument('--interval', type=float, default=0.5,
                         help='[s] time between readings when watching (default: 0.5)')
    return parser


def _led(args: argparse.Namespace) -> int:
    count = len(RaspiMouseConfig().led_pins)
    indices = args.index or list(range(count))
    invalid = [i for i in indices if not 0 <= i < count]
    if invalid:
        print(f'error: LED number must be 0-{count - 1}: {invalid}', file=sys.stderr)
        return 2
    with RaspiMouse() as mouse:
        for i in indices:
            mouse.leds[i].on()
        print(f'LED {" ".join(map(str, indices))} on for {args.duration} s')
        time.sleep(args.duration)
    return 0


def _format_switches(states: tuple[bool, ...]) -> str:
    return ', '.join(
        f'{i}: {"pressed" if pressed else "released"}' for i, pressed in enumerate(states))


def _switch(args: argparse.Namespace) -> int:
    with RaspiMouse() as mouse:
        start = time.monotonic()
        last = tuple(sw.is_pressed() for sw in mouse.switches)
        print(f'{0.0:6.2f} s  {_format_switches(last)}', flush=True)
        if not args.watch:
            return 0
        while time.monotonic() - start < args.duration:
            time.sleep(0.01)
            states = tuple(sw.is_pressed() for sw in mouse.switches)
            if states != last:
                elapsed = time.monotonic() - start
                print(f'{elapsed:6.2f} s  {_format_switches(states)}', flush=True)
                last = states
    return 0


def _buzzer(args: argparse.Namespace) -> int:
    negative = [f for f in args.frequency if f < 0]
    if negative:
        print(f'error: frequency must not be negative: {negative}', file=sys.stderr)
        return 2
    with RaspiMouse() as mouse:
        for frequency in args.frequency:
            mouse.buzzer.play(frequency)
            print(f'{mouse.buzzer.frequency_hz:g} Hz for {args.duration} s', flush=True)
            time.sleep(args.duration)
        mouse.buzzer.stop()
    return 0


def _sensor(args: argparse.Namespace) -> int:
    with RaspiMouse() as mouse:
        start = time.monotonic()
        while True:
            v = mouse.light_sensors.read()
            elapsed = time.monotonic() - start
            print(f'{elapsed:6.2f} s  RF {v.right_front:5d}  R {v.right:5d}  '
                  f'L {v.left:5d}  LF {v.left_front:5d}', flush=True)
            if not args.watch or elapsed + args.interval > args.duration:
                return 0
            time.sleep(args.interval)


def _motor(args: argparse.Namespace) -> int:
    with RaspiMouse() as mouse:
        mouse.motor_power.on()
        mouse.motors.set_frequency(args.left, args.right)
        print(f'left {mouse.motors.left.frequency_hz:g} Hz, '
              f'right {mouse.motors.right.frequency_hz:g} Hz for {args.duration} s', flush=True)
        time.sleep(args.duration)
        mouse.motors.stop()
        mouse.motor_power.off()
        if mouse.left_counter and mouse.right_counter:
            print(f'pulses: left {mouse.left_counter.read_signed():+d}, '
                  f'right {mouse.right_counter.read_signed():+d}', flush=True)
    return 0


def _drive(args: argparse.Namespace) -> int:
    with RaspiMouse() as mouse:
        mouse.motor_power.on()
        drive = mouse.drive
        end = time.monotonic() + args.duration
        # Repeat the command like a ROS node does; the drive stops when commands stop.
        while time.monotonic() < end:
            drive.set_velocity(args.linear, args.angular)
            time.sleep(0.05)
        drive.stop()
        deadline = time.monotonic() + 3.0
        while drive.wheel_frequencies != (0.0, 0.0) and time.monotonic() < deadline:
            time.sleep(0.02)
        time.sleep(0.1)  # let odometry catch up with the last pulses
        odom = drive.odometry()
        mouse.motor_power.off()
        print(f'x {odom.x:+.3f} m, y {odom.y:+.3f} m, '
              f'theta {math.degrees(odom.theta):+.1f} deg', flush=True)
    return 0


def _battery(args: argparse.Namespace) -> int:
    with RaspiMouse() as mouse:
        if mouse.battery is None:
            print('error: the battery monitor is disabled in the configuration', file=sys.stderr)
            return 1
        start = time.monotonic()
        while True:
            elapsed = time.monotonic() - start
            raw = mouse.battery.read_raw()
            voltage = mouse.battery.read_voltage()
            print(f'{elapsed:6.2f} s  {voltage:5.2f} V  (ADC {raw})', flush=True)
            if not args.watch or elapsed + args.interval > args.duration:
                return 0
            time.sleep(args.interval)


def _counter(args: argparse.Namespace) -> int:
    with RaspiMouse() as mouse:
        if not (mouse.left_counter and mouse.right_counter):
            print('error: pulse counters are disabled in the configuration', file=sys.stderr)
            return 1
        start = time.monotonic()
        while True:
            elapsed = time.monotonic() - start
            print(f'{elapsed:6.2f} s  left {mouse.left_counter.read_raw():5d}  '
                  f'right {mouse.right_counter.read_raw():5d}', flush=True)
            if not args.watch or elapsed + args.interval > args.duration:
                return 0
            time.sleep(args.interval)


def _check(args: argparse.Namespace) -> int:
    results = check.run_checks()
    print(check.format_results(results))
    return 1 if any(r.level == check.FAIL for r in results) else 0


_COMMANDS = {
    'check': _check,
    'led': _led,
    'switch': _switch,
    'buzzer': _buzzer,
    'sensor': _sensor,
    'motor': _motor,
    'counter': _counter,
    'battery': _battery,
    'drive': _drive,
}


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = build_parser().parse_args(argv)
    command = _COMMANDS.get(args.command)
    if command is None:
        print(f'{args.command}: not implemented yet', file=sys.stderr)
        return 1
    try:
        return command(args)
    except RaspiMouseError as e:
        print(f'error: {e}', file=sys.stderr)
        print('hint: run "raspimouse-cli check" to find setup problems', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == '__main__':
    sys.exit(main())
