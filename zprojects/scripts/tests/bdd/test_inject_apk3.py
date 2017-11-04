#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'zprojects/scripts'))

import pytest
from pytest_bdd import scenario, given, when, then

from pyutils import fs
import inject_apk


@scenario('inject_apk.feature', 'Existing config have corresponding overrides')
def test_3():
    pass


@given('an existing config a20-moxiaoming')
def create_config(site):
    fs.rm('zprojects/{}'.format(site))
    fs.mkdir('zprojects/{0}/{0}/patch_overrides/overrides'.format(site))


@given('there is vanzo/cross-platform-packages.mk override')
def config_has_cpp(site):
    fs.mkdir('zprojects/{0}/{0}/patch_overrides/overrides/vanzo'.format(site))
    with open('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/cross-platform-packages.mk.override.xyz'.format(site), 'w') as outf:
        outf.write('PRODUCT_PACKAGES += IndexZone\n')


@given('there is vanzo/custom_app override')
def config_has_custom_app(site):
    fs.mkdir('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/custom_app.override.xyz'.format(site))
    fs.touch('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/custom_app.override.xyz/com.test.a.apk'.format(site))


@given('there is vanzo/custom_app/Android.mk override')
def config_has_android_mk(site):
    fs.mkdir('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/custom_app'.format(site))
    with open('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/custom_app/Android.mk.override.xyz'.format(site), 'w') as outf:
        outf.write("""LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := com.test.a
LOCAL_MODULE_TAGS := optional
LOCAL_MULTILIB := 32
LOCAL_SRC_FILES := $(LOCAL_MODULE).apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_MODULE_PATH := $(TARGET_OUT)/app
include $(BUILD_PREBUILT)\n""")


@when('inject apk is called')
def call_inject_apk(site):
    injector = inject_apk.APKInjector()
    inject_apk.validate_config_name(site)
    injector.inject(site, '/var/www/b')


@then('injected apk has been added to vanzo/cross-platform-packages.mk')
def has_cpp(site):
    with open('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/cross-platform-packages.mk.override.xyz'.format(site)) as inf:
        content = inf.read().strip()
    assert 'PRODUCT_PACKAGES += IndexZone\n\nPRODUCT_PACKAGES += com.google.android.gms' == content


@then('injected apk has been added to vendor/custom_app folder')
def has_apk(site):
    assert set(os.listdir('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/custom_app.override.xyz'.format(site))) == {'com.test.a.apk', 'com.google.android.gms.apk'}


@then('injected apk\'s info has been added to vencor/custom_app/Android.mk')
def has_mk(site):
    suppose_to_be = """LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := com.test.a
LOCAL_MODULE_TAGS := optional
LOCAL_MULTILIB := 32
LOCAL_SRC_FILES := $(LOCAL_MODULE).apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_MODULE_PATH := $(TARGET_OUT)/app
include $(BUILD_PREBUILT)
include $(CLEAR_VARS)
LOCAL_MODULE := com.google.android.gms
LOCAL_MODULE_TAGS := optional
LOCAL_MULTILIB := 64
LOCAL_SRC_FILES := $(LOCAL_MODULE).apk
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_CERTIFICATE := PRESIGNED
LOCAL_MODULE_PATH := $(TARGET_OUT)/app
LOCAL_PREBUILT_JNI_LIBS := \\
        @lib/arm64-v8a/libAppDataSearch.so \\
        @lib/arm64-v8a/libNearbyApp.so \\
        @lib/arm64-v8a/libWhisper.so \\
        @lib/arm64-v8a/libconscrypt_gmscore_jni.so \\
        @lib/arm64-v8a/libgames_rtmp_jni.so \\
        @lib/arm64-v8a/libgcastv2_base.so \\
        @lib/arm64-v8a/libgcastv2_support.so \\
        @lib/arm64-v8a/libgms-ocrclient.so \\
        @lib/arm64-v8a/libgmscore.so \\
        @lib/arm64-v8a/libjgcastservice.so \\
        @lib/arm64-v8a/libsslwrapper_jni.so 
include $(BUILD_PREBUILT)"""
    with open('zprojects/{0}/{0}/patch_overrides/overrides/vanzo/custom_app/Android.mk.override.xyz'.format(site)) as inf:
        content = inf.read().strip()
    assert content == suppose_to_be
