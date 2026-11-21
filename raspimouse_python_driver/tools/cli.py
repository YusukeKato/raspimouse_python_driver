"""
Command line tool to check each device by hand.

Run as ``raspimouse-cli`` or ``python3 -m raspimouse_python_driver.tools.cli``.
"""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog='raspimouse-cli', description='Check Raspberry Pi Mouse devices.')
    sub = parser.add_subparsers(dest='command', required=True)

    led = sub.add_parser('led', help='turn an LED on or off')
    led.add_argument('index', type=int, choices=range(4))
    led.add_argument('state', choices=['on', 'off'])

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


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = build_parser().parse_args(argv)
    print(f'{args.command}: not implemented yet', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
