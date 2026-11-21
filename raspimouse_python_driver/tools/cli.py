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

    switch = sub.add_parser('switch', help='print switch states')
    switch.add_argument('--watch', action='store_true',
                        help='keep printing whenever a state changes')
    switch.add_argument('--duration', type=float, default=10.0,
                        help='[s] how long to watch (default: 10.0)')
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


_COMMANDS = {
    'led': _led,
    'switch': _switch,
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
