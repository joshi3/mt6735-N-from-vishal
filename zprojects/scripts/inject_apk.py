#!/usr/bin/env python

"""
Make apk odex.

FIXME: This module will be split into several modules when
refectoring zprojects
"""

import collections
import os
from pyutils import fs
import re
import sh
import shutil
import sys


ZPROJECTS = 'zprojects'


class Error(Exception):
    """Base class for all 5.0+ Exceptions."""

    def __init__(self, msg=''):
        super(Error, self).__init__()
        self._msg = msg

    def __str__(self):
        return str(self._msg)


class ParamError(Error):
    """Argument Error."""

    pass


def get_board_project_name(config_name):
    """Return board name.

    The validation of config_name is garanteed by caller.
    """

    return config_name.split('-')[0]


def get_customer_project_name(config_name):
    """Return custom project name.

    The validation of config_name is garanteed by caller.
    """

    return '-'.join(config_name.split('-')[:2])


class InvalidConfigNameError(Error):
    """Config is invalid, somehow."""

    pass


def is_config_name_legal(config_name):
    """Config name should match certain naming convensions."""

    return re.match(r'[a-z0-9]+-[a-z0-9_]+[a-z0-9](?:[\-_0-9a-z]+[a-z0-9])?$',
                    config_name) is not None


def board_project_exists(config_name):
    """Does board project folder exist."""

    name = get_board_project_name(config_name)
    return os.path.exists(os.path.join(ZPROJECTS, name))


def customer_project_exists(config_name):
    """Does customer project folder exist."""

    name = get_customer_project_name(config_name)
    return os.path.exists(os.path.join(ZPROJECTS, name))


def config_exists(config_name):
    """Does config folder exists."""

    return os.path.exists(
        os.path.join(
            ZPROJECTS, get_customer_project_name(config_name), config_name))


def validate_config_name(config_name):
    """Check if config name is workable.

    That is, board and customer project folers should exist, its name
    should be valid.
    """

    if not is_config_name_legal(config_name):
        raise InvalidConfigNameError(
            'Invalid config name {}'.format(config_name))

    if not board_project_exists(config_name):
        name = get_board_project_name(config_name)
        raise InvalidConfigNameError(
            'Board {} does not exist'.format(name))

    if not customer_project_exists(config_name):
        name = get_customer_project_name(config_name)
        raise InvalidConfigNameError(
            'Customer project {} does not exist'.format(name))

    if not config_exists(config_name):
        raise InvalidConfigNameError(
            'Config {} does not exist'.format(config_name))


def get_config_patch_overrides_path(config_name):
    """Return the config's patch_overrides path."""

    customer_project_name = get_customer_project_name(config_name)
    return os.path.join(
        ZPROJECTS, customer_project_name, config_name, 'patch_overrides')


def get_config_overrides_path(config_name):
    """Return the config's overrides path."""

    return os.path.join(
        get_config_patch_overrides_path(config_name), 'overrides')


def get_config_patches_path(config_name):
    """Return the config's patches path."""

    return os.path.join(
        get_config_patch_overrides_path(config_name), 'patches')


class InvalidAPKError(Error):
    """Something wrong with apk."""

    pass


class ConflictOverridesError(Error):
    """Multiple overrides conflict."""

    pass


def touch(filename): #pragma: no cover
    """Mimic the behavior of touch."""

    with open(filename, 'a'):
        os.utime(filename, None)


def get_filenames_in_apk(apkfilename, search_regex):
    """Return a file list match regex in apk zip file.

    apkfilename -- full path to apk file
    regex -- compiled regex string
    """

    ret = []
    # zipfile module cannot unzip some 'buggy' zip file
    out = sh.unzip('-l', apkfilename).stdout.decode(errors='ignore') #pylint: disable=E1101,C0301
    regex = re.compile(r'\s*\d+\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}\s+(.+)')
    for line in out.splitlines():
        match = regex.match(line)
        if match:
            filename = match.group(1)
            if search_regex.search(filename):
                ret.append(filename)
    return ret


