import argparse
import logging


logger = logging.getLogger(__name__)

COMMANDS = {}


def command(desc, name=None, aliases=None):
    if aliases is None:
        aliases = []
    def decorator(fn):
        main_name = name if name else fn.__name__
        command_details = {
            'function': fn,
            'description': desc,
            'is_alias': False,
            'aliases': [],
        }

        COMMANDS[main_name] = command_details
        for alias in aliases:
            COMMANDS[alias] = command_details.copy()
            COMMANDS[alias]['is_alias'] = True
            COMMANDS[main_name]['aliases'].append(alias)
        return fn
    return decorator


def get_command(name):
    return COMMANDS[name]


@command('Watch a jenkins job at a provided URL', aliases=['wjj', 'jenkins'])
def watch_jenkins_job(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'url',
        type=str,
        nargs=1,
        help='Jenkins URL to watch'
    )
    options = parser.parse_args(args)

    print(options.url)
