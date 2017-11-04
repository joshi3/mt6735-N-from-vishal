#!/usr/bin/env python

'''Output colored text if standard output is a 'xterm' tty'''

import os


_RED       = '\033[91m'
_GREEN     = '\033[92m'
_YELLOW    = '\033[93m'
_BLUE      = '\033[94m'
_MAGENTA   = '\033[95m'
_CYAN      = '\033[96m'
_WHITE     = '\033[1;37m'
_END       = '\033[0m'


def _color(msg, color):
    if os.isatty(1) and os.environ['TERM'] == 'xterm':
        return color + msg + _END
    else:
        return msg


def red(msg):
    return _color(msg, _RED)


def green(msg):
    return _color(msg, _GREEN)


def yellow(msg):
    return _color(msg, _YELLOW)


def white(msg):
    return _color(msg, _WHITE)


def blue(msg):
    return _color(msg, _BLUE)


def cyan(msg):
    return _color(msg, _CYAN)


def magenta(msg):
    return _color(msg, _MAGENTA)