def aapt_badging(apkfilename): #pragma: no cover
    """Stdout from aapt d bading apk."""

    return sh.aapt('d', 'badging', apkfilename).stdout.decode(errors='ignore') #pylint: disable=E1101,C0301


def get_apk_package_name(apkfilename):
    """Return package name of a apk."""

    try:
        info = aapt_badging(apkfilename)
        return re.search(r"^package:\s*name='([^']+)'", info, re.M).group(1)
    except (sh.ErrorReturnCode, AttributeError):
        raise InvalidAPKError(
            'Cannot get package name from {}'.format(apkfilename))


def make_override_name(config_name, path):
    """Return a filename with .override.customer suffix.

    config_name -- config name, like a20-kewang_35m
    path -- path to original file, like vanzo/custom_app/Android.mk
    """

    customer = config_name.split('-')[1]
    return '{}.override.{}'.format(path, customer)


def files_match_under_dir(path, func=lambda x: True):
    """Return a list of filenames that subpath relative to path
    make func return True.

    path -- dir to be searched
    func -- conditional function
    """

    ret = []
    for root, dirs, files in os.walk(path):
        for filename in dirs + files:
            full_path = os.path.join(root, filename)
            if func(full_path):
                ret.append(full_path)
    return ret


def ensure_dir_override_exist(config_name, path):
    """If corresponding override folder does not exist, create an empty one;
    otherwise return the first match.

    config_name -- config name, corresponding config's patch overrides must exist
    path -- path to original folder, like vanzo/custom_app

    return -- path to override folder, relative to src root.
    """

    overrides_path = get_config_overrides_path(config_name)

    regex = re.compile(r'{}\.override\.[^/]+$'.format(re.escape(path)))
    dirs = files_match_under_dir(
        overrides_path, lambda x: regex.search(x) and os.path.isdir(x))

    if not dirs:
        dst = os.path.join(
            overrides_path, make_override_name(config_name, path))
        fs.mkdir(dst)
        return dst
    return dirs[0]


def ensure_file_override_exist(config_name, path):
    """If corresponding override file does not exist, make a copy from src
    or create an empty file if it does not exist in src.

    config_name -- config name, corresponding config's patch_overrides must exist
    path -- path to original file, like vanzo/custom_app/Android.mk

    Throws -- ConflictOverridesError if multiple overrides exist

    return -- path to override file, relative to src root.
    """

    overrides_path = get_config_overrides_path(config_name)

    regex = re.compile(r'{}\.override\.[^/]+$'.format(re.escape(path)))
    files = files_match_under_dir(
        overrides_path, lambda x: regex.search(x) and os.path.isfile(x))

    if len(files) > 1:
        raise ConflictOverridesError('Multiple overrides {}'.format(path))

    if not files:
        dst = os.path.join(
            overrides_path, make_override_name(config_name, path))
        fs.mkdir(os.path.dirname(dst))
        if not os.path.exists(path):
            touch(dst)
        else:
            shutil.copy(path, dst)
        return dst
    return files[0]


