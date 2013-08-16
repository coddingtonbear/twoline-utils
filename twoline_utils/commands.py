import argparse
import json
import logging
import os
import re
import requests
import sys
import time


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
        default=10,
        type=int,
        help='Amount of time to sleep',
    )
    parser.add_arguments(
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

    def send_flash_message(message):
        requests.put(
            os.path.join(
                settings.device_url,
                'flash/'
            ),
            data=json.dumps(message)
        )

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
                    send_flash_message({
                        'message': 'Jenkins job %s:%s succeeded' % (
                            job_name,
                            build_no,
                        ),
                        'blink': [(0, 255, 0), (0, 0, 0)],
                        'timeout': 20,
                    })
                    logger.warn(
                        'Job %s succeeded',
                        formal_build_url,
                    )
                else:
                    send_flash_message({
                        'message': 'Jenkins job %s:%s failed (%s)' % (
                            job_name,
                            build_no,
                            build.get_status()
                        ),
                        'blink': [(255, 0, 0), (0, 0, 0)],
                        'timeout': 20,
                    })
                    logger.warn(
                        'Job %s failed',
                        formal_build_url,
                    )
                sys.exit(0)
            time.sleep(options.sleep_interval)
    except Exception as e:
        logger.exception(e)
