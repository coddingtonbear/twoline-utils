import argparse
import datetime
import json
import logging
import os
import re
import requests
import sys
import time

from twoline_utils.argtypes import color_tuple, time_string
from twoline_utils.utils import send_flash_message


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


@command('Flash the screen when it\'s a certain time')
def alarm(args, settings, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'time',
        type=time_string,
        nargs=1,
        help='Amount of time to wait',
    )
    parser.add_argument(
        'message',
        type=str,
        nargs='?',
        default='Alarm Expired',
        help='Jenkins URL to watch'
    )
    parser.add_argument(
        '--color',
        dest='colors',
        action='append',
        type=color_tuple,
        default=[]
    )
    parser.add_argument(
        '--timeout',
        dest='timeout',
        type=int,
        default=20,
        help='How long to display this message on the screen',
    )
    options = parser.parse_args(args)

    if not options.colors:
        options.colors.extend([(255, 0, 0), (0, 0, 0)])

    while True:
        now = datetime.datetime.now()
        if now.hour == options.time[0][0] and now.minute == options.time[0][1]:
            send_flash_message(
                settings.device_url,
                {
                    'message': options.message,
                    'blink': options.colors,
                    'timeout': options.timeout,
                }
            )
            break

        time.sleep(1.0)


@command('Start a timer and flash the screen when the timer has expired')
def timer(args, settings, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'interval',
        type=float,
        nargs=1,
        help='Amount of time to wait',
    )
    parser.add_argument(
        'message',
        type=str,
        nargs='?',
        default='Timer Expired',
        help='Jenkins URL to watch'
    )
    parser.add_argument(
        '--color',
        dest='colors',
        action='append',
        type=color_tuple,
        default=[]
    )
    parser.add_argument(
        '--timeout',
        dest='timeout',
        type=int,
        default=20,
        help='How long to display this message on the screen',
    )
    options = parser.parse_args(args)

    if not options.colors:
        options.colors.extend([(255, 0, 0), (0, 0, 0)])

    time.sleep(options.interval[0])

    send_flash_message(
        settings.device_url,
        {
            'message': options.message,
            'blink': options.colors,
            'timeout': options.timeout,
        }
    )


@command('Watch a jenkins job at a provided URL', aliases=['wjj', 'jenkins'])
def watch_jenkins_job(args, settings, **kwargs):
    from jenkinsapi.jenkins import Jenkins
    from jenkinsapi.jenkins import JenkinsBase
    from jenkinsapi.build import Build
    from jenkinsapi.utils.requester import Requester
    try:
        from urllib.parser import urlparse
    except ImportError:
        from urlparse import urlparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'url',
        type=str,
        nargs=1,
        help='Jenkins URL to watch'
    )
    parser.add_argument(
        '--sleep-interval',
        dest='sleep_interval',
        default=30,
        type=int,
        help='Amount of time to sleep',
    )
    parser.add_argument(
        '--retries',
        dest='retries',
        default=25,
        type=int,
        help='Number of times to re-poll Jenkins'
    )
    options = parser.parse_args(args)

    class NoVerifyRequester(Requester):
        def get_request_dict(self, *args, **kwargs):
            request_dict = super(NoVerifyRequester, self).get_request_dict(
                *args, **kwargs
            )
            request_dict['verify'] = False
            return request_dict

    def get_job_name_and_build_number(url):
        job_build_matcher = re.compile(
            ".*/job/(?P<job>[^/]+)/(?P<build_number>[^/]+)/.*"
        )
        job, build_no = job_build_matcher.search(url).groups()
        return job, int(build_no)

    def get_formal_build_url(jenkins_url, job_name, build_no):
        return os.path.join(
            jenkins_url,
            'job',
            job_name,
            str(build_no)
        )

    def get_jenkins_base_url(url):
        parsed = urlparse(url)
        return parsed.scheme + '://' + parsed.netloc

    job_name, build_no = get_job_name_and_build_number(options.url[0])
    jenkins_url = get_jenkins_base_url(options.url[0])
    formal_build_url = get_formal_build_url(
        jenkins_url,
        job_name,
        build_no
    )

    try:
        jenkins = Jenkins(
            jenkins_url,
            requester=NoVerifyRequester()
        )
        job = jenkins[job_name]
        job.RETRY_ATTEMPTS = options.retries
        build = Build(formal_build_url, build_no, job)

        while True:
            if not build.is_running():
                if build.is_good():
                    send_flash_message(
                        settings.device_url,
                        {
                            'message': 'Jenkins job %s:%s succeeded' % (
                                job_name,
                                build_no,
                            ),
                            'blink': [(0, 255, 0), (0, 0, 0)],
                            'timeout': 20,
                        }
                    )
                    logger.warn(
                        'Job %s succeeded',
                        formal_build_url,
                    )
                else:
                    send_flash_message(
                        settings.device_url,
                        {
                            'message': 'Jenkins job %s:%s failed (%s)' % (
                                job_name,
                                build_no,
                                build.get_status()
                            ),
                            'blink': [(255, 0, 0), (0, 0, 0)],
                            'timeout': 20,
                        }
                    )
                    logger.warn(
                        'Job %s failed',
                        formal_build_url,
                    )
                sys.exit(0)
            time.sleep(options.sleep_interval)
    except Exception as e:
        logger.exception(e)
