#!/usr/bin/env python

import os
from os.path import exists, join
import sh
import shutil
import sys

from pyutils import fs


_ZPROJECTS = 'zprojects'
_PO_NAME = 'patch_overrides'

class _Error(Exception):
    def __init__(self, msg):
        super(_Error, self).__init__()
        self.msg = msg

    def __str__(self):
        return str(self.msg)


def _is_ali():
    with fs.chdir('{}/scripts'.format(_ZPROJECTS)):
        return 'zprojects_ali' in sh.git('remote', '-v').stdout


def _get_project_name(target_config):
    return target_config.split('-')[0] if _is_ali() else '-'.join(target_config.split('-')[:2])


def _config_has_po(project_name, target_config):
    return exists(join(_ZPROJECTS, project_name, target_config, _PO_NAME))


def _cp_father_po(project_name, target_config):
    def _adjust_symlinks():
        for root, dirs, files in os.walk(target_config_po):
            for filename in (x for x in dirs + files if not exists(join(root, x))):
                path = join(root, filename)
                link_target = os.readlink(path)
                os.remove(path)
                os.symlink(join('..', link_target), path)
                print('ajust link {}'.format(path))

    target_config_po = join(_ZPROJECTS, project_name, target_config, _PO_NAME)

    tokens = target_config.split('-')[:-1]
    while len(tokens) > 1:
        father_po = join(_ZPROJECTS, project_name, '-'.join(tokens), _PO_NAME)
        if exists(father_po):
            shutil.copytree(father_po, target_config_po, symlinks=True)
            print('cp {} -> {}'.format(father_po, target_config))
            return
        tokens = tokens[:-1]

    project_po = join(_ZPROJECTS, project_name, _PO_NAME)
    if exists(project_po):
        shutil.copytree(project_po, target_config_po, symlinks=True)
        print('cp {} -> {}'.format(project_po, target_config))
        _adjust_symlinks()
        if target_config == project_name:
            shutil.rmtree(project_po)
            print('rm {}'.format(project_po))
        return
    print('father does not have patch_overrides')


def _create_config_dir(project_name, target_config):
    target_config_dir = join(_ZPROJECTS, project_name, target_config)
    if not exists(target_config_dir):
        os.makedirs(target_config_dir)


def cp_po(target_config):
    project_name = _get_project_name(target_config)

    if _config_has_po(project_name, target_config):
        print('has po already')
        return

    _create_config_dir(project_name, target_config)

    _cp_father_po(project_name, target_config)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: cp_po target_config')
        sys.exit(1)

    cp_po(sys.argv[1])
