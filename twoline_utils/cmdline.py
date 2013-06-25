import argparse
import logging
import os
import sys

from twoline_utils import commands


logger = logging.getLogger(__name__)


def get_command_list():
    command_lines = []
    for name, info in commands.COMMANDS.items():
        if info['is_alias']:
            continue
        message = "{0}: {1}".format(name, info['description'])
        if info['aliases']:
            message = message + '; aliases: {0}'.format(
                ', '.join(info['aliases'])
            )
        command_lines.append(message)
    prolog = 'available commands:\n'
    return prolog + '\n'.join(['  ' + cmd for cmd in command_lines])


def run_from_cmdline():
    parser = argparse.ArgumentParser(
        epilog=get_command_list(),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'command',
        type=str,
        nargs=1,
        help='Command to run',
        metavar='COMMAND',
        choices=commands.COMMANDS.keys()
    )
    parser.add_argument(
        '--loglevel',
        dest='loglevel',
        default='WARN',
    )
    parser.add_argument(
        '--no-fork',
        dest='fork',
        default=True,
        action='store_false',
        help='Do not fork command actions into a separate process'
    )
    parser.add_argument(
        '--device-url',
        dest='device_url',
        default='http://127.0.0.1:6224/',
        help='Device URL'
    )

    args, remainder = parser.parse_known_args()

    logging.basicConfig(
        level=logging.getLevelName(args.loglevel)
    )

    if args.fork:
        result = os.fork()
        if result:
            sys.exit(0)

    command = commands.get_command(args.command[0])
    logger.debug(
        'Executing command %s with args %s',
        args.command[0],
        remainder
    )
    command['function'](remainder, settings=args)
    logger.debug(
        'Execution of command %s complete',
        args.command[0],
    )