class APKInjector(object): #pylint: disable=R0903
    """Put apk into system in a way that build system
    will make odex during building to speed up rebooting."""

    ApkInfo = collections.namedtuple('ApkInfo', 'path name so')

    def _find_all_apks(self, apk_folder): #pylint: disable=R0201
        """Find all apks under apk_folder recursively."""

        for root, _, files in os.walk(apk_folder):
            return [os.path.join(root, x) for x in files
                    if re.search(r'\.apk$', x, re.I)]

    def _get_apk_info(self, apkfilename): #pylint: disable=R0201
        """Return a namedtuple of package name and all so in this apk."""

        return APKInjector.ApkInfo(
            path=apkfilename,
            name=get_apk_package_name(apkfilename),
            so=get_filenames_in_apk(apkfilename, re.compile(r'\.so$')))

    def _copy_all_apks_to_custom_app(self, info, custom_app): #pylint: disable=R0201,C0301
        """Copy all apks to custom_app folder under overrides, with the
        package name."""

        for i in info:
            shutil.copy(i.path, os.path.join(custom_app, i.name) + '.apk')

    def _update_cpp_mk(self, info, mk_filename): #pylint: disable=R0201,C0301
        """Update cross-platform-platform.mk under overrides."""

        with open(mk_filename, 'a') as outf:
            outf.write('\n')
            for ainfo in info:
                outf.write('PRODUCT_PACKAGES += {}\n'.format(ainfo.name))

    def _does_apk_support_64bit(self, soes): #pylint: disable=R0201
        """If apk support 64bit."""

        return any('/arm64-v8a/' in x for x in soes)

    def _exclude_unsupported_so(self, soes):
        """Exclude all unneccesary so."""
        def _does_path_32bit(path):
            """If this path refers to a 32bit so."""
            return any(x in path for x in ('/armeabi/', '/armeabi-v7a/'))

        def _does_path_x86(path):
            """If this path refers to a x86 so."""

            return '/x86/' in path

        if self._does_apk_support_64bit(soes):
            soes = [aso for aso in soes if not _does_path_32bit(aso)]
        return [aso for aso in soes if not _does_path_x86(aso)]

    def _update_android_mk(self, info, mk_filename): #pylint: disable=R0201
        """Update Android.mk under overrides."""

        local_path_defined = True
        with open(mk_filename) as inf:
            if not re.search(r'\bLOCAL_PATH\b', inf.read(), re.M):
                local_path_defined = False

        with open(mk_filename, 'a') as outf:
            if not local_path_defined:
                outf.write('LOCAL_PATH := $(call my-dir)\n')
            for i in info:
                outf.write('include $(CLEAR_VARS)\n')
                outf.write('LOCAL_MODULE := {}\n'.format(i.name))
                outf.write('LOCAL_MODULE_TAGS := optional\n')
                bit = '64' if self._does_apk_support_64bit(i.so) else '32'
                outf.write('LOCAL_MULTILIB := {}\n'.format(bit))
                outf.write('LOCAL_SRC_FILES := $(LOCAL_MODULE).apk\n')
                outf.write('LOCAL_MODULE_CLASS := APPS\n')
                outf.write('LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)\n') #pylint: disable=C0301
                outf.write('LOCAL_CERTIFICATE := PRESIGNED\n')
                outf.write('LOCAL_MODULE_PATH := $(TARGET_OUT)/app\n')
                soes = self._exclude_unsupported_so(i.so)
                if soes:
                    outf.write('LOCAL_PREBUILT_JNI_LIBS := \\\n')
                for index, aso in enumerate(soes):
                    ends = '\\' if index != len(soes) - 1 else ''
                    outf.write('        @{} {}\n'.format(aso, ends))
                outf.write('include $(BUILD_PREBUILT)\n')
                outf.write('\n')

    def inject(self, config_name, apk_folder):
        """Do it."""

        apks = self._find_all_apks(apk_folder)
        if not apks:
            return

        info = [self._get_apk_info(x) for x in apks]
        custom_app_dir = ensure_dir_override_exist(
            config_name, 'beetec/custom_app')
        self._copy_all_apks_to_custom_app(info, custom_app_dir)

        cpp_mk = ensure_file_override_exist(
            config_name, 'beetec/cross-platform-packages.mk')
        self._update_cpp_mk(info, cpp_mk)

        android_mk = ensure_file_override_exist(
            config_name, 'beetec/custom_app/Android.mk')
        self._update_android_mk(info, android_mk)


def _go():  #pragma: no cover
    """Suppress pylint Redefining name from outer space warnings."""

    injector = APKInjector()
    config_name = sys.argv[1]
    apk_folder = sys.argv[2]

    validate_config_name(config_name)
    injector.inject(config_name, apk_folder)


if __name__ == '__main__': #pragma: no cover
    _go()
