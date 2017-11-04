#!/usr/bin/env python

import os
import datetime

from py_common import sh, ShError, DirRestorer


def git(cmd):
    '''git wrapper'''
    print(cmd)
    output = sh(cmd)
    for line in output:
        print(line)


def git_output(cmd):
    print(cmd)
    return sh(cmd)


def git_get_last_author(path):
    return sh('git log --pretty=format:%aN -1 {0}'.format(path))[0]


def git_get_last_date(path):
    return sh('git log --pretty=format:%ai -1 {0}'.format(path))[0]


class BlameTokens(object):
    
    def __init__(self):
        self.sha1 = None
        self.author = None
        self.date = None
        self.lineno = None
        self.content = None


def _break_blame_line(line):
    '''6216b0d5 (moxiaoming   Thu Dec 15 16:03:29 2011    5) mt13_w690_f1_pulid_v3   other stuff
        sha1      author                date             lineno    project
         0         1           2   3   4     5      6     7          8
         
    >>> blame_tokens = _break_blame_line('6216b0d5 (moxiaoming   Thu Dec 15 16:03:29 2011    5) mt13_w690_f1_pulid_v3   other stuff')
    >>> print(blame_tokens.sha1)
    6216b0d5
    >>> print(blame_tokens.author)
    moxiaoming
    >>> blame_tokens.date == datetime.datetime.strptime('Thu Dec 15 16:03:29 2011', '%a %b %d %H:%M:%S %Y')
    True
    >>> print(blame_tokens.lineno)
    5
    >>> print(blame_tokens.content)
    mt13_w690_f1_pulid_v3   other stuff
    
    
    '''

    tokens = line.split(None, 8)

    blame_tokens = BlameTokens()
    blame_tokens.sha1 = tokens[0]
    blame_tokens.author = tokens[1][1:]
    blame_tokens.date = datetime.datetime.strptime(' '.join(tokens[2:7]), '%a %b %d %H:%M:%S %Y')
    blame_tokens.lineno = tokens[7][:-1]
    blame_tokens.content = tokens[8]

    return blame_tokens

        
def git_blame_walk(path):
    with DirRestorer():
        os.chdir(os.path.dirname(path))
        output = git_output('git blame --date=local {0}'.format(os.path.basename(path)))
        return [_break_blame_line(line) for line in output]
