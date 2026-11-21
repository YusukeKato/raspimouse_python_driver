"""
Command line tool to check each device by hand.

Run as ``raspimouse-cli`` or ``python3 -m raspimouse_python_driver.tools.cli``.
"""

import argparse
import sys
import time

from ..config import RaspiMouseConfig
from ..exceptions import RaspiMouseError
from ..robot import RaspiMouse


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog='raspimouse-cli', description='Check Raspberry Pi Mouse devices.')
    sub = parser.add_subparsers(dest='command', required=True)

    led = sub.add_parser('led', help='turn LEDs on for a while')
    led.add_argument('index', type=int, nargs='*',
                     help='LED numbers 0-3 (default: all)')
    led.add_argument('--duration', type=float, default=1.0, help='[s] (default: 1.0)')

    sub.add_parser('switch', help='print switch states')
    sub.add_parser('sensor', help='print light sensor values')

    buzzer = sub.add_parser('buzzer', help='sound the buzzer (0 stops)')
    buzzer.add_argument('frequency', type=int)

    motor = sub.add_parser('motor', help='run the motors for a while')
    motor.add_argument('left', type=int, help='signed frequency [Hz]')
    motor.add_argument('right', type=int, help='signed frequency [Hz]')
    motor.add_argument('--duration', type=float, default=1.0, help='[s]')

    sub.add_parser('counter', help='print pulse counter values')
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


_COMMANDS = {
    'led': _led,
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
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == '__main__':
    sys.exit(main())
