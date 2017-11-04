#!/usr/bin/env python

'''Handy functions and classes relates to python, not projects.'''

import os
import errno
from commands import getstatusoutput

class DirRestorer(object):
    '''Context manager for dir operations, return to cwd after operation.
    
    >>> import os
    >>> org_dir = os.getcwd()
    >>> with DirRestorer():
    ...    os.chdir('..')
    ...
    >>> org_dir == os.getcwd()
    True
    
    '''

    def __enter__(self):
        self.__dir = os.getcwd()
        return self.__dir


    def __exit__(self, type_, value, traceback):
        os.chdir(self.__dir)


def have_same_content(file1, file2):
    '''If files or dirs have same content.
    
    >>> have_same_content('test_custom_mt6575ics/path/to/some/where1/a.txt', 'test_custom_mt6575ics/path/to/some/where2/a.txt')
    False
    
    >>> have_same_content('test_custom_mt6575ics/path/to/some/where3/a.txt', 'test_custom_mt6575ics/path/to/some/where2/a.txt')
    True

    '''

    return getstatusoutput('diff -qr {file1} {file2}'.format(**locals()))[0] == 0


class ShError(Exception):
    '''When command goes wrong.
    
    >>> str(ShError('Error'))
    "'Error'"
    
    '''

    def __init__(self, error_msg=None):
        self.__error_msg = error_msg


    def __str__(self):
        return repr(self.__error_msg)


def sh(cmd, toleration=False):
    '''shell command wrapper
    
    >>> sh('xx') #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ShError: 'xx: 32512: sh: xx: not found'

    >>> sh('for i in 1 2 3; do echo $i; done')
    ['1', '2', '3']
    
    '''

    status, output = getstatusoutput(cmd)
    if not toleration and status:
        raise ShError('{cmd}: {status}: {output}'.format(**locals()))
    return output.splitlines()


def mkdir_p(path):
    '''Recursive dir creation.
    
    >>> parent = 'test_custom_mt6575ics/path/to/some/where3/'
    >>> mkdir_p(parent)
    
    >>> mkdir_p(parent + 'h/d')
    >>> os.path.exists(parent + 'h/d')
    True
    
    >>> import shutil
    >>> shutil.rmtree(parent + '/h')
    >>> os.path.exists(parent + '/h')
    False
    
    >>> mkdir_p('/haha') #doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    OSError: [Errno ...] Permission denied: '/haha'
        
    '''

    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno != errno.EEXIST or not os.path.isdir(path):
            raise
