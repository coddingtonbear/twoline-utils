import re

def color_tuple(string):
    r, g, b = string.split(',')
    return int(r), int(g), int(b)


def time_string(string):
    time_matcher = re.compile('(\d+):(\d+)')
    return [int(g) for g in time_matcher.match(string).groups()]
