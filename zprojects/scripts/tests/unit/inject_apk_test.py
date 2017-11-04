#!/usr/bin/env python

import os
import pyutils
import sh
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'zprojects/scripts'))
import re

import pytest

import inject_apk


@pytest.mark.parametrize('config_name, board_project_name', [
        ('a20', 'a20'),
        ('a20-kewang', 'a20'),
        ('a20-kewang_35m-abc', 'a20'),
])
def test_get_board_project_name(config_name, board_project_name):
    assert inject_apk.get_board_project_name(config_name) == board_project_name


@pytest.mark.parametrize('config_name, customer_project_name', [
        ('a20-kewang', 'a20-kewang'),
        ('a20-kewang_35m-abc', 'a20-kewang_35m'),
])
def test_get_customer_project_name(config_name, customer_project_name):
    assert inject_apk.get_customer_project_name(config_name) == customer_project_name


@pytest.mark.parametrize('config_name, ret', [
        ('a20-kewang', True),
        ('a20-kewang_35m', True),
        ('a20-kewang_35m-abc', True),
        ('a20-kewang-abc', True),
])
def test_is_config_name_legal_legal_config_name_return_True(config_name, ret):
    assert inject_apk.is_config_name_legal(config_name)


@pytest.mark.parametrize('config_name, ret', [
        ('a20', False),
        ('a20-kewang_', False),
        ('', False),
        ('-a20-kewang', False),
        ('-', False),
        ('_a20-kewang', False),
        ('#a20-kewang', False),
        ('a20-kewang-', False),
        ('a20-kewa!ng', False),
])
def test_is_config_name_legal_illegal_config_name_return_False(config_name, ret):
    assert not inject_apk.is_config_name_legal(config_name)


def test_validate_config_name_invalid_config_name_raise_InvalidConfigNameError(monkeypatch):
    monkeypatch.setattr('inject_apk.is_config_name_legal', lambda x: False)
    monkeypatch.setattr('inject_apk.board_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.customer_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.config_exists', lambda x: True)

    with pytest.raises(inject_apk.InvalidConfigNameError) as exc:
        inject_apk.validate_config_name('!a20')

    assert 'Invalid config name' in str(exc)


def test_validate_config_name_not_such_board_project_raise_InvalidConfigNameError(monkeypatch):
    monkeypatch.setattr('inject_apk.is_config_name_legal', lambda x: True)
    monkeypatch.setattr('inject_apk.board_project_exists', lambda x: False)
    monkeypatch.setattr('inject_apk.customer_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.config_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.get_board_project_name', lambda x: 'abc')

    with pytest.raises(inject_apk.InvalidConfigNameError) as exc:
        inject_apk.validate_config_name('a20-kewang')

    assert 'Board abc does not exist' in str(exc)


def test_validate_config_name_no_such_project_name_raise_InvalidConfigNameError(monkeypatch):
    monkeypatch.setattr('inject_apk.is_config_name_legal', lambda x: True)
    monkeypatch.setattr('inject_apk.board_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.customer_project_exists', lambda x: False)
    monkeypatch.setattr('inject_apk.config_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.get_customer_project_name', lambda x: 'abc')

    with pytest.raises(inject_apk.InvalidConfigNameError) as exc:
        inject_apk.validate_config_name('a20-kewang')

    assert 'Customer project abc does not exist' in str(exc)


def test_validate_config_name_no_such_config_raise_InvalidConfigNameError(monkeypatch):
    monkeypatch.setattr('inject_apk.is_config_name_legal', lambda x: True)
    monkeypatch.setattr('inject_apk.board_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.customer_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.config_exists', lambda x: False)

    with pytest.raises(inject_apk.InvalidConfigNameError) as exc:
        inject_apk.validate_config_name('a20-kewang-xyz')

    assert 'Config a20-kewang-xyz does not exist' in str(exc)


def test_validate_config_name_valid_config_name_return(monkeypatch):
    monkeypatch.setattr('inject_apk.is_config_name_legal', lambda x: True)
    monkeypatch.setattr('inject_apk.board_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.customer_project_exists', lambda x: True)
    monkeypatch.setattr('inject_apk.config_exists', lambda x: True)

    inject_apk.validate_config_name('a20-kewang')


def test_config_patch_overrides_path_config_return():
    assert inject_apk.get_config_patch_overrides_path('a20-kewang_35m-abc') == \
        '{}/a20-kewang_35m/a20-kewang_35m-abc/patch_overrides'.format(inject_apk.ZPROJECTS)


def test_config_patch_overrides_path_config_is_customer_project_return():
    assert inject_apk.get_config_patch_overrides_path('a20-kewang') == \
        '{}/a20-kewang/a20-kewang/patch_overrides'.format(inject_apk.ZPROJECTS)


def test_get_config_overrides_path():
    assert inject_apk.get_config_overrides_path('a20-kewang_35m-abc') == \
        '{}/a20-kewang_35m/a20-kewang_35m-abc/patch_overrides/overrides'.format(inject_apk.ZPROJECTS)


def test_get_config_patches_path():
    assert inject_apk.get_config_patches_path('a20-kewang_35m-abc') == \
        '{}/a20-kewang_35m/a20-kewang_35m-abc/patch_overrides/patches'.format(inject_apk.ZPROJECTS)


def test_get_apk_package_name_invalid_input_return_package_name(monkeypatch):
    monkeypatch.setattr('inject_apk.aapt_badging', lambda x: """sdkVersion:'14'\n"""\
                            """package: name='com.google.android.gm' versionCode='4800250' versionName='4.8 (1167183)'\n"""\
                            """targetSdkVersion:'19'\n"""\
                            """uses-permission:'android.permission.ACCESS_NETWORK_STATE'\n""")

    assert inject_apk.get_apk_package_name('abc.apk') == 'com.google.android.gm'


def test_get_apk_package_name_invalid_apk_raise_InvalidAPKError(monkeypatch):
    def fake_aapt_badging(x):
        raise sh.ErrorReturnCode_1('', '', '')

    monkeypatch.setattr('inject_apk.aapt_badging', fake_aapt_badging)

    with pytest.raises(inject_apk.InvalidAPKError):
        inject_apk.get_apk_package_name('abc.apk')


def test_get_apk_package_name_cannot_find_package_name_raise_InvalidAPKError(monkeypatch):
    monkeypatch.setattr('inject_apk.aapt_badging', lambda x: """package-name='com.google.android.gm' versionCode='4800250' versionName='4.8 (1167183)'\n"""\
                            """sdkVersion:'14'\n"""\
                            """targetSdkVersion:'19'\n"""\
                            """uses-permission:'android.permission.ACCESS_NETWORK_STATE'\n""")

    with pytest.raises(inject_apk.InvalidAPKError):
        inject_apk.get_apk_package_name('abc.apk')


def test_make_override_name():
    assert inject_apk.make_override_name('a20-kewang_35m-abc', 'vanzo/custom_app') == 'vanzo/custom_app.override.kewang_35m'
