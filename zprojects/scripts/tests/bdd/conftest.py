#!/usr/bin/env python

import pytest
from pyutils import fs
import sh


@pytest.yield_fixture(scope='module')
def site():
    def reset():
        sh.git('clean', '-xfd', _cwd='vanzo')
        sh.git('reset', '--hard', 'HEAD', _cwd='vanzo')

    config_name = 'a20-moxiaoming_35m'

    reset()
    yield config_name
    reset()
    fs.rm('zprojects/{}'.format(config_name))

