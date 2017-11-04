#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=C
# pylint: disable=R
# Using the global statement
# pylint: disable=W0603

"""
Please run:
    sudo ln -sf ~/.../vanzo_common2.py  /usr/lib/python2.6/vanzo_common2.py
    So this lib can be accessed from every where
"""

import commands
import datetime
import os
import sys
import tempfile
import glob
import errno
import re
import shutil
import filecmp
import subprocess
from xlwt import Workbook
from xlwt import Borders
from xlwt import XFStyle
from xlwt import Font
from xlwt import Formula
from dateutil import parser
from dateutil import relativedelta

from xml.etree import ElementTree
from xml.dom.minidom import parse
import sqlite3
from hashlib import md5
from xml.etree import ElementTree
from urllib import urlopen
import json
import contextlib

__version__ = "2.00"

###############################################################################
#                         colorized output
###############################################################################
_YELLOW = '\033[93m'
_GREEN = '\033[92m'
_RED = '\033[91m'
_WHITE = '\033[1;37m'
_END = '\033[0m'

def _color(msg, color):
    if os.isatty(1) and os.environ['TERM'] == 'xterm':
        return color + msg + _END
    else:
        return msg


def _red(msg):
    return _color(msg, _RED)


def _green(msg):
    return _color(msg, _GREEN)


def _yellow(msg):
    return _color(msg, _YELLOW)


def _white(msg):
    return _color(msg, _WHITE)

MAP_KPI_QUANTITY = {u"软件配置组":110, u"软件应用组":40, u"软件驱动组":20, u"软件测试部":20}

################################################################################
########@@ General func
################################################################################

def my_log(msg):
    msg2 = "===%s@" % __name__
    msg3 = msg2 + datetime.datetime.now().strftime("%Y%m%d:%H%M%S") + "===" + msg + "\n"
    with open("logs_vc2.txt","a+") as outfile1:
        outfile1.write(msg3)

def my_dbg(msg, logit=False):
    msg2 = "===%s@" % __name__
    msg3 = msg2 + datetime.datetime.now().strftime("%Y%m%d:%H%M%S") + "===" + msg + "\n"
    print(msg3)
    if logit:
        my_log(msg)

def my_sys(cmd):
    return os.system(cmd)

def my_copy(src1, target1):
    if os.path.exists(src1):
        shutil.copy(src1, target1)

def my_exit(msg, code):
    my_dbg(msg)
    sys.exit(code)

def npn(project1):
    pos1 = project1.rfind(".")
    if pos1 > 0:
        project2 = project1[pos1:]
    else:
        project2 = project1

    for one in fallback_rules_keys_i:
        if one == "_aphone":
            break
        if project2.endswith(one):
            project2 = project2.rpartition(one)[0]
        elif one + '_' in project2:
            project2 = project2.replace(one + '_', "_")

    project2 = project2.replace("mt82ali_", "mt82_")
    project2 = project2.replace("mt72ali_", "mt72_")
    project2 = project2.replace("mt92ali_", "mt92_")

    if pos1 > 0:
        project2 = project1[:pos1] + project2
    return project2

def my_split(str1, splitter=","):
    """
    split always return one element even if you give it empty str,we don't need it
    """
    return [one for one in str1.split(splitter) if len(one.strip()) > 0]

def _duplicate_if_link_file(file1):
    if os.path.islink(file1):
        my_sys("cp %s tmp1; rm %s; mv tmp1 %s" % (file1, file1, file1))

def _my_rename_or_remove(file1, file2, remove=False):
    """
    when remove file1, maybe some other link to it (thus *DEAD* after its target deleted)
        if file2 is None, files that link to file1 will be linked to file2
    """
    if file2 != None:
        dir1 = os.path.dirname(file1)
        file1a = os.path.basename(file1)
        file2a = os.path.basename(file2)
        cmd = "find %s -type l" % dir1
        list1 = commands.getstatusoutput(cmd)[1].split()
        for one in list1:
            cmd = "ls -l %s" % one
            output2 = commands.getstatusoutput(cmd)[1].split(">")[-1].strip()
            output2 = os.path.basename(output2)
            if output2 == file1a:
                if os.path.basename(one) == file2a:
                    cmd = "rm -f %s;cp %s %s" % (one, file1, one)
                else:
                    cmd = "ln -sf %s %s" % (file2a, one)
                my_dbg(_yellow("update link:%s" % cmd), True)
                my_sys(cmd)
    if remove:
        my_sys("rm -rf %s" % file1)
    else:
        my_sys("mv -f %s %s" % (file1, file2))

def my_rename(file1, file2):
    _my_rename_or_remove(file1, file2)

def my_remove(file1, file2=None):
    _my_rename_or_remove(file1, file2, True)

def get_ip():
    """
    Get the ip address of current PC, last 2 digits
    """
    tmpstr = commands.getstatusoutput("ifconfig | grep 192.168.1.")[1]
    pos = tmpstr.find("192.168.1.")
    return tmpstr[pos + 10:pos + 13].strip()

def samba_run(cmd, server, where, needs_output=False):
    """
    run cmd on samba server with smbclient under some directory
    If needs_output, return the result
    """
    if needs_output:
        cmd2 = """smbclient -c '%s' //192.168.1.%s/%s/ -U%%""" % (cmd, server, where)
        return commands.getstatusoutput(cmd2)[1]
    else:
        cmd2 = """smbclient -c '%s' //192.168.1.%s/%s/ -U%% > /dev/null 2>&1""" % (cmd, server, where)
        my_sys(cmd2)

def samba_run_d(cmd, server, needs_output=False):
    """
    run cmd on samba server with smbclient under dailybuild
    """
    return samba_run(cmd, server, "dailybuild", needs_output)

def samba_run_d2(cmd, server, needs_output=False):
    """
    run cmd on samba server with smbclient under dailybuild2
    """
    return samba_run(cmd, server, "dailybuild2", needs_output)

def samba_run_o(cmd, server, needs_output=False):
    """
    run cmd on samba server with smbclient under ondemand
    """
    return samba_run(cmd, server, "ondemand", needs_output)

def file2list(file1):
    """
    gen list from file
    """
    return [line.strip() for line in open(file1)]

def list2file(list1, file1):
    """
    write list to file
    """
    with open(file1, "w+") as outfile:
        for one in list1:
            print >> outfile, one

def kill_android_app(app):
    tmpstr = commands.getstatusoutput("adb shell ps")[1].split("\n")
    for one in tmpstr:
        if app in one:
            list1 = one.split()
            my_sys("adb shell kill %s" % list1[1])
            return

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno != errno.EEXIST or not os.path.isdir(path):
            raise

def get_keyed_list_from_file(file1, key1, key2 = None):
    list1 = []
    with open(file1) as infile:
        in1 = False
        for line in infile:
            if in1:
                if key2 != None and not key2 in line: # reach end mark
                    in1 = False
                    continue
                if not line.strip():                  # empty line
                    in1 = False
                    continue
                item = line.replace("\\", "").strip()
                if not item:                          # only \
                    continue
                list1.append(item)
                if not "\\" in line:                  # no \
                    in1 = False
                    continue
            elif re.match(r'^{0}\W'.format(key1), line):
                in1 = True
    return list1

def get_dimension_from_project_config(file2):
    if file2 == None or not os.path.exists(file2):
        return
    width = 0
    height = 0
    with open(file2) as in_file:
        lines = in_file.readlines()
        for line in lines:
            if line.startswith("LCM_WIDTH"):
                width = int(line.split("=")[1].split()[0].strip())
            elif line.startswith("LCM_HEIGHT"):
                height = int(line.split("=")[1].split()[0].strip())
    if width > 0 and height > 0:
        return (width, height)

def get_resolution_from_dimension(size1, project_info=None):
    if not type(size1) in (list, tuple):
        size1 = my_split(size1)
    size2 = (int(size1[0]), int(size1[1]))
    lcm_density = "mdpi"
    pixels = size2[0] * size2[1]
    if pixels <= 240 * 432:
        lcm_density = "ldpi"
    if pixels >= 480 * 800:
        lcm_density = "hdpi"
    if pixels >= 640 * 960:
        lcm_density = "xhdpi"
    if pixels >= 1080 * 1920:
        if project_info != None and project_info["age"] < PROJECT_INFO["mt6592jb9"]["age"]:
            lcm_density = "xhdpi"
        else:
            lcm_density = "xxhdpi"
    return lcm_density

def get_customer_info_from_redmine():
  ret,out1= commands.getstatusoutput("""curl -H "Content-Type: application/xml" -X GET -H "X-Redmine-API-Key: 2b6ce8c30c9b51f94315bc94b0743a643dcc77da" http://192.168.1.62/redmine/customers.xml 2>/dev/null""")
  pos1 = out1.find("<?xml version")
  out1 = out1[pos1:]
  root = ElementTree.fromstring(out1)
  p=root.findall('customer')
  list1 = []
  for oneper in p:
      map2 =  {}
      for child in oneper.getchildren():
          map2[child.tag] = child.text
      list1.append(map2)
  return list1

def get_contact_info_from_redmine(cid):
  ret,out1= commands.getstatusoutput("""curl -H "Content-Type: application/xml" -X GET -H "X-Redmine-API-Key: 2b6ce8c30c9b51f94315bc94b0743a643dcc77da" http://192.168.1.62/redmine/customers/%s.xml 2>/dev/null""" % cid)
  pos1 = out1.find("<?xml version")
  out1 = out1[pos1:]
  root = ElementTree.fromstring(out1)
  p=root.findall('contacts')[0].findall('contact')
  list1 = []
  for oneper in p:
      map2 =  {}
      for child in oneper.getchildren():
          map2[child.tag] = child.text
      list1.append(map2)
  return list1

def normalize_size(size1):
    return int(size1[0]), int(size1[1])

def normalize_cwd(dir1):
    """so we can run from anywhere in codebase"""
    while not os.path.exists(dir1):
        os.chdir("../")
        if os.getcwd() == "/":
            my_dbg(_red("where r u? I can not find code base!"))
            sys.exit(-1)

def get_image_format_from_size(size1, project_name):
    project_info=get_project_info(project_name)
    id_ = get_project_info(project_name)['id']

    ret1 = "unknown"
    size2 = normalize_size(size1)
    if size2 == (540, 960):
        ret1 = "qhd"
    elif size2 == (640, 960):
        ret1 =  "lqhd"
    elif size2 == (480, 800):
        ret1 =  "wvga"
    elif size2 == (480, 854):
        ret1 =  "fwvga"
    elif size2 == (320, 480):
        ret1 =  "hvga"
    elif size2 == (800, 480):
        ret1 =  "wvgal"
    elif size2 == (720, 1280):
        #if any(id_.startswith(i) for i in ('mt6589', 'mt6572jb3', 'mt6582')):
        if project_info["age"] >= PROJECT_INFO["mt6589jb2"]["age"]:
            ret1 = "hd720"
        else:
            ret1 = "hd"
    elif size2 == (240, 320):
        ret1 =  "qvga"
    elif size2 == (1080, 1920):
        ret1 =  "fhd"
    elif size2 == (1200,1920):
        ret1 = "wuxga"
    if id_.startswith('mt6572') and ('_td_' in project_name or project_name.endswith('_td')):
        ret1 = 'cmcc_' + ret1
    elif project_info["android"] in ('44', '45') and ('_lte_' in project_name or project_name.endswith('_lte')):
        ret1 = 'cmcc_lte_' + ret1
    return ret1

PROJECT_INFO = {}

def _is_mttype(project_name, startswith, keys):
    # tokens that a signaficant in project name
    sensentive_keys = set(('v3', 'r4', 'ics', 'jb', 'jb2', 'jb3', 'jb5', 'jb7', 'jb9', 'kk', 'cta', 'lca', 'tdd', 'lte', 'ds5', 'ds3','ds',))
    # project name must starts with one of (startswith)
    if not any([project_name.startswith(i) for i in startswith]):
        return False
    # project name must have all (keys)
    if not all([_token_in_project(project_name, i) for i in keys]):
        return False
    # project name must not have (sensentive_keys - keys)
    sensentive_keys.difference_update(keys)
    if any([_token_in_project(project_name, i) for i in sensentive_keys]):
        return False

    return True

def _is_mt6573v3(project_name):
    return _is_mttype(project_name, ('mt73_', 'mt13_'), ('v3',))

def _is_mt6513r4(project_name):
    return _is_mttype(project_name, ('mt13_', 'mt73_'), ('r4',))

def _is_mt6575icsr2(project_name):
    return _is_mttype(project_name, ('mt75r2_',), ('ics',))

def _is_mt6575ics(project_name):
    return _is_mttype(project_name, ('mt75_', 'mt15_'), ('ics',))

def _is_mt6575jbcta(project_name):
    return _is_mttype(project_name, ('mt75_',), ('jb', 'cta'))

def _is_mt6575jb(project_name):
    return _is_mttype(project_name, ('mt75_',), ('jb',))

def _is_mt6575gbr2cta(project_name):
    return _is_mttype(project_name, ('mt75r2_',), ('cta'))

def _is_mt6575gbr2(project_name):
    return _is_mttype(project_name, ('mt75r2_',), ())

def _is_mt6575gb(project_name):
    return _is_mttype(project_name, ('mt75_',), ())

def _is_mt6515cta(project_name):
    return _is_mttype(project_name, ('mt15m_',), ('cta',))

def _is_mt6515(project_name):
    return _is_mttype(project_name, ('mt15m_',), ())

def _is_mt6515mtdcta(project_name):
    return _is_mttype(project_name, ('mt15mtd_',), ('cta',))

def _is_mt6515mtd(project_name):
    return _is_mttype(project_name, ('mt15mtd_',), ())

def _is_mt6515icsmtd(project_name):
    return _is_mttype(project_name, ('mt15mtd_',), ('ics',))

def _is_mt6515cmcccta(project_name):
    return _is_mttype(project_name, ('mt15cmcc_',), ('cta',))

def _is_mt6515cmcc(project_name):
    return _is_mttype(project_name, ('mt15cmcc_',), ())

def _is_mt6517tdcta(project_name):
    return _is_mttype(project_name, ('mt17td_',), ('ics', 'cta'))

def _is_mt6517td(project_name):
    return _is_mttype(project_name, ('mt17td_',), ('ics',))

def _is_mt6517cmcc(project_name):
    return _is_mttype(project_name, ('mt17cmcc_',), ('ics',))

def _is_mt6577ics(project_name):
    return _is_mttype(project_name, ('mt17_', 'mt77_'), ('ics',))

def _is_mt6577jbcta(project_name):
    return _is_mttype(project_name, ('mt17_', 'mt77_', 'mt17r2_'), ('jb', 'cta'))

def _is_mt6577jb(project_name):
    return _is_mttype(project_name, ('mt17_', 'mt77_', 'mt17r2_'), ('jb',))

def _is_mt6589jb2cmcc(project_name):
    return _is_mttype(project_name, ('mt89cmcc_',), ('jb2',))

def _is_mt6589jb2cta(project_name):
    return _is_mttype(project_name, ('mt89_',), ('jb2', 'cta'))

def _is_mt6589jb2(project_name):
    return _is_mttype(project_name, ('mt89_',), ('jb2',))

def _is_mt6589jb(project_name):
    return _is_mttype(project_name, ('mt89_',), ('jb',))

def _is_mt6572jb3(project_name):
    return _is_mttype(project_name, ('mt72_',), ('jb3',))

def _is_mt6572jb3nand(project_name):
    return _is_mttype(project_name, ('mt72_',), ('jb3', 'lca'))

def _is_mt6572jb3cta(project_name):
    return _is_mttype(project_name, ('mt72_',), ('jb3', 'cta',))

def _is_mt6572jb3nandcta(project_name):
    return _is_mttype(project_name, ('mt72_',), ('jb3', 'cta', 'lca'))

def _is_mt6572ali(project_name):
    return _is_mttype(project_name, ('mt72ali_',), ('jb3',))

def _is_mt6572alicta(project_name):
    return _is_mttype(project_name, ('mt72ali_',), ('jb3','cta',))

def _is_mt6572jb3cmcc(project_name):
    return _is_mttype(project_name, ('mt72cmcc_',), ('jb3',))

def _is_mt6572jb3nandcmcc(project_name):
    return _is_mttype(project_name, ('mt72cmcc_',), ('jb3','lca',))

def _is_mt6582jb5cta(project_name):
    return _is_mttype(project_name, ('mt82_',), ('jb5','cta',))

def _is_mt6582jb5cmcc(project_name):
    return _is_mttype(project_name, ('mt82cmcc_',), ('jb5',))

def _is_mt6582jb5(project_name):
    return _is_mttype(project_name, ('mt82_',), ('jb5',))

def _is_mt6582alicta(project_name):
    return _is_mttype(project_name, ('mt82ali_',), ('jb5','cta',))

def _is_mt6582ali(project_name):
    return _is_mttype(project_name, ('mt82ali_',), ('jb5',))

# Vanzo:yucheng on: Wed, 15 Jan 2014 13:32:15 +0800
# Added for freezed projects
def _is_mt6582freeze(project_name):
    return _is_mttype(project_name, ('mt82_',), ('freeze',))
# End of Vanzo: yucheng
def _is_mt6592jb9(project_name):
    return _is_mttype(project_name, ('mt92_',), ('jb9',))

def _is_mt6592tdd(project_name):
    return _is_mttype(project_name, ('mt92_',), ('tdd',))

def _is_mt6592jb9cta(project_name):
    return _is_mttype(project_name, ('mt92_',), ('jb9','cta',))

def _is_mt6592tddcta(project_name):
    return _is_mttype(project_name, ('mt92_',), ('tdd','cta',))

def _is_mt6592alijb9(project_name):
    return _is_mttype(project_name, ('mt92ali_',), ('jb9',))

def _is_mt6592alitdd(project_name):
    return _is_mttype(project_name, ('mt92ali_',), ('tdd',))

def _is_mt6571jb7(project_name):
    return _is_mttype(project_name, ('mt71_',), ('jb7',))

def _is_mt6571jb7nand(project_name):
    return _is_mttype(project_name, ('mt71_',), ('jb7', 'lca'))

def _is_mt6571jb7cta(project_name):
    return _is_mttype(project_name, ('mt71_',), ('jb7', 'cta',))

def _is_mt6571jb7nandcta(project_name):
    return _is_mttype(project_name, ('mt71_',), ('jb7', 'lca', 'cta',))

def _is_mt6582kk(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk',))

def _is_mt6582kktdd(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk','tdd',))

def _is_mt6592kk(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk',))

def _is_mt6592kktdd(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk','tdd',))

def _is_mt6582kklte(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk','lte',))

def _is_mt6592kklte(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk','lte',))

def _is_mt6582kkltecta(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk','lte','cta',))

def _is_mt6592kkltecta(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk','lte','cta',))

def _is_mt6582kkltecmcc(project_name):
    return _is_mttype(project_name, ('mt82cmcc_',), ('kk','lte',))

def _is_mt6592kkltecmcc(project_name):
    return _is_mttype(project_name, ('mt92cmcc_',), ('kk','lte',))

def _is_mt6571kk(project_name):
    return _is_mttype(project_name, ('mt71_',), ('kk',))

def _is_mt6571kklca(project_name):
    return _is_mttype(project_name, ('mt71_',), ('kk', 'lca'))

def _is_mt6572kk(project_name):
    return _is_mttype(project_name, ('mt72_',), ('kk',))

def _is_mt6572kklca(project_name):
    return _is_mttype(project_name, ('mt72_',), ('kk', 'lca'))

def _is_mt6582kklteds3m(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk','lte','ds3',))

def _is_mt6592kklteds3m(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk','lte','ds3',))

def _is_mt6582kklteds3mcta(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk','lte','ds3','cta',))

def _is_mt6592kklteds3mcta(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk','lte','ds3','cta',))

def _is_mt6595kklte(project_name):
    return _is_mttype(project_name, ('mt95_',), ('kk','lte'))

def _is_mt6595kkltecta(project_name):
    return _is_mttype(project_name, ('mt95_',), ('kk','lte','cta'))

def _is_mt6595kklteds(project_name):
    return _is_mttype(project_name, ('mt95_',), ('kk','lte','ds'))
def _is_mt6595kkltedscta(project_name):
    return _is_mttype(project_name, ('mt95_',), ('kk','lte','ds','cta'))
def _is_mt6582kklteds5m(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk','lte','ds5',))

def _is_mt6592kklteds5m(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk','lte','ds5',))

def _is_mt6582kklteds5mcta(project_name):
    return _is_mttype(project_name, ('mt82_',), ('kk','lte','ds5','cta',))

def _is_mt6592kklteds5mcta(project_name):
    return _is_mttype(project_name, ('mt92_',), ('kk','lte','ds5','cta',))

def _is_mt6732kklte(project_name):
    return _is_mttype(project_name, ('mt6732_',), ('kk','lte'))

def _is_mt6752kklte(project_name):
    return _is_mttype(project_name, ('mt6752_',), ('kk','lte'))

def _is_mt6732kkltecta(project_name):
    return _is_mttype(project_name, ('mt6732_',), ('kk','lte', 'cta',))

def _is_mt6752kkltecta(project_name):
    return _is_mttype(project_name, ('mt6752_',), ('kk','lte', 'cta',))

def _is_mt6732kklteali(project_name):
    return _is_mttype(project_name, ('mt6732ali_',), ('kk','lte'))

def _is_mt6752kklteali(project_name):
    return _is_mttype(project_name, ('mt6752ali_',), ('kk','lte'))

PROJECT_INFO["mt6573v3"] = {"id":"mt6573v3", "age":250, "vtrunk":"vtrunk-v3", "repo":"platform_gingerbread", "project":"vanzo73_gb", "android":"23", "images_nand":(
        "MT6573_Android_scatter.txt",
        "preloader_vanzo73_gb.bin",
        "uboot_vanzo73_gb.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6513r4"] = {"id":"mt6513r4", "age":260, "vtrunk":"vtrunk-r4", "repo":"platform_gingerbread", "project":"vanzo13_6626_gb", "android":"23", "images_nand":(
        "MT6573_Android_scatter.txt",
        "preloader_vanzo13_6626_gb.bin",
        "uboot_vanzo13_6626_gb.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6575gb"] = {"id":"mt6575gb", "age":300, "vtrunk":"vtrunk", "repo":"platform_gb2", "project":"vanzo75_gb2", "android":"23", "images_emmc":(
        "MT6575_Android_scatter_emmc.txt",
        "preloader_vanzo75_gb2.bin",
        "uboot_vanzo75_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6575ics"] = {"id":"mt6575ics", "age":400, "vtrunk":"vtrunk", "repo":"platform_ics", "project":"vanzo75_cu_ics", "android":"40", "images_emmc":(
        "MT6575_Android_scatter_emmc.txt",
        "preloader_vanzo75_cu_ics.bin",
        "uboot_vanzo75_cu_ics.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6515"] = {"id":"mt6515", "age":500, "vtrunk":"vtrunk-6626", "repo":"platform_gb2", "project":"vanzo15_6626_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo15_6626_gb2.bin",
        "uboot_vanzo15_6626_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6515cta"] = {"id":"mt6515cta", "age":501, "vtrunk":"cta-6626", "repo":"platform_gb2", "project":"vanzo15_6626_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo15_6626_gb2.bin",
        "uboot_vanzo15_6626_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6577ics"] = {"id":"mt6577ics", "age":600, "vtrunk":"vtrunk-77", "repo":"platform_ics", "project":"vanzo77_ics2", "android":"40", "images_nand":(
        "MT6577_Android_scatter.txt",
        "preloader_vanzo77_ics2.bin",
        "uboot_vanzo77_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
), "images_emmc":(
        "MT6577_Android_scatter_emmc.txt",
        "preloader_vanzo77_ics2.bin",
        "uboot_vanzo77_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6575icsr2"] = {"id":"mt6575icsr2", "age":700, "vtrunk":"vtrunk-6628", "repo":"platform_ics", "project":"vanzo75_ics", "android":"40", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo75_ics.bin",
        "uboot_vanzo75_ics.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
), "images_emmc":(
        "MT6575_Android_scatter_emmc.txt",
        "preloader_vanzo75_ics.bin",
        "uboot_vanzo75_ics.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6575gbr2"] = {"id":"mt6575gbr2", "age":800, "vtrunk":"vtrunk-6628", "repo":"platform_gb2", "project":"vanzo75_6628_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo75_6628_gb2.bin",
        "uboot_vanzo75_6628_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6575gbr2cta"] = {"id":"mt6575gbr2cta", "age":801, "vtrunk":"cta-6628", "repo":"platform_gb2", "project":"vanzo75_6628_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo75_6628_gb2.bin",
        "uboot_vanzo75_6628_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6517td"] = {"id":"mt6517td", "age":900, "vtrunk":"vtrunk-17td", "repo":"platform_ics", "project":"vanzo17_td3001_ics2", "android": "40", "images_nand":(
        "MT6577_Android_scatter.txt",
        "preloader_vanzo17_td3001_ics2.bin",
        "uboot_vanzo17_td3001_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
), "images_emmc":(
        "MT6577_Android_scatter_emmc.txt",
        "preloader_vanzo17_td3001_ics2.bin",
        "uboot_vanzo17_td3001_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6517tdcta"] = {"id":"mt6517tdcta", "age":901, "vtrunk":"cta-17td", "repo":"platform_ics", "project":"vanzo17_td3001_ics2", "android": "40", "images_nand":(
        "MT6577_Android_scatter.txt",
        "preloader_vanzo17_td3001_ics2.bin",
        "uboot_vanzo17_td3001_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
), "images_emmc":(
        "MT6577_Android_scatter_emmc.txt",
        "preloader_vanzo17_td3001_ics2.bin",
        "uboot_vanzo17_td3001_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6577jb"] = {"id":"mt6577jb", "age":1100, "vtrunk":"vtrunk", "repo":"platform_jb", "project":"vanzo77_twn_jb", "android": "41", "images_emmc":(
        "MT6577_Android_scatter_emmc.txt",
        "preloader_vanzo77_twn_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
), "images_nand":(
        "MT6577_Android_scatter.txt",
        "preloader_vanzo77_twn_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6577jbcta"] = {"id":"mt6577jbcta", "age":1101, "vtrunk":"cta", "repo":"platform_jb", "project":"vanzo77_twn_jb", "android": "41", "images_emmc":(
        "MT6577_Android_scatter_emmc.txt",
        "preloader_vanzo77_twn_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
), "images_nand":(
        "MT6577_Android_scatter.txt",
        "preloader_vanzo77_twn_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6575jb"] = {"id":"mt6575jb", "age":1200, "vtrunk":"vtrunk", "repo":"platform_jb", "project":"vanzo75_twn_jb", "android": "41", "images_emmc":(
        "MT6575_Android_scatter_emmc.txt",
        "preloader_vanzo75_twn_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
        "EBR2",
), "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo75_twn_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6575jbcta"] = {"id":"mt6575jbcta", "age":1201, "vtrunk":"cta", "repo":"platform_jb", "project":"vanzo75_twn_jb", "android": "41", "images_emmc":(
        "MT6575_Android_scatter_emmc.txt",
        "preloader_vanzo75_twn_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6515mtd"] = {"id":"mt6515mtd", "age":1300, "vtrunk":"vtrunk-15td", "repo":"platform_gb2", "project":"vanzo15_td_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo15_td_gb2.bin",
        "uboot_vanzo15_td_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6515mtdcta"] = {"id":"mt6515mtdcta", "age":1301, "vtrunk":"cta-15td", "repo":"platform_gb2", "project":"vanzo15_td_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo15_td_gb2.bin",
        "uboot_vanzo15_td_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6589jb"] = {"id":"mt6589jb", "age":1500, "vtrunk":"vtrunk-89", "repo":"platform_jb", "project":"vanzo89_jb", "android": "41", "images_emmc":(
        "MT6589_Android_scatter_emmc.txt",
        "preloader_vanzo89_jb.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6515cmcc"] = {"id":"mt6515cmcc", "age":1600, "vtrunk":"vtrunk-cmcc", "repo":"platform_gb2", "project":"vanzo15_cmcc_td_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo15_cmcc_td_gb2.bin",
        "uboot_vanzo15_cmcc_td_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6515cmcccta"] = {"id":"mt6515cmcccta", "age":1601, "vtrunk":"cta-cmcc", "repo":"platform_gb2", "project":"vanzo15_cmcc_td_gb2", "android":"23", "images_nand":(
        "MT6575_Android_scatter.txt",
        "preloader_vanzo15_cmcc_td_gb2.bin",
        "uboot_vanzo15_cmcc_td_gb2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
)}

PROJECT_INFO["mt6515icsmtd"] = {"id":"mt6515icsmtd", "age":1602, "vtrunk":"vtrunk-15td", "repo":"platform_ics", "project":"vanzo15_td_ics2", "android":"40", "images_emmc":(
        "MT6575_Android_scatter_emmc.txt",
        "preloader_vanzo15_td_ics2.bin",
        "uboot_vanzo15_td_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6517cmcc"] = {"id":"mt6517cmcc", "age":1650, "vtrunk":"vtrunk-gemini", "repo":"platform_ics", "project":"vanzo17_cmcc_td_ics2", "android": "40", "images_nand":(
        "MT6577_Android_scatter.txt",
        "preloader_vanzo17_cmcc_td_ics2.bin",
        "uboot_vanzo17_cmcc_td_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
        "DSP_BL",
), "images_emmc":(
        "MT6577_Android_scatter_emmc.txt",
        "preloader_vanzo17_cmcc_td_ics2.bin",
        "uboot_vanzo17_cmcc_td_ics2.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "DSP_BL",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6589jb2"] = {"id":"mt6589jb2", "age":1700, "vtrunk":"vtrunk", "repo":"platform_89", "project":"vanzo89_wet_jb2", "android": "42", "images_emmc":(
        "MT6589_Android_scatter_emmc.txt",
        "preloader_vanzo89_wet_jb2.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6589jb2cmcc"] = {"id":"mt6589jb2cmcc", "age":1702, "vtrunk":"vtrunk-cmcc", "repo":"platform_89", "project":"vanzo89_cmcc_jb2", "android": "42", "images_emmc":(
        "MT6589_Android_scatter_emmc.txt",
        "preloader_vanzo89_cmcc_jb2.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6589jb2cta"] = {"id":"mt6589jb2cta", "age":1701, "vtrunk":"cta", "repo":"platform_89", "project":"vanzo89_wet_jb2", "android": "42", "images_emmc":(
        "MT6589_Android_scatter_emmc.txt",
        "preloader_vanzo89_wet_jb2.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6572jb3"] = {"id":"mt6572jb3", "age":1900, "vtrunk":"vtrunk", "repo":"platform_72", "project":"vanzo72_wet_jb3", "android": "42", "images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_wet_jb3.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572jb3nand"] = {"id":"mt6572jb3nand", "age":1901, "vtrunk":"vtrunk", "repo":"platform_72", "project":"vanzo72_wet_lca", "android": "42", "images_nand":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_wet_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",),
        "images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_wet_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572jb3cta"] = {"id":"mt6572jb3cta", "age":1902, "vtrunk":"cta", "repo":"platform_72", "project":"vanzo72_wet_jb3", "android": "42", "images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_wet_jb3.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572jb3nandcta"] = {"id":"mt6572jb3nandcta", "age":1903, "vtrunk":"cta", "repo":"platform_72", "project":"vanzo72_wet_lca", "android": "42", "images_nand":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_wet_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
)}

PROJECT_INFO["mt6572ali"] = {"id":"mt6572ali", "age":1910, "vtrunk":"vtrunk", "repo":"platform_72_ali", "project":"vanzo72_wet_jb3", "android": "42", "images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_wet_jb3.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572alicta"] = {"id":"mt6572alicta", "age":1911, "vtrunk":"cta", "repo":"platform_72_ali", "project":"vanzo72_wet_jb3", "android": "42", "images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_wet_jb3.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572jb3cmcc"] = {"id":"mt6572jb3cmcc", "age":1920, "vtrunk":"vtrunk-cmcc", "repo":"platform_72", "project":"vanzo72_et_cmcc_jb3", "android": "42", "images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_et_cmcc_jb3.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572jb3nandcmcc"] = {"id":"mt6572jb3nandcmcc", "age":1921, "vtrunk":"vtrunk-cmcc", "repo":"platform_72", "project":"vanzo72_et_cmcc_lca", "android": "42", "images_nand":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_et_cmcc_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
)}

PROJECT_INFO["mt6582jb5"] = {"id":"mt6582jb5", "age":2200, "vtrunk":"vtrunk", "repo":"platform_82", "project":"vanzo82_wet_jb5", "android": "42", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_wet_jb5.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582jb5cta"] = {"id":"mt6582jb5cta", "age":2201, "vtrunk":"cta", "repo":"platform_82", "project":"vanzo82_wet_jb5", "android": "42", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_wet_jb5.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582jb5cmcc"] = {"id":"mt6582jb5cmcc", "age":2202, "vtrunk":"vtrunk-cmcc", "repo":"platform_82", "project":"vanzo82_t_cmcc_jb5", "android": "42", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_t_cmcc_jb5.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582ali"] = {"id":"mt6582ali", "age":2300, "vtrunk":"vtrunk", "repo":"platform_82_ali", "project":"vanzo82_wet_jb5", "android": "42", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_wet_jb5.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582alicta"] = {"id":"mt6582alicta", "age":2301, "vtrunk":"cta", "repo":"platform_82_ali", "project":"vanzo82_wet_jb5", "android": "42", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_wet_jb5.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

# Vanzo:yucheng on: Wed, 15 Jan 2014 13:33:03 +0800
# Added for vtrunk MT6582 release branch: vtrunk-rel
PROJECT_INFO["mt6582freeze"] = {"id":"mt6582freeze", "age":2302, "vtrunk":"vtrunk-rel", "repo":"platform_82", "project":"vanzo82_wet_jb5", "android": "42", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_wet_jb5.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}
# End of Vanzo: yucheng
PROJECT_INFO["mt6592jb9"] = {"id":"mt6592jb9", "age":2500, "vtrunk":"vtrunk", "repo":"platform_92", "project":"vanzo92_wet_jb9", "android": "42", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_wet_jb9.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592tdd"] = {"id":"mt6592tdd", "age":2510, "vtrunk":"vtrunk", "repo":"platform_92", "project":"vanzo92_wet_tdd", "android": "42", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_wet_tdd.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592alijb9"] = {"id":"mt6592alijb9", "age":2520, "vtrunk":"vtrunk", "repo":"platform_92_ali", "project":"vanzo92_wet_jb9", "android": "42", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_wet_jb9.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592alitdd"] = {"id":"mt6592alitdd", "age":2521, "vtrunk":"vtrunk", "repo":"platform_92_ali", "project":"vanzo92_wet_tdd", "android": "42", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_wet_tdd.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592jb9cta"] = {"id":"mt6592jb9cta", "age":2530, "vtrunk":"cta", "repo":"platform_92", "project":"vanzo92_wet_jb9", "android": "42", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_wet_jb9.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592tddcta"] = {"id":"mt6592tddcta", "age":2531, "vtrunk":"cta", "repo":"platform_92", "project":"vanzo92_wet_tdd", "android": "42", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_wet_tdd.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}


PROJECT_INFO["mt6571jb7"] = {"id":"mt6571jb7", "age":2600, "vtrunk":"vtrunk", "repo":"platform_71", "project":"vanzo71_et_jb7", "android": "42", "images_emmc":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_et_jb7.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6571jb7nand"] = {"id":"mt6571jb7nand", "age":2601, "vtrunk":"vtrunk", "repo":"platform_71", "project":"vanzo71_et_lca", "android": "42", "images_nand":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_et_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",),
        "images_emmc":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_et_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6571jb7cta"] = {"id":"mt6571jb7cta", "age":2610, "vtrunk":"cta", "repo":"platform_71", "project":"vanzo71_et_jb7", "android": "42", "images_emmc":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_et_jb7.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6571jb7nandcta"] = {"id":"mt6571jb7nandcta", "age":2611, "vtrunk":"cta", "repo":"platform_71", "project":"vanzo71_et_lca", "android": "42", "images_nand":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_et_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",),
        "images_emmc":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_et_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6582kk"] = {"id":"mt6582kk", "age":2700, "vtrunk":"vtrunk", "repo":"platform_kk_82_92", "project":"vanzo82_cwet_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_cwet_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582kktdd"] = {"id":"mt6582kktdd", "age":2710, "vtrunk":"vtrunk", "repo":"platform_kk_82_92", "project":"vanzo82_cwet_td", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_cwet_td.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}


PROJECT_INFO["mt6592kk"] = {"id":"mt6592kk", "age":2800, "vtrunk":"vtrunk", "repo":"platform_kk_82_92", "project":"vanzo92_cwet_kk", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_cwet_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kktdd"] = {"id":"mt6592kktdd", "age":2810, "vtrunk":"vtrunk", "repo":"platform_kk_82_92", "project":"vanzo92_cwet_td", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_cwet_td.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582kklte"] = {"id":"mt6582kklte", "age":2900, "vtrunk":"vtrunk", "repo":"platform_kk_lt_82_92", "project":"vanzo82_lwt_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kklte"] = {"id":"mt6592kklte", "age":3000, "vtrunk":"vtrunk", "repo":"platform_kk_lt_82_92", "project":"vanzo92_lwt_kk", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582kkltecta"] = {"id":"mt6582kkltecta", "age":3010, "vtrunk":"cta", "repo":"platform_kk_lt_82_92", "project":"vanzo82_lwt_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kkltecta"] = {"id":"mt6592kkltecta", "age":3020, "vtrunk":"cta", "repo":"platform_kk_lt_82_92", "project":"vanzo92_lwt_kk", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582kkltecmcc"] = {"id":"mt6582kkltecmcc", "age":3030, "vtrunk":"cmcc", "repo":"platform_kk_lt_82_92", "project":"vanzo82_lwt_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kkltecmcc"] = {"id":"mt6592kkltecmcc", "age":3040, "vtrunk":"cmcc", "repo":"platform_kk_lt_82_92", "project":"vanzo92_lwt_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6571kk"] = {"id":"mt6571kk", "age":3100, "vtrunk":"vtrunk", "repo":"platform_kk_71_72", "project":"vanzo71_cwet_kk", "android": "44", "images_emmc":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_cwet_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6571kklca"] = {"id":"mt6571kklca", "age":3200, "vtrunk":"vtrunk", "repo":"platform_kk_71_72", "project":"vanzo71_cwet_lca", "android": "44", "images_nand":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_cwet_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
),"images_emmc":(
        "MT6571_Android_scatter.txt",
        "preloader_vanzo71_cwet_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572kk"] = {"id":"mt6572kk", "age":3300, "vtrunk":"vtrunk", "repo":"platform_kk_71_72", "project":"vanzo72_cwet_kk", "android": "44", "images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_cwet_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6572kklca"] = {"id":"mt6572kklca", "age":3400, "vtrunk":"vtrunk", "repo":"platform_kk_71_72", "project":"vanzo72_cwet_lca", "android": "44", "images_nand":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_cwet_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "secro.img",
),"images_emmc":(
        "MT6572_Android_scatter.txt",
        "preloader_vanzo72_cwet_lca.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
)}

PROJECT_INFO["mt6582kklteds3m"] = {"id":"mt6582kklteds3m", "age":3500, "vtrunk":"vtrunk", "repo":"platform_kk_lt_82_92_ds", "project":"vanzo82_lt_ds_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lt_ds_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kklteds3m"] = {"id":"mt6592kklteds3m", "age":3600, "vtrunk":"vtrunk", "repo":"platform_kk_lt_82_92_ds", "project":"vanzo92_lt_ds_kk", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_lt_ds_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582kklteds3mcta"] = {"id":"mt6582kklteds3mcta", "age":3610, "vtrunk":"cta", "repo":"platform_kk_lt_82_92_ds", "project":"vanzo82_lt_ds_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lt_ds_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kklteds3mcta"] = {"id":"mt6592kklteds3mcta", "age":3620, "vtrunk":"cta", "repo":"platform_kk_lt_82_92_ds", "project":"vanzo92_lt_ds_kk", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_lt_ds_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6595kklte"] = {"id":"mt6595kklte", "age":4000, "vtrunk":"vtrunk", "repo":"platform_kk_95", "project":"vanzo95_lwt_kk", "android": "44", "images_emmc":(
        "MT6595_Android_scatter.txt",
        "preloader_vanzo95_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6595kkltecta"] = {"id":"mt6595kkltecta", "age":4010, "vtrunk":"cta", "repo":"platform_kk_95", "project":"vanzo95_lwt_kk", "android": "44", "images_emmc":(
        "MT6595_Android_scatter.txt",
        "preloader_vanzo95_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6595kklteds"] = {"id":"mt6595kklteds", "age":4020, "vtrunk":"vtrunk", "repo":"platform_kk_95_ds", "project":"vanzo95_lwt_ds_kk", "android": "44", "images_emmc":(
        "MT6595_Android_scatter.txt",
        "preloader_vanzo95_lwt_ds_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

PROJECT_INFO["mt6595kkltedscta"] = {"id":"mt6595kkltedscta", "age":4030, "vtrunk":"cta", "repo":"platform_kk_95_ds", "project":"vanzo95_lwt_ds_kk", "android": "44", "images_emmc":(
        "MT6595_Android_scatter.txt",
        "preloader_vanzo95_lwt_ds_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

PROJECT_INFO["mt6582kklteds5m"] = {"id":"mt6582kklteds5m", "age":4100, "vtrunk":"vtrunk", "repo":"platform_kk_lt_82_92_ds5m", "project":"vanzo82_lwt_2s_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lwt_2s_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kklteds5m"] = {"id":"mt6592kklteds5m", "age":4110, "vtrunk":"vtrunk", "repo":"platform_kk_lt_82_92_ds5m", "project":"vanzo92_lwt_2s_kk", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_lwt_2s_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6582kklteds5mcta"] = {"id":"mt6582kklteds5mcta", "age":4120, "vtrunk":"cta", "repo":"platform_kk_lt_82_92_ds5m", "project":"vanzo82_lwt_2s_kk", "android": "44", "images_emmc":(
        "MT6582_Android_scatter.txt",
        "preloader_vanzo82_lwt_2s_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6592kklteds5mcta"] = {"id":"mt6592kklteds5mcta", "age":4130, "vtrunk":"cta", "repo":"platform_kk_lt_82_92_ds5m", "project":"vanzo92_lwt_2s_kk", "android": "44", "images_emmc":(
        "MT6592_Android_scatter.txt",
        "preloader_vanzo92_lwt_2s_kk.bin",
        "lk.bin",
        "logo.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
        "MBR",
        "EBR1",
        "EBR2",
)}

PROJECT_INFO["mt6732kklte"] = {"id":"mt6732kklte", "age":4200, "vtrunk":"vtrunk", "repo":"platform_kk_6732_6752", "project":"vanzo6752_lwt_kk", "android": "45", "images_emmc":(
        "MT6752_Android_scatter.txt",
        "preloader_vanzo6752_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "trustzone.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

PROJECT_INFO["mt6752kklte"] = {"id":"mt6752kklte", "age":4210, "vtrunk":"vtrunk", "repo":"platform_kk_6732_6752", "project":"vanzo6752_lwt_kk", "android": "45", "images_emmc":(
        "MT6752_Android_scatter.txt",
        "preloader_vanzo6752_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "trustzone.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

PROJECT_INFO["mt6732kkltecta"] = {"id":"mt6732kkltecta", "age":4230, "vtrunk":"cta", "repo":"platform_kk_6732_6752", "project":"vanzo6752_lwt_kk", "android": "45", "images_emmc":(
        "MT6752_Android_scatter.txt",
        "preloader_vanzo6752_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "trustzone.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

PROJECT_INFO["mt6752kkltecta"] = {"id":"mt6752kkltecta", "age":4240, "vtrunk":"cta", "repo":"platform_kk_6732_6752", "project":"vanzo6752_lwt_kk", "android": "45", "images_emmc":(
        "MT6752_Android_scatter.txt",
        "preloader_vanzo6752_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "trustzone.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

PROJECT_INFO["mt6732kklteali"] = {"id":"mt6732kklteali", "age":4250, "vtrunk":"vtrunk", "repo":"platform_kk_6732_6752_ali", "project":"vanzo6752_lwt_kk", "android": "45", "images_emmc":(
        "MT6752_Android_scatter.txt",
        "preloader_vanzo6752_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "trustzone.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

PROJECT_INFO["mt6752kklteali"] = {"id":"mt6752kklteali", "age":4260, "vtrunk":"vtrunk", "repo":"platform_kk_6732_6752_ali", "project":"vanzo6752_lwt_kk", "android": "45", "images_emmc":(
        "MT6752_Android_scatter.txt",
        "preloader_vanzo6752_lwt_kk.bin",
        "lk.bin",
        "logo.bin",
        "trustzone.bin",
        "boot.img",
        "recovery.img",
        "system.img",
        "userdata.img",
        "cache.img",
        "secro.img",
)}

def get_all_project_info():
    return PROJECT_INFO

def _token_in_project(project, token):
    return project.endswith('_' + token) or '_' + token + '_' in project

def _is_ali(project):
    return re.match('mt[^_]+ali_', project) is not None

def _is_mul(project):
    return project.endswith('_mul') or '_mul_' in project

def _is_cta(project):
    return _token_in_project(project, 'cta') or _token_in_project(project, 'cphone')

def _is_aphone(project):
    return _token_in_project(project, 'aphone')

def _is_ephone(project):
    return _token_in_project(project, 'ephone')

def _is_aephone(project):
    return _is_aphone(project) or _is_ephone(project)

def _is_vphone(project):
    return _token_in_project(project, 'vphone')

def _is_sphone(project):
    return _token_in_project(project, 'sphone')

def _is_tphone(project):
    return _token_in_project(project, 'tphone')

def _is_ophone(project):
    return _token_in_project(project, 'ophone')

def _does_use_wallpaper_database(project):
    return int(get_project_info(project)['android']) >= 40

def _wallpaper_database_path():
    return os.path.join(os.path.expanduser('~'), 'build_projects/wallpapers')

def get_project_info(project_name):
    project_info = None
    matches = [info for id_, info in PROJECT_INFO.items()
               if globals()['_is_' + id_](project_name)]
    if len(matches) == 1:
        project_info = matches[0]

    if project_info != None:
        if not project_info.has_key("storage"):
            if project_info.has_key("images_nand") and project_info.has_key("images_emmc"):
                project_info["storage"] = "unknown"
            elif project_info.has_key("images_nand"):
                project_info["storage"] = "nand"
            elif project_info.has_key("images_emmc"):
                project_info["storage"] = "emmc"

    return project_info

def get_project_ui(project_name):
    if project_name == None:
        return

    project_name = project_name.lower()
    if "aphone" in project_name:
        UI = "aphone"
    elif "ephone" in project_name:
        UI = "ephone"
    elif "tphone" in project_name:
        UI = "tphone"
    elif "ophone" in project_name:
        UI = "ophone"
    elif "vphone" in project_name:
        UI = "vphone"
    elif "sphone" in project_name or "sense" in project_name:
        UI = "sphone"
    elif "cta" in project_name or "cphone" in project_name:
        UI = "cphone"
    else:
        UI = "vtrunk"

    return UI
USERDATA_EXCLUDE_LIST = (
    "data/com.android.phone/minilog",
    "data/net.cactii.flash2",
    "data/cn.dpocket.moplusand.ui",
    "data/com.mediatek.dataservice",
    "data/com.dayingjia.stock.activity",
    "data/com.magzter.indiatoday.cosmopolitan.momagic",
    "data/com.magzter.indiatoday.momagic",
    "data/com.diguayouxi",
    "data/com.easou.android",
    "data/com.ganji.android",
    "data/com.neomtel.mxhome",
    "data/com.qzone",
    "data/mcube",
    "data/com.tencent.mtt",
    "data/com.tencent.pengyou",
    "data/com.tencent.qqphonebook",
    "data/com.tencent.qqpimsecure",
    "data/com.uucun848.android.cms",
    "data/com.mas.wawagame.Kuwalord",
    "data/com.android.caivs.app",
    "data/com.xiaoao.lobby",
    "data/com.zzz.ringdroid",
    "data/com.android.vending",
    "data/com.android.launcher/a3m*",
    "data/com.mediatek.factorymode.FatFormatFlag",
    "data/com.lenovo.safecenter",
    "data/whitelist",
    "data/com.weimei.shuibowen",
    "system/lockscreencom.mediatek.DataUsageLockScreenClient",
    "mdl",
    "nvram",
    "user",
)

def remove_sth_from_userdata(dir1, limitsize=False):
    if limitsize:
        limit1 = 150
        out1 = int(filter(str.isdigit, commands.getstatusoutput("du -sh %s" % dir1)[1]))
        if out1 > limit1:
            my_sys("rm -rf %s/vspace" % dir1)
            out1 = int(filter(str.isdigit, commands.getstatusoutput("du -sh %s" % dir1)[1]))
            if out1 > limit1:
                my_sys("rm -rf %s/dalvik-cache" % dir1)

    for one in USERDATA_EXCLUDE_LIST:
        my_sys("rm -rf %s/%s" % (dir1, one))
################################################################################
########@@ Methods for server site build
################################################################################
VANZO_TEAM_CUSTOM = (
u"陈怡彬",
u"伍宏海",
u"姚凯凯",
u"王帅",
u"王尊秋",
u"彭桦",
u"李斌",
u"张晓虎",
u"崔小俊",
u"龚梦飞",
u"莫晓明",
u"黄风棋",
u"蒋燕清",
u"王吉成",
u"定制验证",
u"定制工具",
u"定制手工",
u"软件定制",
u"软件配置组",
)

VANZO_TEAM_T2 = (
u"王飞",
u"林茂彬",
u"栾世俊",
u"陈伟军",
u"朱寒冬",
u"滕琦",
u"软件精品",
u"软件精品组",
)

VANZO_TEAM_APP = (
u"余成",
u"叶剑波",
u"韩盛鹏",
u"汤磊",
u"方放杰",
u"张敬枝",
u"殷俊",
u"李冰",
u"张凯华",
u"钟俊瑜",
u"黄炎辉",
u"李琦权",
u"张泽辉",
u"于健鹏",
u"吴杜",
u"方志洲",
u"张塑",
u"冯海涛",
u"匡傲松",
u"岳彩礼",
u"邱凯",
u"陈斌",
u"移动入库",
u"阿里技术支持",
u"MTK技术支持",
u"软件应用",
u"软件应用组",
)

VANZO_TEAM_UI= (
u"徐磊",
u"黄富坤",
u"白垠",
u"邹默涵",
u"尚晓鹏",
u"王建华",
u"魏宇",
u"葛小丽",
u"陈敬诚",
u"郑聪",
u"张书礼",
u"马小军",
u"软件UI",
u"软件UI组",
)

VANZO_TEAM_DRIVER = (
u"杨志红",
u"张欣瑀",
u"吴捷",
u"李成成",
u"徐俊",
u"杨光",
u"阳洋",
u"薛传政",
u"宋立新",
u"软件驱动",
u"软件驱动组",
)

VANZO_TEAM_SWTEST = (
u"颜骁骏",
u"李惠",
u"张萌",
u"李春林",
u"王东",
u"鲍正南",
u"吴建方",
u"周露颖",
u"姜洋燕",
u"张晓西",
u"林鑫",
u"程秀建",
u"袁庆",
u"谢辉",
u"高小翠",
u"罗烨",
u"刘娟",
u"黄娟",
u"颜林艳",
u"王甫娟",
u"赵鹏",
u"朱琳",
u"单耀华",
u"吴丽",
u"徐冬玲",
u"孟娜",
u"伏坤然",
u"软件测试",
u"软件测试部",
)

VANZO_TEAM_PM = (
u"王绍维",
u"李德凯",
u"李俊杰",
u"高义兵",
u"陈创",
u"李勇",
u"卢丹",
u"狄宝林",
u"张小亚",
u"吴翠红",
u"陈燕平",
u"朱健申",
u"朱明",
u"曾芳",
u"赵川",
u"吕辉",
u"岑年",
u"陆晨",
u"付清容",
u"穆晶晶",
u"徐娇春",
u"FAE调优",
u"项目管理部",
)

VANZO_TEAM_MAN = (
u"刘俊明",
u"周少斌",
u"石磊",
u"管理组",
u"软件QA",
)

VANZO_TEAM_FIN = (
u"向文达",
u"钱梅华",
u"朱永龙",
u"敖玉艳",
u"左伟香",
u"曹萍",
u"李利民",
u"易钊",
u"财务部",
)

VANZO_TEAM_STR = (
u"肖义洪",
u"郭易军",
u"武乐强",
u"王昕",
u"陈君林",
u"产品结构",
u"硬件结构部",
)

VANZO_TEAM_ADM = (
u"胡佳妮",
u"宋伟琴",
u"张亚荣",
u"李志国",
u"杨星",
u"行政部",
)

VANZO_TEAM_LAYOUT = (
u"王芳",
u"沈伟民",
u"陈莹莹",
u"胡花",
u"沈林",
u"硬件Layout组",
)

VANZO_TEAM_BASE = (
u"赵利峰",
u"音频调优",
u"罗鹏",
u"张晨",
u"黄以来",
u"王一彪",
u"李浩",
u"陈法",
u"罗建龙",
u"武光维",
u"吕洋",
u"王肖",
u"鄢明智",
u"王志超",
u"王礼",
u"硬件开发",
u"硬件基带组",
)

VANZO_TEAM_SYSTEM = (
u"张庆占",
u"武志勇",
u"丁格",
u"藏公瑾",
u"系统组",
u"硬件系统组",
)

VANZO_TEAM_HWTEST = (
u"魏振敏",
u"董镕春",
u"高瑶凯",
u"张作远",
u"汪桂云",
u"周传俊",
u"常亚珍",
u"张文通",
u"卜建国",
u"李强",
u"梁学明",
u"硬件测试",
u"刘奋飞",
u"郑云敏",
u"郑延",
u"胡双",
u"赵敏洁",
u"硬件测试组"
)

VANZO_TEAM_RF = (
u"赵淮北",
u"李军",
u"曾神",
u"周进",
u"李庆会",
u"查甫俊",
u"刘照黎",
u"硬件射频组",
)

VANZO_TEAM_RUN = (
u"张伟",
u"宋燕",
u"管嫣",
u"李倩",
u"冯春",
u"张海丽",
u"曹清莲",
u"缪春燕",
u"杨晓玲",
u"莫佳丽",
u"马静",
u"徐春花",
u"孙娇娇",
u"王柳",
u"林丽慧",
u"运营部",
)

VANZO_TEAM_ALL = (
VANZO_TEAM_SWTEST,
VANZO_TEAM_CUSTOM,
VANZO_TEAM_T2,
VANZO_TEAM_APP,
VANZO_TEAM_UI,
VANZO_TEAM_DRIVER,
VANZO_TEAM_PM,
VANZO_TEAM_MAN,
VANZO_TEAM_FIN,
VANZO_TEAM_STR,
VANZO_TEAM_ADM,
VANZO_TEAM_LAYOUT,
VANZO_TEAM_BASE,
VANZO_TEAM_SYSTEM,
VANZO_TEAM_HWTEST,
VANZO_TEAM_RF,
VANZO_TEAM_RUN,
)

VANZO_TEAM_TRANS = {
    "chenyibin":u"陈怡彬",
    "luanshijun":u"栾世俊",
    "wuhonghai":u"伍宏海",
    "yaokaikai":u"姚凯凯",
    "wangshuai":u"王帅",
    "wangzunqiu":u"王尊秋",
    "gongmengfei":u"龚梦飞",
    "libin":u"李斌",
    "jiangyanqing":u"蒋燕清",
    "yangxiaolong":u"杨晓龙",
    "zhangxiaohu":u"张晓虎",
    "cuixiaojun":u"崔小俊",
    "moxiaoming":u"莫晓明",
    "huangfengqi":u"黄风棋",
    "zhuhandong":u"朱寒冬",
    "penghua":u"彭桦",

    "wangfei":u"王飞",
    "chenweijun":u"陈伟军",
    "tengqi":u"滕琦",
    "helianyi":u"何廉毅",
    "linmaobin":u"林茂彬",

    "yucheng":u"余成",
    "yuecaili":u"岳彩礼",
    "yejianbo":u"叶剑波",
    "hanshengpeng":u"韩盛鹏",
    "tanglei":u"汤磊",
    "fangfangjie":u"方放杰",
    "zhangjingzhi":u"张敬枝",
    "yinjun":u"殷俊",
    "libing":u"李冰",
    "zhangkaihua":u"张凯华",
    "zhongjunyu":u"钟俊瑜",
    "huangyanhui":u"黄炎辉",
    "liqiquan":u"李琦权",
    "zhangzehui":u"张泽辉",
    "yujianpeng":u"于健鹏",
    "wudu":u"吴杜",
    "fangzhizhou":u"方志洲",
    "zhangsu":u"张塑",
    "fenghaitao":u"冯海涛",
    "kuangaosong":u"匡傲松",
    "qiukai":u"邱凯",
    "chenbin":u"陈斌",

    "xulei":u"徐磊",
    "huangfukun":u"黄富坤",
    "weiyu":u"魏宇",
    "baiyin":u"白垠",
    "hexiuhui":u"何修辉",
    "shangxiaopeng":u"尚晓鹏",
    "zoumohan":u"邹默涵",
    "chenjingcheng":u"陈敬诚",
    "zhengchong":u"郑聪",

    "yangzhihong":u"杨志红",
    "zhangxinyu":u"张欣瑀",
    "maxiaojun":u"马小军",
    "wujie":u"吴捷",
    "lichengcheng":u"李成成",
    "xujun":u"徐俊",
    "yangguang":u"杨光",
    "yangyang":u"阳洋",
    "xuechuanzheng":u"薛传政",
    "songlixin":u"宋立新",
}

#we use 2T hard disk for dailybuild
DAILYBUILD_SERVER_LIST  =  ("59", "60", "63", "64",       "66",             "69", "70", "71", "73", "74", "75", "77", "78",)
ONDEMAND_SERVER_LIST    =  ("59", "60", "63", "64", "65", "66", "67", "69", "70", "71", "73", "74", "75", "77", "78",)
ONDEMAND_SERVER_LIST_1204   =  ("68","72","76","79","80","81","82",)

#E5620@2.4G, 16core:59,60,65,66,67,70
#E5645@2.4G, 24core:63,64,69,
#E5650@2.67G,24core,71,73,74,75,76,77,78,79
#1T HD:65,67
_ONDEMAND_SERVER_CLASSIFIED_LIST = (
    ("59", "60", "65", "66", "67", "70"),
    ("63", "64", "69", ),
    ("71", "73", "74", "75", "77", "78",),
)

OTHER_SERVER_LIST = ("61", "62", "57", "31", "34", "41")

def get_all_server_list():
    list1 = list(ONDEMAND_SERVER_LIST)
    list1.extend(ONDEMAND_SERVER_LIST_1204)
    list1.extend(OTHER_SERVER_LIST)
    return list1

def get_build_server_list():
    list1 = list(ONDEMAND_SERVER_LIST)
    list1.extend(ONDEMAND_SERVER_LIST_1204)
    return list1

def _line2map(line):
    """
    Turn one line of buildlist into map
    With the 1st item be project's name
    If mode not specified, default to eng
    """
    map1 = {}
    list1 = line.split(":")
    map1["project"] = list1[0].strip()
    for one in list1[1:]:
        if "=" in one:
            list2 = one.split("=")
            map1[list2[0].strip()] = list2[1].strip()
        else:
            map1[one.strip()] = one.strip()
    if not map1.has_key("mode"):
        map1["mode"] = "eng"
    return map1

def _my_cmp(map1, map2):
    """
    special comparator
    """
    if map1["project"] == map2["project"]:
        return cmp(map1["mode"], map2["mode"])
    else:
        return cmp(map1["project"], map2["project"])

def _my_cmp2(project1, project2):
    """
    special comparator
    """
    project1a = project1.replace("_user", "").replace("_eng","")
    project2a = project2.replace("_user", "").replace("_eng","")
    if project1a == project2a:
        return cmp(project1, project2)
    else:
        return cmp(project1a, project2a)

def _my_cmp3(build1, build2):
    """
    special comparator
    """
    return -cmp(build1[0][-6:], build2[0][-6:])

def gen_simple_project_mode_list(list1):
    """
    remove other keys
    and gen build list with mode included
    such as:
        f680_user
    """
    list2 = []
    for map1 in list1:
        list2.append(map1["project"] + "_" + map1["mode"])
    return list2

def gen_simple_project_list(list1):
    """
    remove other keys
    and gen build list with only project name
    such as:
        f680
    """
    list2 = []
    for map1 in list1:
        list2.append(map1["project"])
    list1 = list(set(list2))
    list1.sort()
    return list1

def gen_build_list(filename):
    """
    Generate build list, each one stored in map
    """
    list1 = []
    with open(filename) as myfile:
        for line in myfile:
            if not "#" in line and len(line.strip()) != 0:
                list1.append(_line2map(line.lower()))

    return list1

def is_this_d_server(ip_addr=None):
    if ip_addr == None:
        ip_addr = get_ip()
    if ip_addr in DAILYBUILD_SERVER_LIST:
        return True
    else:
        return False

def is_this_o_server(ip_addr=None):
    #Wether this PC is server
    if ip_addr == None:
        ip_addr = get_ip()
    t2346 = ONDEMAND_SERVER_LIST + ONDEMAND_SERVER_LIST_1204
    if ip_addr in t2346:
        return True
    else:
        return False

def outputtoxls(filename, sheet_names, map1):
    """
    common file to output excel file
    """
    if os.path.exists(filename):
        os.remove(filename)
    excel = Workbook()
    outputtoxls2(excel, sheet_names, map1)
    excel.save(filename)

def outputtoxls2(excel, sheet_names, map1):
    borders = Borders()
    borders.left = borders.right = borders.top = borders.bottom = Borders.THIN
    style = XFStyle()
    font = Font()
    font.name = 'Verdana'
    font.bold = True
    font.colour_index = 6 #1:white,2:red,3:green,4:blue,5:yellow,6:pink
    style.font = font
    style.borders = borders

    style2 = XFStyle()
    font2 = Font()
    font2.name = 'Verdana'
    font2.bold = True
    #font2.underline = Font.UNDERLINE_SINGLE
    font2.colour_index = 4
    style2.font = font2
    style2.borders = borders
    for one in sheet_names:
        sheet1 = excel.add_sheet(one)
        map2 = map1[one]
        for (i, one) in enumerate(map2["column_names"]):
            sheet1.write(0, i, one, style)
            sheet1.col(i).width = map2["column_widths"][i]
        for (i, one) in enumerate(map2["contents"]):
            for (j , two) in enumerate(one):
                sheet1.write(1+i, j, two, style2)

#Globals for generate images location
EXCELFILE = "images_location.xls"
_ALL_DAYS = 30
_ALL_DAYS2 = 7
_BATCH_FILE_ALL2 = "scripts/dailybuild_all_projects.txt"
_g_databases = {}
_g_commits = {}
_g_dates = {}
def _outputtoxls(databases):
    if os.path.exists(EXCELFILE):
        os.remove(EXCELFILE)

    excel = Workbook()
    sheet1 = excel.add_sheet("images_location")

    borders = Borders()
    borders.left = borders.right = borders.top = borders.bottom = Borders.THIN

    style = XFStyle()
    font = Font()
    font.name = 'Verdana'
    font.bold = True
    font.colour_index = 6 #1:white,2:red,3:green,4:blue,5:yellow,6:pink
    style.font = font
    style.borders = borders

    style2 = XFStyle()
    font2 = Font()
    font2.name = 'Verdana'
    font2.bold = True
    font2.underline = Font.UNDERLINE_SINGLE
    font2.colour_index = 4
    style2.font = font2
    style2.borders = borders

    style3 = XFStyle()
    font3 = Font()
    font3.name = 'Verdana'
    font3.bold = True
    font3.underline = Font.UNDERLINE_SINGLE
    font3.colour_index = 5
    style3.font = font3
    style3.borders = borders

    sheet1.col(0).width = 15000
    for i in range(_ALL_DAYS):
        dt2 = datetime.datetime.now() - datetime.timedelta(i)
        if dt2.isoweekday() == 7:
            sheet1.write(0, 1+i, _g_dates[i][4:], style2)
        else:
            sheet1.write(0, 1+i, _g_dates[i][4:], style)
        sheet1.col(1+i).width = 1500
    list_projects = []
    def _get_project_name886(one):
        pos1 = one.replace("_eng_", "___").replace("_user_", "___").find("___")
        return one[:pos1]

    for one in databases:
        for two in databases[one]:
            three = _get_project_name886(two[0])
            if not three in list_projects:
                list_projects.append(three)
    list_projects.sort()
    n = "HYPERLINK"
    for (i, one) in enumerate(list_projects):
        if "user" in one:
            sheet1.write(1 + i, 0, one, style2)
        else:
            sheet1.write(1 + i, 0, one, style)

    for i in _g_dates:
        if not databases.has_key(_g_dates[i]):
            continue
        one_day_projects = databases[_g_dates[i]]
        for one in one_day_projects:
            three = _get_project_name886(one[0])
            col1 = i + 1
            row1 = list_projects.index(three) + 1
            pos1 = one[1].find("192.168.1.") + 10
            server1 = one[1][pos1: pos1+2]
            out1 = samba_run_d("ls %s/%s/misc/*target_files*.zip" % (_g_dates[i], one[0]), server1, True)
            if not "NT_STATUS_NO_SUCH_FILE" in out1 and not "NT_STATUS_OBJECT_PATH_NOT_FOUND" in out1:
                out2 = samba_run_d("ls %s/%s/misc/sdk" %(_g_dates[i], one[0]), server1, True)
                try:
                    if not "NT_STATUS_NO_SUCH_FILE" in out2 and not "NT_STATUS_OBJECT_PATH_NOT_FOUND" in out2:
                        sheet1.write(row1, col1, Formula(n + """("%s";"%s")"""%(one[1], server1)), style)
                    else:
                        sheet1.write(row1, col1, Formula(n + """("%s";"%s")"""%(one[1], server1)), style2)
                except Exception, e: # pylint: disable=W0703
                    print e
                    print _g_dates[i]
                    print one
    excel.save(EXCELFILE)

def gen_images_location():
    """
    Generate excel file for ondemand build image locations
    """
    dt1 = datetime.datetime.now()
    for i in range(_ALL_DAYS):
        _g_dates[i] = (dt1 - datetime.timedelta(i)).strftime('%Y%m%d')
        for server in DAILYBUILD_SERVER_LIST:
            out1 = samba_run_d("""cd %s;ls""" %(_g_dates[i]), server, True)
            if "NT_STATUS_OBJECT_NAME_NOT_FOUND" in out1:
                continue
            for out2 in out1.split():
                if _g_dates[i] in out2:
                    out3 = samba_run_d("""cd %s/%s;ls system.img""" %(_g_dates[i], out2), server, True)
                    if not "NT_STATUS_NO_SUCH_FILE" in out3:
                        if not _g_databases.has_key(_g_dates[i]):
                            _g_databases[_g_dates[i]] = []
                        out2a = """\\\\192.168.1.%s\\dailybuild\\%s\\%s""" % (server, _g_dates[i], out2)
                        _g_databases[_g_dates[i]].append([out2, out2a])
    _outputtoxls(_g_databases)

EXCELFILE2 = "images_location2.xls"
def _outputtoxls2(databases):
    """
    gen image locations which is located in ondemand build servers
    """
    if os.path.exists(EXCELFILE2):
        os.remove(EXCELFILE2)
    excel = Workbook()

    borders = Borders()
    borders.left = borders.right = borders.top = borders.bottom = Borders.THIN

    style = XFStyle()
    font = Font()
    font.name = 'Verdana'
    font.bold = True
    font.colour_index = 6 #1:white,2:red,3:green,4:blue,5:yellow,6:pink
    style.font = font
    style.borders = borders

    style2 = XFStyle()
    font2 = Font()
    font2.name = 'Verdana'
    font2.bold = True
    font2.underline = Font.UNDERLINE_SINGLE
    font2.colour_index = 4
    style2.font = font2
    style2.borders = borders

    n = "HYPERLINK"
    j = 1
    sheet1 = excel.add_sheet("all_%d" % _ALL_DAYS2)
    sheet1.col(0).width = 3000
    sheet1.col(1).width = 3000
    sheet1.col(2).width = 5000
    sheet1.col(3).width = 5000
    sheet1.col(4).width = 20000
    sheet1.write(0, 0, "Date", style2)
    sheet1.write(0, 1, "Time", style2)
    sheet1.write(0, 2, "Committer", style2)
    sheet1.write(0, 3, "Server", style2)
    sheet1.write(0, 4, "Version", style2)
    for i in range(_ALL_DAYS2):
        if databases.has_key(_g_dates[i]):
            onedaybuild = databases[_g_dates[i]]
            onedaybuild.sort(_my_cmp3)
            for onebuild in onedaybuild:
                time1 = onebuild[0][-6:-4] + ":" + onebuild[0][-4:-2] + ":" + onebuild[0][-2:]
                sheet1.write(j, 0, _g_dates[i], style)
                sheet1.write(j, 1, time1, style)
                version1 = onebuild[0][:-15]
                pos1 = version1.rfind("_")
                sheet1.write(j, 2, version1[pos1+1:], style)
                sheet1.write(j, 3, "v" + onebuild[1][12:14], style)
                sheet1.write(j, 4, Formula(n + """("%s";"%s")"""%(onebuild[1], version1[:pos1])), style2)
                j += 1

    excel.save(EXCELFILE2)

def gen_images_location2():
    """
    Generate excel file for ondemand build image locations
    """
    dt1 = datetime.datetime.now()
    for i in range(_ALL_DAYS2):
        _g_dates[i] = (dt1 - datetime.timedelta(i)).strftime('%Y%m%d')
        for server in ONDEMAND_SERVER_LIST:
            out1 = samba_run_d2("""cd %s;ls""" %(_g_dates[i]), server, True)
            if "NT_STATUS_OBJECT_NAME_NOT_FOUND" in out1:
                continue
            for out2 in out1.split():
                if _g_dates[i] in out2:
                    out3 = samba_run_d2("""cd %s/%s;ls system.img""" %(_g_dates[i], out2), server, True)
                    if not "NT_STATUS_NO_SUCH_FILE" in out3:
                        if not _g_databases.has_key(_g_dates[i]):
                            _g_databases[_g_dates[i]] = []
                        out2a = """\\\\192.168.1.%s\\dailybuild2\\%s\\%s""" % (server, _g_dates[i], out2)
                        _g_databases[_g_dates[i]].append([out2, out2a])
    _outputtoxls2(_g_databases)

################################################################################
########@@ For Client Side Build
################################################################################

_TAG_EXCLUDE_LIST = (
    "ORIGINAL_V4",
    "ORIGINAL_V6",
    "ORIGINAL_V7",
    "ORIGINAL_V8",
    "APHONE_V6",
    "SPHONE_V2",
    "SPHONE_V6",
)

def onedemand_build_c_gen_project_list(key1=None):
    """
    Generate project list
    """
    file1 = os.path.expanduser("~/build_projects/scripts/dailybuild_all_projects.txt")
    list1 = []
    with open(file1) as myfile:
        for line in myfile:
            if not "#" in line and len(line.strip()) != 0:
                list2 = line.strip().split(":")
                list1.append(list2[0].strip())
    list1 = list(set(list1))
    list1.sort()

    if key1 != None:
        list2 = []
        for one in list1:
            if key1 in one:
                list2.append(one)
        return list2
    return list1

def onedemand_build_c_check_server(server):
    """
    For ondemand build, check whether server is free or busy of dead
    """
    ret = -1
    ret2 = ""
    who = ""
    when = ""
    project = ""
    out = samba_run_d2("ls", server, True)
    if "hb.txt" in out:
        samba_run_d2("get hb.txt hb.txt", server)
        try:
            line, = open("hb.txt")
            if len(line) >= 6:
                str1 = datetime.datetime.now().strftime("%H%M%S")
                ret2 = line.strip()
                diff1 = (int(str1[0:2]) - int(line[0:2])) * 3600
                diff1 += (int(str1[2:4]) - int(line[2:4])) * 60
                diff1 += (int(str1[4:6]) - int(line[4:6]))
                if diff1 < 0:
                    diff1 = -diff1
                out2 = samba_run_o("ls", server, True)
                if "ondemand_build_doing " in out2:
                    ret = 1
                    ret2 = "building"
                    samba_run_o("get logs.txt logs.txt", server)
                    one = ""
                    with open("logs.txt") as inF:
                        for line in inF:
                            one = line
                    pos1 = one.find("-C")
                    who = one[pos1:].split()[1].replace("Tool_", "")
                    pos1 = one.find("201")
                    when = one[pos1+11:pos1+11+8]
                    pos1 = one.find(" -P ")
                    project = one[pos1 + 4:].split()[0]
                    os.remove("logs.txt")
                elif diff1 < 120:
                    ret = 1
                    if "ondemand_build " in out2:
                        ret = 1
                        ret2 = "ordered"
                    else:
                        ret = 0
        except ValueError:
            ret = 1
            ret2 = "unknown"
        os.remove("hb.txt")
    return (ret, ret2, who, when, project)


def onedemand_build_c_get_free_servers():
    """
    For ondemand build, return list of free servers
    """
    free_servers = []
    t2644 = ONDEMAND_SERVER_LIST + ONDEMAND_SERVER_LIST_1204
    for server in t2644:
        ret = onedemand_build_c_check_server(server)
        if ret[0] == 0:
            print _green('{0:<5}{1:<10}'.format(server, "free"))
            free_servers.append(server)
        elif ret[0] == -1:
            print _red('{0:<5}{1:<10}{2:<15}'.format(server, "dead", ret[1]))
        elif ret[0] == 1:
            print _yellow('{0:<5}{1:<10}{2:<15}{3:<10}{4}'.format(server,ret[1],ret[2],ret[3],ret[4]))
            #print _yellow(server + ":" + ret[1] + ":" + ret[2] + ":" + ret[3])
    return free_servers

def ge_kk(project_name):
    return get_project_info(project_name)["age"] >=  PROJECT_INFO["mt6582kk"]["age"]

def onedemand_build_c_get_free_server(urgent=False, project_name=None):
    free_servers = []

    list2662 = list(_ONDEMAND_SERVER_CLASSIFIED_LIST)

    if project_name:
        if ge_kk(project_name):
            list2662[-1] = list2662[-1] + ONDEMAND_SERVER_LIST_1204

    l1 = len(list2662) -1
    for i in range(l1, -1, -1):
        list1 = list2662[i]
        for server in list1:
            if onedemand_build_c_check_server(server)[0] == 0:
                free_servers.append(server)
        if len(free_servers) > 1:
            break

    len1 = len(free_servers)
    if urgent:
        len1 += 1
    if len1 >= 2:
        len2 = len(free_servers)
        if len2 == 1:
            return free_servers[0]
        else:
            return free_servers[int(datetime.datetime.now().strftime("%S")) % len2]
    else:
        return None

def onedemand_build_c_trigger_build(ds1, server, cmd1):
    """
    Trigger ondemand build accroding to parameters stored in ds1
    """
    #1st: generate ondemand
    with open("ondemand_build","w") as outfile1:
        temp = sys.stdout
        sys.stdout = outfile1
        print "version:vanzo20120717"
        for one in ("committer", "project", "mode"):
            print "%s:%s" % (one, ds1[one])

        if ds1.has_key("verifychange"):
            print "%s:%s" % ("verifychange", ds1["verifychange"])

        if ds1.has_key("verifyproject"):
            print "%s:%s" % ("verifyproject", ds1["verifyproject"])

        if len(ds1["snapshotfile"]) > 0:
            print "snapshotfile:" + ds1["snapshotfile"].split("/")[-1]
        if len(ds1["extraoverlayfrom"]) > 0:
            print "extraoverlayfrom:" + ds1["extraoverlayfrom"].split("/")[-1]
        if len(ds1["removeset"]) > 0:
            for one in ds1["removeset"]:
                print "remove:" + one
        for one in ("patchset", "gitamset"):
            if len(ds1[one]) > 0:
                for two in ds1[one]:
                    three = two.split(":")
                    print one.replace("set","") + ":" + three[0] + ":" + three[1].split("/")[-1]
        if len(ds1["freezeto"]) > 0:
            print "freezeto:" + ds1["freezeto"]
        if ds1["buildsdk"]:
            print "sdk"
        if ds1["quick"]:
            print "quick"
        if ds1["onlybootimage"]:
            print "onlybootimage"
        sys.stdout = temp

    #2nd:updateload files
    if ds1.has_key("snapshotfile"):
        value1 = ds1["snapshotfile"]
        value2 = value1.split("/")[-1]
        samba_run_o("""put %s %s""" % (value1, value2), server)

    if ds1.has_key("extraoverlayfrom"):
        value1 = ds1["extraoverlayfrom"]
        if value1 != "":
            value2 = value1.split("/")[-1]
            samba_run_o("""put %s %s""" % (value1, value2), server)

    for one in ("patchset", "gitamset"):
        if ds1.has_key(one):
            for one in ds1[one]:
                two = one.split(":")
                value2 = two[1].split("/")[-1]
                samba_run_o("""put %s %s""" % (two[1], value2), server)

    #3rd:write logs
    with open("logs.txt","a+") as outfile1:
        print >> outfile1, datetime.datetime.now().strftime("%D:%H-%M-%S")
        print >> outfile1, "committer:" + ds1["committer"]
        print >> outfile1, "server:" + server
        print >> outfile1, "cmd:" + cmd1
        print >> outfile1, "\n"

    #4th:trigger
    samba_run_o("rm ondemand_build*", server)
    samba_run_o("put ondemand_build ondemand_build", server)
    os.remove("ondemand_build")


RES_SERVER = '192.168.1.52:86'


def ondemand_server_status():
    '''Return a list of all ondeman server status.

    Results are cached, maynot be the lastest.

    Each item is a dict has keys:
    --- ip: Server ip address
    --- updated: When the server status updated
    --- project: The project current processing
    --- who: The committer
    --- when: When this project started building
    --- mode: user/debug etc.
    --- state: building/ordered/free/dead
    --- supported: The invertal of supported android versions on this server
    '''

    try:
        return json.loads(urlopen(
            'http://{0}/servers/status/'.format(RES_SERVER)
        ).read())
    except:
        return []


def ondemand_build(params):
    '''Try to build a project on an ondemand server.

    On success, it returns the server ip e.g. '59', otherwise, it returns None
    on no free server and throws an Exception when error occurs.

    Without chdir, this function should be thread-safe.'''

    class _Error(Exception):
        def __init__(self, msg):
            super(_Error, self).__init__()
            self.msg = msg

        def __str__(self):
            return self.msg

    @contextlib.contextmanager
    def _temp_dir():
        tmp = tempfile.mkdtemp()
        try:
            yield tmp
        finally:
            shutil.rmtree(tmp)

    def _lock_server(project_name):
        '''Return the first free server support this project and lock the server'''

        ret = json.loads(urlopen(
            'http://{0}/servers/lock/{1}/'.format(RES_SERVER, project_name)
        ).read())
        if 'error' in ret:
            raise _Error(ret['error'])
        return ret

    def _populate_ondemand_build():
        inter = ['version:vanzo20120717']
        for k in ('committer', 'project', 'mode'):
            inter.append('{0}:{1}'.format(k, params[k]))
        for k in ('verifyproject', 'verifychange', 'freezeto'):
            if k in params:
                inter.append('{0}:{1}'.format(k, params[k]))
        for k in ('snapshotfile', 'extraoverlayfrom'):
            if k in params:
                inter.append('{0}:{1}'.format(k, os.path.basename(params[k])))
        if 'removeset' in params:
            for v in params.get('removeset', []):
                inter.append('remove:{1}'.format(v))
        for k in ('patchset', 'gitamset'):
            for v in params.get(k, []):
                dir_, file_ = v.split(':')
                inter.append('{0}:{1}:{2}'.format(
                        k.replace('set', ''), dir_, os.path.basename(file_)
                ))
        for k in ('buildsdk', 'quick', 'onlybootimage'):
            if k in params:
                inter.append(k)

        with open(ondemand_build_filename, 'w') as out:
            out.write('\n'.join(inter) + '\n')

    def _upload_extra_files():
        for k in ('snapshotfile', 'extraoverlayfrom'):
            if k in params:
                samba_run_o('''put {0} {1}'''.format(params[k], os.path.basename(params[k])), server)
        for k in ('patchset', 'gitamset'):
            if k in params:
                for v in params.get(k, []):
                    file_ = v.split(':')[1]
                    samba_run_o('''put {0} {1}'''.format(file_, os.path.basename(file_)), server)

    def _upload_ondemand_build():
        try:
            samba_run_o('rm ondemand_build*', server)
        except:
            pass
        samba_run_o('put {0} ondemand_build'.format(ondemand_build_filename), server)

    with _temp_dir() as root:
        ondemand_build_filename = os.path.join(root, 'ondemand_build')
        _populate_ondemand_build()
        ret = _lock_server(params['project'])
        if not ret['ip']:
            return None
        try:
            server = ret['ip']
            _upload_extra_files()
            _upload_ondemand_build()
        finally:
            samba_run_o('''rm {0}'''.format(ret['tag']), server)
    return server

################################################################################
########@@ For Image Custom
################################################################################

def _image_custom_pre_gen_system_file_and_dir_list(file1):
    file1 = os.path.abspath(file1)
    cachedir = os.path.dirname(file1) + "/cache"
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)

    if not (os.path.exists(cachedir+ "/fl.txt")):
        tmpdir = tempfile.mkdtemp()
        cmd1 = "cd %s; unzip %s > /dev/null" % (tmpdir, file1)
        my_sys(cmd1)

        cmd1 = "cd %s; find . -type f > %s/fl.txt" % (tmpdir, cachedir)
        my_sys(cmd1)
        cmd1 = "cd %s; find . -type d > %s/dl.txt" % (tmpdir, cachedir)
        my_sys(cmd1)
        shutil.rmtree(tmpdir, True)

def image_custom_gen_system_file_and_dir_list(file1, list1=None, isDir=False):
    """
    list1: filter
    isDir: to gen file or dir list
    """
    _image_custom_pre_gen_system_file_and_dir_list(file1)
    if isDir:
        listfile  =  "dl.txt"
    else:
        listfile  =  "fl.txt"
    with open(os.path.dirname(file1)+ "/cache/" + listfile) as myfile:
        if not list1:
            list1 = []
        list2 = [one.strip()[2:] for one in myfile if one.strip()[2:] in list1]
    return list2

def image_custom_update_model_info_in_build_prop(file1, model, display):
    file2 = file1 + ".tmp"
    with open(file1, "r") as in_file:
        with open(file2, "w") as out_file:
            for line in in_file:
                if "ro.product.model" in line:
                    line2 = "ro.product.model=" + model + "\n"
                elif "ro.build.display.id" in line and len(display) > 0:
                    time1 = line.strip()[-16:]
                    line2 ="ro.build.display.id=" + display + time1 + "\n"
                else:
                    line2 = line
                out_file.write(line2)
    os.rename(file2, file1)

def image_custom_update_default_lang_in_build_prop(file1, lan, region):
    file2 = file1 + ".tmp"
    with open(file1, "r") as in_file:
        with open(file2, "w") as out_file:
            for line in in_file:
                if "ro.product.locale.language" in line:
                    line2 = "ro.product.locale.language=" + lan + "\n"
                elif "ro.product.locale.region" in line:
                    line2 ="ro.product.locale.region=" + region + "\n"
                else:
                    line2 = line
                out_file.write(line2)
    os.rename(file2, file1)

def image_custom_update_props_in_build_prop(file1, value1):
    map1 = {}
    list1 = my_split(value1)
    for one in list1:
        list2 = one.split("=")
        map1[list2[0]] = one

    file2 = file1 + ".tmp"
    with open(file1, "r") as in_file:
        with open(file2, "w") as out_file:
            for line in in_file:
                hit = False
                if "=" in line and not "#" in line:
                    for one in map1.keys():
                        if one in line:
                            hit = True
                            line2 = map1[one] + "\n"
                            map1[one] = ""
                            break
                if not hit:
                    line2 = line
                out_file.write(line2)
            for one in map1:
                if len(map1[one]) > 0:
                    out_file.write(map1[one] + "\n")
    os.rename(file2, file1)

def _project_custom_ensure_overlay_and_patchset_repos(project_name): # pylint: disable=W0603
    def _ensure_apks_repo_2066(project_info):
        str1 = "apks"
        if project_info["age"] >=  PROJECT_INFO["mt6592jb9"]["age"]:
            str1 = "apks92"

        if not os.path.exists("../../%s" % str1):
            my_sys("cd ../..;git clone vanzo:tools/%s.git" % str1)
        else:
            my_sys("cd ../../%s;git clean -fd;git checkout . > /dev/null; git pull > /dev/null" % str1)

        if os.path.exists(".repo"):
            my_sys("ln -sf ../../%s apks" % str1)
        elif os.path.exists("../../../vanzo_team"):
            my_sys("mkdir -p ro; cd ro && rm -f apks && ln -sf ../../../%s apks" % str1)
            my_sys("mkdir -p rw; cd rw && rm -f apks && ln -sf ../../../%s apks" % str1)
            my_sys("rm -f apks;ln -sf ../../%s apks" % str1)
            my_sys("cd ..;rm -f apks;ln -sf ../%s apks" % str1)

    project_info = get_project_info(project_name)
    _ensure_apks_repo_2066(project_info)

    global gCustomRootRO
    global gOverlayRootRO
    global gPatchsetRootRO
    if os.path.exists(".repo"):
        gCustomRootRO = "vendor/vanzo_custom"
        gOverlayRootRO = "vendor/vanzo_custom/overlay_projects"
        gPatchsetRootRO = "vendor/vanzo_custom/patch_projects"
    else:
        gCustomRootRO = "ro/%s/vanzo_custom" % project_info["repo"]
        gOverlayRootRO = "%s/overlay_projects" % gCustomRootRO
        gPatchsetRootRO = "%s/patch_projects" % gCustomRootRO

        if not os.path.exists(gCustomRootRO):
            ro_root = os.path.dirname(gCustomRootRO)
            if not os.path.exists(ro_root):
                os.makedirs(ro_root)
            my_sys('''cd %s;git clone vanzo:%s/vendor/vanzo_custom;cd vanzo_custom;git checkout %s;'''%(ro_root, project_info['repo'], project_info['vtrunk']))
        else:
            my_sys("cd %s; git clean -xfd; git reset --hard $(git rev-parse --symbolic-full-name --abbrev-ref @{u});git checkout %s;git pull" % (gCustomRootRO, project_info["vtrunk"]))
    #else:
    #    my_sys("cd %s; repo sync .;git checkout %s 2> /dev/null" % (gCustomRootRO, project_info["vtrunk"]))

################################################################################
########@@ For Project custom , fallback rules and handling func
################################################################################

OVERLAY_KEY = "\.overlay\." #to be used where . is special, such as in shell cmd
OVERLAY_KEY2 = ".overlay."
PATCHSET_KEY = "\.patchset\."
PATCHSET_KEY2 = ".patchset."

fallback_rules_keys_i = ( "_dev", "_v3", "_r4", "_ics", "_kk", "_jb7", "_jb9", "_tdd", "_lte", "_ds5", "_ds3","_ds", "_jb5", "_jb3", "_jb2", "_jb", "_mul", "_twog", "_cta",
# Vanzo:yucheng on: Sun, 19 Jan 2014 15:15:47 +0800
# Added for freezed projects
    "_freeze",
# End of Vanzo: yucheng
    "_aphone", "_ephone", "_sphone", "_vphone", "_tphone", "_ophone", "_cphone", "mt13_", "mt15_", "mt17_",
# Vanzo:yucheng on: Sun, 19 Jan 2014 15:15:47 +0800
# Added for freezed projects
    "_tphone-v1",
    "_tphone-v3",
# End of Vanzo: yucheng
    "mt15m_x200b", "mt15m_x200c",
    "mt15m_x300b", "mt15m_x300bp","mt15m_x300c",
    "mt15m_x300mbp","mt15m_x300mc","mt15m_x300mcbp",
    "mt17_x1a-1","mt17r2_z1a",
    "mt75r2_z1a","mt75r2_z1-w",
    "mt72_f100cl",
    "mt72_f99cl",
    "mt72_k1cl",
    "mt72_k22cl",
    "mt72_x12cl",
    "mt72_z12cl",
    "mt72_z15cl",
    "mt72_z16cl",
    "mt72_z18cl",
    "mt72_z19cl",
    "mt72_z2cl",
    "mt72_z25cl",
    "mt72_z26cl",
    "mt72_z27cl",
    "mt72_z35ccl",
    "mt72_z5cl",
    "mt72_z9cl",
    "mt72_z953cl",
    "mt72_z39cl",
    "mt82_a15cl",
    "mt82_a25cl",
    "mt82_a26cl",
    "mt82_a6cl",
    "mt82_a8cl",
    "mt82_a936cl",
    "mt82_a9cl",
    "mt82_k28cl",
)

fallback_rules_keys = []
fallback_rules_keys.extend(fallback_rules_keys_i)

fallback_rules_len = len(fallback_rules_keys)
fallback_rules_maps = { "_dev":"", "_v3":"", "_r4":"", "_ics":"", "_kk":"", "_jb7":"", "_jb9":"", "_tdd":"", "_lte":"", "_ds3":"","_ds":"", "_ds5":"", "_jb5":"", "_jb3":"", "_jb2":"", "_jb":"", "_mul":"", "_twog":"", "_cta":"",
# Vanzo:yucheng on: Sun, 19 Jan 2014 15:17:13 +0800
# Added for freezed projects
    "_freeze":"",
# End of Vanzo: yucheng
    "_aphone":"", "_ephone":"", "_sphone":"", "_vphone":"", "_tphone":"", "_ophone":"", "_cphone":"",
    "mt13_":"mt73_", "mt15_":"mt75_", "mt17_":"mt77_",
# Vanzo:yucheng on: Sun, 19 Jan 2014 15:17:13 +0800
# Added for freezed projects
    "_tphone-v1":"_tphone",
    "_tphone-v3":"_tphone",
# End of Vanzo: yucheng
    "mt15m_x200b":"mt15m_x200", "mt15m_x200c":"mt15m_x200",
    "mt15m_x300b":"mt15m_x300", "mt15m_x300bp":"mt15m_x300","mt15m_x300c":"mt15m_x300",
    "mt15m_x300mbp":"mt15m_x300m","mt15m_x300mc":"mt15m_x300m","mt15m_x300mcbp":"mt15m_x300m",
    "mt17_x1a-1":"mt17_x1-1","mt17r2_z1a":"mt17r2_z1",
    "mt75r2_z1a":"mt75r2_z1","mt75r2_z1-w":"mt75r2_z1",
    "mt72_f100cl":"mt72_f100",
    "mt72_f99cl":"mt72_f99",
    "mt72_k1cl":"mt72_k1",
    "mt72_k22cl":"mt72_k22",
    "mt72_x12cl":"mt72_x12",
    "mt72_z12cl":"mt72_z12",
    "mt72_z15cl":"mt72_z15",
    "mt72_z16cl":"mt72_z16",
    "mt72_z18cl":"mt72_z18",
    "mt72_z19cl":"mt72_z19",
    "mt72_z2cl":"mt72_z2",
    "mt72_z25cl":"mt72_z25",
    "mt72_z26cl":"mt72_z26",
    "mt72_z27cl":"mt72_z27",
    "mt72_z35ccl":"mt72_z35cl",
    "mt72_z5cl":"mt72_z5",
    "mt72_z9cl":"mt72_z9",
    "mt72_z953cl":"mt72_z953",
    "mt72_z39cl":"mt72_z39",
    "mt82_a15cl":"mt82_a15",
    "mt82_a25cl":"mt82_a25",
    "mt82_a26cl":"mt82_a26",
    "mt82_a6cl":"mt82_a6",
    "mt82_a8cl":"mt82_a8",
    "mt82_a936cl":"mt82_a936",
    "mt82_a9cl":"mt82_a9",
    "mt82_k28cl":"mt82_k28",
}

gCustomRootRO = ""
gOverlayRootRO = ""
gPatchsetRootRO = ""
gCustomRootRW = ""
gOverlayRootRW = ""
gPatchsetRootRW = ""

def gen_unique_overlays_list(project1):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project1)
    cmd = """find %s -type f  | grep '%s' | sed 's/%s.*//g' | sort | uniq""" % (gOverlayRootRO, OVERLAY_KEY, OVERLAY_KEY)
    uniq_overlays = commands.getstatusoutput(cmd)[1].split()
    cmd = """find %s -type l  | grep '%s' | sed 's/%s.*//g' | sort | uniq""" % (gOverlayRootRO, OVERLAY_KEY, OVERLAY_KEY)
    uniq_overlays.extend(commands.getstatusoutput(cmd)[1].split())
    cmd = """find %s -type d  | grep '%s' | sed 's/%s.*//g' | sort | uniq""" % (gOverlayRootRO, OVERLAY_KEY, OVERLAY_KEY)
    uniq_overlays.extend(commands.getstatusoutput(cmd)[1].split())
    return list(set(uniq_overlays))

def gen_unique_patchset_list(project1):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project1)
    cmd = """find %s -type f  | grep '%s' | sed 's/%s.*//g' | sort | uniq""" % (gPatchsetRootRO, PATCHSET_KEY, PATCHSET_KEY)
    uniq_patchsets = commands.getstatusoutput(cmd)[1].split()
    cmd = """find %s -type l  | grep '%s' | sed 's/%s.*//g' | sort | uniq""" % (gPatchsetRootRO, PATCHSET_KEY, PATCHSET_KEY)
    uniq_patchsets.extend(commands.getstatusoutput(cmd)[1].split())
    return list(set(uniq_patchsets))

def _mismatch_legacy(patch, project_name):
    def _fortphone():
        return '_fortphone.patchset.' in patch or '_fortphone.overlay.' in patch
    def _forvtrunk():
        return '_forvtrunk.patchset.' in patch or '_forvtrunk.overlay.' in patch
    def _is_vanilla():
        return not re.search(r'_[a-z]phone', project_name)

    patch = os.path.basename(patch)
    if _is_vanilla() and _fortphone():
        return True
    if _is_tphone(project_name) and _forvtrunk():
        return True

    return False

def gen_project_overlays_list(project_name, uniq_overlays):
    project_overlays = {}
    for one in uniq_overlays:
        two = one + OVERLAY_KEY2 + project_name
        three = project_custom_get_fallback(two)
        if three != None:
            if _mismatch_legacy(three, project_name):
                continue

            one2 = one.replace(gOverlayRootRO + "/", "")
            project_overlays[one2] = three
    return project_overlays

def gen_project_patchset_list(project_name, uniq_patchsets, check=True):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project_name)
    cwd = os.getcwd() + "/"
    project_patchsets = []
    for one in uniq_patchsets:
        two = one + PATCHSET_KEY2 + project_name
        three = project_custom_get_fallback(two)
        if three != None:
            if _mismatch_legacy(three, project_name):
                continue

            one2 = os.path.dirname(one.replace(gPatchsetRootRO + "/", ""))
            if not check:
                four = cwd + three
                if os.path.exists(four):
                    pass
                elif os.path.exists(four + ".keep"):
                    four += ".keep"
                elif os.path.exists(four + ".delete"):
                    four += ".delete"
                project_patchsets.append((one2, four))
            elif os.path.exists(one2):
                project_patchsets.append((one2, cwd + three))
    return project_patchsets

def project_custom_build_fallback_list(filename1):
    if len(fallback_rules_keys) > 100:
        return
    with open(filename1) as myfile:
        for line in myfile:
            if not "#" in line and line.strip() != 0:
                list1 = line.strip().split(":")
                if len(list1) == 2:
                    k1 = list1[0].strip()
                    v1 = list1[1].strip()
                    assert npn(k1) == k1, "project %s not normalized!" % k1
                    assert npn(v1) == v1, "project %s not normalized!" % v1
                    fallback_rules_keys.append(k1)
                    fallback_rules_maps[k1] = v1
    fallback_rules_keys.reverse()

def _project_custom_exists_any(file1):
    def _project_legit():
        project_info = get_project_info(project_name)
        # 72 only
        if not project_info['id'].startswith('mt6572jb3'):
            return True
        # 72 contains two project folders
        projects = set(('vanzo72_wet_jb3', 'vanzo72_wet_lca')) - set((project_info['project'],))
        # if other 'project' folder in path, then filter it out
        if any(i.join('//') in file1 for i in projects):
            return False
        return True

    # if patch file in different 'project' folder, then 'pretend'
    #+file not exist
    project_name = get_project_name()
    if not _project_legit():
        return False

    if os.path.exists(file1 + ".delete"):
        my_dbg(_yellow("Warning...%s with .delete extension" % file1))
        return True
    if os.path.exists(file1 + ".keep"):
        my_dbg(_yellow("Warning...%s with .keep extension" % file1))
        return True
    if os.path.exists(file1):
        return True
    return False

def _does_fallback_rule_match(rule, project):
    # explicit fallback rules
    if rule not in fallback_rules_keys_i and rule == project:
        return True
    # implicit fallback rules
    if rule in fallback_rules_keys_i and rule in project:
        return True
    return False

def _project_custom_get_fallback2(one):
    list1 = [one]
    while len(list1) > 0:
        two = list1.pop(0)
        for onerule in fallback_rules_keys:
            p1 = two.find(OVERLAY_KEY2)
            if p1 < 0:
                p1 = two.find(PATCHSET_KEY2)
            if _does_fallback_rule_match(onerule, two[p1:].replace(OVERLAY_KEY2, '').replace(PATCHSET_KEY2, '')):
                three = two[:p1] + two[p1:].replace(onerule, fallback_rules_maps[onerule])
                if _project_custom_exists_any(three):
                    return three
                else:
                    list1.append(three)
    return None

fallback_exclude_list = (
     "build/tools/buildinfo.sh",
)

def _xphone_filter_out_vtrunk_patchset(npn_project, patchset):
    def _xphone_needs_filter_out(dir_name, ui):
        return os.path.exists(dir_name + '/no_vtrunk_patch_for_' + ui) or \
            os.path.exists(dir_name + '/no_vtrunk_patch_for_xphone')

    xphones = ('aphone', 'ephone', 'vphone', 'tphone', 'ophone')
    for suffix in ('_' + x for x in xphones):
        if patchset.endswith(suffix):
            return patchset

    dir_name = os.path.dirname(patchset)

    for suffix in xphones:
        if globals()['_is_' + suffix](npn_project):
            if _xphone_needs_filter_out(dir_name, suffix):
                return None
    return patchset

def project_custom_get_fallback(two):
    pos1 = two.find(".overlay.")
    if pos1 < 0:
        pos1 = two.find(".patchset.")
        raw_project_name = two[pos1 + 10:].split("/")[0]
    else:
        raw_project_name = two[pos1 + 9:].split("/")[0]
    two = npn(two)
    project_name = npn(raw_project_name)
    if len(fallback_rules_keys) <= fallback_rules_len:
        assert os.path.exists("%s/fallback_extra.txt" % gCustomRootRO)
        if two[two.find("/", 22) + 1:pos1] not in fallback_exclude_list:
            project_custom_build_fallback_list("%s/fallback_extra.txt" % gCustomRootRO)
    if _project_custom_exists_any(two):
        return two
    else:
        three = _project_custom_get_fallback2(two)
        if three:
            three = _xphone_filter_out_vtrunk_patchset(two, three)
        if three:
            return three
        else:
            if two[two.find("/", 22) + 1:pos1] in fallback_exclude_list:
                return

            for one in ("cphone",):
                if one in project_name:
                    four = two.replace(project_name, "all_%s_projects" % one)
                    if _project_custom_exists_any(four):
                        return four

            for one in ("twog",):
                pseudo_project_name = get_project_name() if os.path.exists(".repo") else raw_project_name
                if one in pseudo_project_name:
                    four = two.replace(project_name, "all_%s_projects" % one)
                    if _project_custom_exists_any(four):
                        return four

            if os.path.exists(".repo"):
                project_info = get_project_info(get_project_name())
                for one in ("nand", "emmc"):
                    if project_info["storage"] == one:
                        four = two.replace(project_name, "all_%s_projects" % one)
                        if _project_custom_exists_any(four):
                            return four

            if "lca" in project_name:
                four = two.replace(project_name, "all_lca_projects")
                if _project_custom_exists_any(four):
                    return four

            #all_mul_tphone_projects
            pseudo_project_name = get_project_name() if os.path.exists(".repo") else raw_project_name
            ui = get_project_ui(project_name)
            if "_mul_" in pseudo_project_name and "_tphone_" in pseudo_project_name:
                four = "all_mul_tphone_projects"
                if _project_custom_exists_any(four):
                    return four

            for one in ("aphone", "ephone", "sphone", "vphone", "tphone", "ophone", "vtrunk"):
                if one == ui:
                    four = two.replace(project_name, "all_%s_projects" % one)
                    if _project_custom_exists_any(four):
                        return four

            for one in ("mul",):
                if one in pseudo_project_name:
                    four = two.replace(project_name, "all_%s_projects" % one)
                    if _project_custom_exists_any(four):
                        return four

            list1 = project_name.split("_")
            four = two.replace(project_name, "all_%s_%s_projects" % (list1[0], list1[1]))
            five = two.replace(project_name, "all_%s_%s_%s_projects" % (list1[0], list1[1], ui))
            six = two.replace(project_name, "all_%s_%s_%s_projects" % (list1[0], list1[1], list1[3]))
            if _project_custom_exists_any(six):
                return six
            if _project_custom_exists_any(five):
                return five
            if _project_custom_exists_any(four):
                return four

            for one in ("mt13", "mt15", "mt17"):
                if project_name.startswith(one):
                    four = two.replace(project_name, "all_%s_projects" % one)
                    if _project_custom_exists_any(four):
                        return four

            for one in ("std","swcdma","sgsm","td", "wcdma", "gsm", "ldata", "mt6735_3m_fdd_cs", "mt6735_5m_cs", "mt6735_3m_tdd_cs"):
                pseudo_project_name = get_project_name() if os.path.exists(".repo") else project_name
                if pseudo_project_name.endswith('_' + one) or '_' + one + '_' in pseudo_project_name:
                    four = two.replace(project_name, "all_%s_projects" % one)
                    if _project_custom_exists_any(four):
                        return four

            list1 = project_name.split("_")
            four = two.replace(project_name, "all_%s_projects" % list1[3])
            if _project_custom_exists_any(four):
                return four

            four = two.replace(project_name, "all_projects")
            if _project_custom_exists_any(four):
                return four

def _project_custom_check_fallback2(project1, project2, depth=0):
    """recursive run"""
    if depth > 5:
        return None
    three_list = []
    for onerule in fallback_rules_keys:
        if _does_fallback_rule_match(onerule, project1):
            three = project1.replace(onerule, fallback_rules_maps[onerule])
            if three == project2:
                return True
            else:
                three_list.append(three)
    for three in three_list:
        four = _project_custom_check_fallback2(three, project2, depth + 1)
        if four:
            return True
    return False

def project_custom_check_fallback(project1, project2):
    if len(fallback_rules_keys) <= 10:
        assert os.path.exists("%s/fallback_extra.txt" % gOverlayRootRO)
        project_custom_build_fallback_list("%s/fallback_extra.txt" % gCustomRootRO)
    return _project_custom_check_fallback2(project1, project2)

def check_duplicate_overlay_files(uniq_overlays, fixit=False, error_file=None):
    for one in uniq_overlays:
        cmd = """find %s -type f | grep '%s' | sort | uniq""" % (gCustomRootRO, one)
        files = commands.getstatusoutput(cmd)[1].split()
        if len(files) < 2:
            continue
        isDir = False
        for two in files:
            if "/" in two.replace(one,""):
                isDir = True
                break
        if isDir:
            continue
        _check_duplicate_overlay_files2(files, fixit, error_file)

def _check_duplicate_overlay_files2(files, fixit, error_file):
    """compare a list of files, find out same"""
    list_len = len(files)
    for one in range(0, list_len):
        if not os.path.isfile(files[one]):
            continue
        for two in range(one+1, list_len):
            if not os.path.isfile(files[one]):
                break
            if not os.path.isfile(files[two]):
                continue
            if filecmp.cmp(files[one], files[two], False):
                pos = files[one].rfind("/")
                pos2 = files[two].rfind("/")
                #we only compre files under same dir
                if files[one][:pos] == files[two][:pos2]:
                    _check_duplicate_overlay_files3(files[one], files[two], fixit, error_file)

def _check_duplicate_overlay_files3(file1, file2, fixit, error_file):
    """
    file1 and file2 are same, should link one to another
    """
    my_dbg(_yellow("Warning! Found duplicate files! should use link!"), True)
    my_dbg(_yellow(file1), True)
    my_dbg(_yellow(file2), True)
    if error_file != None:
        my_sys("echo Warning! Found duplicate files! should use link! >> %s" % error_file)
        my_sys("echo %s >> %s" % (file1, error_file))
        my_sys("echo %s >> %s" % (file2, error_file))

    if not fixit:
        return
    assert os.path.isfile(file1)
    assert os.path.isfile(file2)

    dir1 = os.path.dirname(file1)
    file1a = os.path.basename(file1)
    file2a = os.path.basename(file2)
    cmd = "find %s -type l" % dir1
    list1 = commands.getstatusoutput(cmd)[1].split()
    file1b = False
    file2b = False
    for one in list1:
        cmd = "ls -l %s" % one
        output2 = commands.getstatusoutput(cmd)[1].split(">")[-1].strip()
        output2 = os.path.basename(output2)
        if output2 == file1a:
            if file2b:
                my_dbg(_yellow("Warning, both file1 and file2 has files link to it!!!"), True)
                my_sys("ln -sf %s %s" % (file2a, one))
            else:
                file1b = True
        elif output2 == file2a:
            if file1b:
                my_dbg(_yellow("Warning, both file1 and file2 has files link to it!!!"), True)
                my_sys("ln -sf %s %s" % (file1a, one))
            else:
                file2b = True
    assert not file1b or not file2b
    if file1b:
        cmd = "ln -sf %s %s" % (file1a, file2)
    else:
        cmd = "ln -sf %s %s" % (file2a, file1)
    my_sys(cmd)

check_dangerous_overlay_exclude_list = (
     "frameworks/base/data/sounds/Android.mk",
     "build/target/product/core_default_sound.mk",
     "vendor/mediatek/etc/apns-conf.xml",
)

def check_dangerous_overlay_files(project1):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project1)
    cmd1 = """ find %s -mindepth 2 -type f  | grep '\.overlay\.' | grep -v '\.jpg' | grep -v '\.mp3' | grep -v '\.zip' | grep -v '\.so\.' | grep -v '\.bmp' | grep -v '\.MP3' | grep -v '\.ogg' | grep -v '\.xls' | grep -v '\.png' | grep -v '\.apk' | grep -v '\.ttf' """ % gOverlayRootRO
    list1 = commands.getstatusoutput(cmd1)[1].split()
    list2 = []
    for one in list1:
        if "ASCII" in commands.getstatusoutput("file " + one)[1]:
            list2.append(one)
    for one in list2:
        _check_dangerous_overlay_files2(one)

def _get_change_time(file1):
    cmd1 = "cd " + file1[:file1.rfind("/")] + "; git log " + file1[file1.rfind("/")+1:]
    list1 = commands.getstatusoutput(cmd1)[1].split("\n")
    if len(list1) < 3:
        return
    for one in list1:
        if one.startswith("Date:"):
            line2 = one[5:].strip()[:-5]
            return parser.parse(line2)

change_time_map = {}
def _check_dangerous_overlay_files2(file1):
    file2 = file1[24:file1.find(OVERLAY_KEY2)]
    if file2 in check_dangerous_overlay_exclude_list:
        return
    if not os.path.exists(file2):
        return
    if not change_time_map.has_key(file2):
        change_time_map[file2] = _get_change_time(file2)
    dt2 = change_time_map[file2]
    if dt2 == None:
        return
    dt1 = _get_change_time(file1)
    rd1 = relativedelta.relativedelta(dt1, dt2)
    if ((((rd1.months * 30  + rd1.days) * 24 + rd1.hours) * 60) + rd1.minutes) * 60 + rd1.seconds < 0:
        my_dbg("Error! Found dangerous overlay file!")
        my_sys("echo file:" + file1)

def check_special_overlay_files(project1, key1, fixit=False):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project1)

    cmd1 = """ find vendor | grep %s """ % key1
    list1 = commands.getstatusoutput(cmd1)[1].split()
    for one in list1:
        my_dbg("Found project extension with _v3", True)
        my_dbg(one, True)
        if fixit:
            my_rename(one, one.replace("_v3",""))

def check_redundant_overlay_files(project1, uniq_overlays, fixit=False, error_file=None):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project1)
    for one in uniq_overlays:
        cmd = """find vendor | grep '%s' | sort | uniq""" % one
        files = commands.getstatusoutput(cmd)[1].split()
        if len(files) < 2:
            continue
        isDir = False
        for two in files:
            if "/" in two.replace(one,""):
                isDir = True
                break
        if isDir:
            continue
        _check_redundant_overlay_files2(files, fixit, error_file)

def _check_redundant_overlay_files2(files, fixit, error_file):
    """compare a list of files, find out same"""
    list_len = len(files)
    for one in range(0, list_len):
        if not os.path.exists(files[one]):
            continue
        for two in range(one+1, list_len):
            if not os.path.exists(files[one]):
                break
            if not os.path.exists(files[two]):
                continue
            if filecmp.cmp(files[one], files[two], False):
                pos = files[one].rfind("/")
                pos2 = files[two].rfind("/")
                #we only compre files under same dir
                if files[one][:pos] == files[two][:pos2]:
                    project1 = files[one].split(".")[-1]
                    project2 = files[two].split(".")[-1]
                    is_redundant = False
                    if project_custom_check_fallback(project1, project2):
                        is_redundant = True
                        file1 = files[one]
                        file2 = files[two]
                    elif project_custom_check_fallback(project2, project1):
                        is_redundant = True
                        file1 = files[two]
                        file2 = files[one]
                    if is_redundant:
                        my_dbg(_yellow("Warning! Found redundant files!"), True)
                        my_dbg(_yellow(file1), True)
                        my_dbg(_yellow(file2), True)
                        if error_file != None:
                            my_sys("echo Warning! Found redundant files! >> %s" % error_file)
                            my_sys("echo %s >> %s" % (file1, error_file))
                            my_sys("echo %s >> %s" % (file2, error_file))
                        if fixit:
                            my_remove(file1, file2)

def check_dead_overlay_files(project1):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project1)
    cmd = "find vendor -type l"
    list1 = commands.getstatusoutput(cmd)[1].split()
    for one in list1:
        cmd2 = "cat %s" % one
        ret2 = commands.getstatusoutput(cmd2)[0]
        if ret2 != 0:
            cmd2 = "cd %s" % one
            ret2 = commands.getstatusoutput(cmd2)[0]
        if ret2 != 0:
            my_dbg(_yellow("Warning! Found dead link!"), True)
            my_dbg(_yellow(one), True)

################################################################################
########@@ For Update Overlay Files
################################################################################
PROJECT_ENV_KEY = "VANZO2_PROJECT_NAME"
COMITTER_ENV_KEY = "COMITTER_NAME"
search_dirs = (
    "frameworks/base",
    "mediatek/source",
    "packages",
    "vendor/overlay",
    "vendor/overlay_res",
)

def _get_project_buildinfo(map1, one):
    list1 = [one]
    while len(list1) > 0:
        two = list1.pop(0)
        for onerule in fallback_rules_keys:
            if _does_fallback_rule_match(onerule, two):
                three = two.replace(onerule, fallback_rules_maps[onerule])
                if map1.has_key(three):
                    return map1[three]
                else:
                    list1.append(three)
    return None

def get_project_buildinfo(file1, project_name):
    map1 = {}
    with open(file1) as myfile:
        for line in myfile:
            if '#' in line:
                line2 = line[:line.find('#')]
            else:
                line2 = line
            a = line2.strip().split(":")
            if len(a) >= 5:
                map1[a[0].strip()] = a[1:]
    if map1.has_key(project_name):
        return map1[project_name]
    if len(fallback_rules_keys) <= fallback_rules_len:
        assert os.path.exists("%s/fallback_extra.txt" % gCustomRootRO)
        project_custom_build_fallback_list("%s/fallback_extra.txt" % gCustomRootRO)
    return _get_project_buildinfo(map1, project_name)

def update_buildinfo():
    ret = my_sys("cd build/; git status | grep buildinfo")
    if ret == 0:
        return False

    project_name = get_project_name()
    project_info = get_project_info(project_name)
    list1 = project_name.split("_")
    device = list1[1].upper()
    model = list1[2].upper()
    manufaturer = list1[3].upper()
    display = model
    notshowdate = False

    file1 = "./vendor/vanzo_custom/overlay_projects/build/tools/buildinfo.custom"
    list1 = get_project_buildinfo(file1, project_name)
    if list1 != None and len(list1) >= 4:
        a1 = list1[0].strip()
        if len(a1) != 0:
            model = a1
        a2 = list1[1].strip()
        if a2 == "notshowdate":
            notshowdate = True
        a3 = list1[2].strip()
        if len(a3) != 0:
            display = a3
        a4 = list1[3].strip()
        if len(a4) != 0:
            manufaturer = a4

    a = project_name.split("_")
    filename1 = "build/tools/buildinfo.sh"
    four =  filename1 + ".tmp"
    with open(filename1, "r") as in_file:
        with open(four, "w") as out_file:
            for line in in_file:
                line2 = line.replace("$TARGET_DEVICE", device)
                line2 = line2.replace("$PRODUCT_MODEL", model)
                line2 = line2.replace("$PRODUCT_NAME", device)
                line2 = line2.replace("$FLAVOR", project_name)
                if project_info["id"] in ("mt6575ics", "mt6575icsr2","mt6577ics"):
                    line2 = line2.replace("$TARGET_BOARD_PLATFORM", a[0].upper()+ "_" + a[1].upper() + "_ICS")
                if project_info["id"] == "mt6513r4":
                    line2 = line2.replace("$TARGET_BOARD_PLATFORM", a[0].upper()+ "_" + a[1].upper() + "_R4")
                elif project_info["id"] in ("mt6573v3", "mt6515", "mt6575gb", "mt6575gbr2", "mt6515cmcc"):
                    line2 = line2.replace("$TARGET_BOARD_PLATFORM", a[0].upper()+ "_" + a[1].upper() + "_V3")
                else:
                    line2 = line2.replace("$TARGET_BOARD_PLATFORM", a[0].upper()+ "_" + a[1].upper())

                if "_cphone" in project_name or notshowdate:
                    line2 = line2.replace("$BUILD_DISPLAY_ID",  display)
                else:
                    line2 = line2.replace("$BUILD_DISPLAY_ID",  display + " `date +%Y%m%d-%H%M%S`")
                if len(manufaturer) > 0:
                    line2 = line2.replace("$PRODUCT_MANUFACTURER",  manufaturer)
                out_file.write(line2)
    my_sys("mv -f " + four + " " + filename1)

    filename1 = "build/core/Makefile"
    four =  filename1 + ".tmp"
    with open(filename1, "r") as in_file:
        with open(four, "w") as out_file:
            for line in in_file:
                line2 = line
                if "build_desc" in line:
                    line2 = line2.replace("$(TARGET_PRODUCT)", device)
                elif "BUILD_FINGERPRINT" in line:
                    line2 = line2.replace("$(TARGET_PRODUCT)", device)
                    line2 = line2.replace("$(TARGET_DEVICE)", device)
                out_file.write(line2)
    my_sys("mv -f " + four + " " + filename1)

    return True

def get_project_name():
    project_name = ""
    if os.environ.get(PROJECT_ENV_KEY):
        project_name = os.environ[PROJECT_ENV_KEY]
    if len(project_name) < 2:
        while not os.path.exists(".repo/manifest.xml"):
            os.chdir("..")
            if os.getcwd() == "/":
                my_dbg(_red("where r u? I can not find code base!"))
                return project_name
        name = commands.getstatusoutput("ls -l .repo/manifest.xml")[1]
        pos = name.rfind("/")
        pos2 = name.rfind(".")
        project_name = name[pos+1:pos2]
    return project_name

VANZO_PRINT_PO = 'VANZO_PRINT_PO'

def update_overlays(project_overlays):
    my_dbg("update_overlays")
    for one in project_overlays:
        if os.path.exists(project_overlays[one] + ".keep") or os.path.exists(npn(project_overlays[one]) + ".keep"):
            if os.environ.get(VANZO_PRINT_PO):
                print('OIO:{0}'.format(project_overlays[one] + '.keep'))
            continue
        elif os.path.exists(project_overlays[one] + ".delete") or os.path.exists(npn(project_overlays[one]) + ".delete"):
            if os.environ.get(VANZO_PRINT_PO):
                print('OIO:{0}'.format(project_overlays[one] + '.delete'))
            my_sys("rm -rf " + one)
        else:
            if os.environ.get(VANZO_PRINT_PO):
                print('OIO:{0}'.format(project_overlays[one]))
            if os.path.isfile(project_overlays[one]):
                my_sys("rm -f " + one)
                pos = one.rfind("/")
                if pos > 0:
                    two = one[0:pos]
                    my_sys("mkdir -p " + two)
                my_sys("cp -f " + project_overlays[one] + " " + one)
            elif os.path.isdir(project_overlays[one]):
                my_sys("mkdir -p " + one)
                my_sys("cp -afL " + project_overlays[one] + "/* " + one)

def update_patchsets(project_patchsets, project, partial=False):
    my_dbg("update_patchsets")
    for one in project_patchsets:
        if os.path.exists(one[1] + ".keep"):
            if os.environ.get(VANZO_PRINT_PO):
                print('PIO:{0}:{1}'.format(one[0], one[1] + '.keep'))
            continue
        elif os.path.getsize(one[1]) < 10:
            continue
        elif not os.path.exists(one[0]):
            continue
        else:
            if os.environ.get(VANZO_PRINT_PO):
                print('PIO:{0}:{1}'.format(one[0], one[1]))
            cmd = "cd " + one[0] + "; patch -p1 < " + one[1]
            if commands.getstatusoutput(cmd)[0]:
                pos1 = one[1].find("patch_projects")
                cmd2 = "cd %s;git log --pretty=%%aN:%%ad -1 --date='iso' %s" % (one[1][:pos1], one[1][pos1:])
                msg2 = commands.getstatusoutput(cmd2)[1][:-6]
                msg1 = "Error! %s, %s" % (one[1][pos1:], msg2)
                if not os.path.exists("out/target/product"):
                    my_sys("mkdir -p out/target/product")
                my_sys("echo '" + msg1 + "' >> out/target/product/%s_patch_projects.log_err"%project)
                my_dbg(_red(msg1))
                if not partial:
                    assert False,"patch error!!!!!!!!!!!!!!!!!!!!!"
            else:
                cmd = "cd " + one[0] + "; find . -name '*.orig' -type f | xargs rm -rf"
                my_sys(cmd)

def do_concat_files(project_name):
    project = get_project_info(project_name)["project"]
    filelists1 = {
    "mediatek/config/%s/" % project  :("ProjectConfig.mk", "global", "global2", "bsp", "mt13", "mt15", "mt17", "app", "app2", "modem", "aphone", "cphone", "ephone", "sphone", "vphone", "tphone", "ophone", "nomul","lang", "ui","mului", "custom",),
    "build/target/product/"         :("%s.mk" % project,"app","aphone","ephone","sphone","vphone","tphone","ophone","custom", "cphone",),
    "frameworks/base/data/sounds/"  :("Android.mk", "aphone", "cphone", "ephone", "sphone","vphone","tphone","ophone","custom", "ui",),
    "vendor/google/3rdapp/"         :("Android.mk", "app", "rib", "custom",),
    "vendor/google/userdata/"       :("Android.mk", "app", "custom",),
    }
    for key1 in filelists1:
        list1 = filelists1[key1]
        targetfile1 = key1  + list1[0]
        if not os.path.exists(targetfile1):
            continue
        for two in list1[1:]:
            file1 = targetfile1 + "." + two
            if not os.path.exists(file1):
                continue

            hit = False
            for one in ("aphone", "cphone", "ephone", "sphone", "vphone", "tphone", "ophone","mt13", "mt15", "mt17"):
                if one in two and  not one in project_name:
                    hit = True
                    break
            if hit:
                continue
            if two == "nomul" and "_mul" in project_name:
                continue

            msg0 = "#" * 78
            msg1 = "#" * 8 + "Below Setting is from " + list1[0] + "." + two + ", dont edit directly" + "#" * 8
            my_sys("echo >> " + targetfile1)
            my_sys("echo '" + msg0 + "' >> " + targetfile1)
            my_sys("echo '" + msg0 + "' >> " + targetfile1)
            my_sys("echo '" + msg1 + "' >> " + targetfile1)
            my_sys("echo '" + msg0 + "' >> " + targetfile1)
            my_sys("echo '" + msg0 + "' >> " + targetfile1)
            my_sys("echo >> " + targetfile1)
            my_sys("cat "  + file1 + " >> " + targetfile1)

png_exclude_list = (
     "./packages/apps/Phone/res/drawable-mdpi-finger/ic_call_backspace.png",
     "./packages/apps/Phone/res/drawable-hdpi/vt_incall_local.png",
)

def remove_other_res(project):
    lcm_width, lcm_height = get_dimension_from_project_config("./mediatek/config/%s/ProjectConfig.mk" % project)
    lcm_density = get_resolution_from_dimension((lcm_width, lcm_height))
    pixels = lcm_width * lcm_height

    #remove res of other unrelated res
    remove_list = []
    grep_dirs = ["\-320x240", "\-400x240", "\-480x320", "\-800x480", "\-854x480"]
    if pixels == 320*240:
        grep_dirs.remove("\-320x240")
    elif pixels == 400*240:
        grep_dirs.remove("\-400x240")
    elif pixels == 400*320:
        grep_dirs.remove("\-400x320")
    elif pixels == 800*480:
        grep_dirs.remove("\-800x480")
    elif pixels == 854*480:
        grep_dirs.remove("\-854x480")
    for one in search_dirs:
        if not os.path.exists(one):
            continue
        for two in grep_dirs:
            cmd1 = "find %s -type d  | grep '%s' " % (one, two)
            out1 = commands.getstatusoutput(cmd1)[1]
            remove_list.extend(out1.split())
    for one in remove_list:
        cmd1 = "rm -rf " + one
        my_sys(cmd1)

    #remove other png
    grep_dirs = ["\-ldpi", "\-mdpi", "\-hdpi"]
    if lcm_density  == "ldpi":
        grep_dirs.remove("\-ldpi")
    elif lcm_density  == "mdpi":
        grep_dirs.remove("\-mdpi")
    elif lcm_density  == "hdpi":
        grep_dirs.remove("\-hdpi")

    remove_list = []
    for one in search_dirs:
        if not os.path.exists(one):
            continue
        for two in grep_dirs:
            cmd1 = "find %s -type d  | grep '%s' " % (one, two)
            remove_list.extend(commands.getstatusoutput(cmd1)[1].split())

    for one in remove_list:
        #my_dbg("now handling %s...%d of %d" % (one, remove_list.index(one), len(remove_list)))
        cmd1 = "find %s -type f  | grep '\.png' " % (one)
        filelist1 = commands.getstatusoutput(cmd1)[1].split()
        for two in filelist1:
            file1 = two[two.rfind("/") + 1:]
            dir1 = one[:one.rfind("/")]
            cmd1 = "find %s -type f  | grep '/%s' " % (dir1, file1)
            filelist2 = commands.getstatusoutput(cmd1)[1].split()
            if len(filelist2) > 1:
                my_sys("rm -f " + two)
            else:
                pass
                #my_dbg("Warning:" + two)

    for one in png_exclude_list:
        dir1 = one[:one.rfind("/") + 1]
        file1 = one[one.rfind("/") + 1:]

        if not os.path.exists(dir1):
            continue
        if os.path.exists(one):
            continue

        cmd1 = "cd " + dir1 + ";" + "git checkout " + file1 + " 2>/dev/null"
        my_sys(cmd1)

def remove_other_res2(project):
    lcm_width, lcm_height = get_dimension_from_project_config("./mediatek/config/%s/ProjectConfig.mk" % project)
    pixels = lcm_width * lcm_height

    #remove res of other unrelated res
    remove_list = []
    grep_dirs = ["\-320x240", "\-400x240", "\-480x320", "\-800x480", "\-854x480", "\-960x540", "\-960x640", "\-1280x720",]
    for one in grep_dirs:
        two = one[2:].split("x")
        three = int(two[0]) * int(two[1])
        if pixels == three:
            grep_dirs.remove(one)
            break
    for one in search_dirs:
        if not os.path.exists(one):
            continue
        if not os.path.exists(one):
            continue
        for two in grep_dirs:
            cmd1 = "find %s -type d  | grep '%s' " % (one, two)
            remove_list.extend(commands.getstatusoutput(cmd1)[1].split())
    for one in remove_list:
        cmd1 = "rm -rf " + one
        #my_dbg(cmd1)
        my_sys(cmd1)

def _get_project_wallpaper_dir(project):
    project_info = get_project_info(project)
    str1 = ""
    if project_info["android"] == "40":
        str1 = "mediatek/source/packages/WallpaperChooser"
    elif project_info["android"] in ("41", "42",):
        str1 = "mediatek/packages/apps/WallpaperChooser"
    #elif project_info["android"] in ("44",):
    elif ge_kk(project):
        str1 = "vendor/google/extras/WallpaperChooser"
    else:
        str1 = "packages/apps/WallpaperChooser"
    if _is_tphone(project) or _is_ophone(project):
        if ge_kk(project):
            return str1.replace("WallpaperChooser", "WallpaperChooserTphone")
        else:
            return str1.replace("WallpaperChooser", "WallpaperChooser2")
    return str1

def _delete_all_wallpapers_from_wallpaperchooser(project):
    wallpaper_dir = os.path.join(_get_project_wallpaper_dir(project), 'res')
    all_files = glob.glob(os.path.join(wallpaper_dir, 'drawable-*/wallpaper_*.jpg'))
    dimension = _project_custom_gen_project_dimension(project)
    project_info = get_project_info(project)
    res1 = get_resolution_from_dimension(dimension, project_info)
    excluded = glob.glob(os.path.join(wallpaper_dir, 'drawable-{0}/wallpaper_c*.jpg'.format(res1)))
    for wallpaper in list(set(all_files) - set(excluded)):
        os.remove(wallpaper)

#added by wf for kk wallpaper not copy the default paper
def sumFile(fobj):
    m = md5()
    while True:
        d = fobj.read()
        if not d:
            break
        m.update(d)
        del(d)
    return m.hexdigest()
def md5SumLocalFile(fname):
    try:
        f = open(fname, 'rb')
        ret = sumFile(f)
        f.close()
        return ret
    except:
        return None
def is_same_file(src_file,dst_file):
    if not os.path.exists(src_file):
        return False
    if not os.path.exists(dst_file):
        return False
    md5_src=md5SumLocalFile(src_file)
    md5_dst=md5SumLocalFile(dst_file)
    #print "src:%s,dst %s"%(md5_src,md5_dst)
    if md5_src == md5_dst:
        return True
    else:
        return False
#added by wf end

def _copy_wallpapers_from_database_to_wallpaperchosser(project):
    dimension = _project_custom_gen_project_dimension(project)
    project_info = get_project_info(project)
    res1 = get_resolution_from_dimension(dimension, project_info)
    subname = 'vtrunk'
    if _is_aephone(project):
        subname = 'aphone'
    elif _is_tphone(project):
        subname = 'kktphone' if ge_kk(project) else 'tphone'
    elif _is_ophone(project):
        subname = 'ooskktphone'
    src_folder = os.path.join(
        _wallpaper_database_path(),
        '{0}-{1}'.format(subname, '{0}x{1}'.format(dimension[1], dimension[0])))
    wallpaper_dir = os.path.join(_get_project_wallpaper_dir(project), 'res')
    dst_folder = os.path.join(wallpaper_dir, 'drawable-{0}'.format(res1))
    if not os.path.exists(dst_folder):
        my_sys("mkdir -p " + dst_folder)
    xml = os.path.join(wallpaper_dir, 'values/wallpapers.xml')
    wallpapers = get_wallpaper_list_from_wallpaper_xml(xml)
    for wallpaper in [i+'.jpg' for i in wallpapers]:
        if 'wallpaper_c' in wallpaper:
            continue
        shutil.copy2(os.path.join(src_folder, wallpaper), dst_folder)
        shutil.copy2(os.path.join(
                src_folder, wallpaper.replace('.jpg', '_small.jpg')), dst_folder)

def _remove_redundant_wallpapers(project):
    wallpaper_dir = os.path.join(_get_project_wallpaper_dir(project), 'res')
    list1 = glob.glob(os.path.join(wallpaper_dir, "drawable-*/wallpaper_*.jpg"))
    xml = os.path.join(wallpaper_dir, "values/wallpapers.xml")
    list2 = get_wallpaper_list_from_wallpaper_xml(xml)
    for one in list1:
        two = one.replace("_small", "").split("/")[-1].split(".")[0]
        if not two in list2:
            os.remove(one)

def _project_custom_gen_project_dimension(project1):
    project_info = get_project_info(project1)
    return get_dimension_from_project_config('mediatek/config/%s/ProjectConfig.mk' % project_info['project'])

def remove_redundant_wallpapers(project):
    if not os.path.exists(os.path.join(_get_project_wallpaper_dir(project), "res/values/wallpapers.xml")):
        return
    if _does_use_wallpaper_database(project):
        _delete_all_wallpapers_from_wallpaperchooser(project)
        _copy_wallpapers_from_database_to_wallpaperchosser(project)
    else:
        _remove_redundant_wallpapers(project)

def update_geocoding_db(project_name, project_info):
    if project_info["age"] <  PROJECT_INFO["mt6589jb2"]["age"]:
        return
    #if "mul" in project_name and "lca" in project_name:
    if "mul" in project_name:
        mygeocodingdb = "../../database/geocoding_empty.db"
    else:
        mygeocodingdb = "../../database/geocoding.db"
    if not os.path.exists(mygeocodingdb):
        return
    my_sys("cp -f %s mediatek/external/GeoCoding/geocoding.db" % mygeocodingdb)

apnlist = []
apnlist2 = []
apnlist3 = []

APNFILES = (
#   "carrier",
    "mcc",
    "mnc",
    "apn",
    "user",
    "server",
    "password",
    "proxy",
    "port",
    "mmsproxy",
    "mmsport",
    "mmsc",
    "authtype",
    "type",
    "roaming_protocol",
    "protocol",
    "spn",
)

APNFILES2 = (
    "carrier",
    "mcc",
#    "mnc",
    "apn",
    "user",
    "server",
    "password",
    "proxy",
    "port",
    "mmsproxy",
    "mmsport",
    "mmsc",
    "authtype",
    "type",
    "roaming_protocol",
    "protocol",
    "spn",
)

"""
Compare 2 mncs
"""
def myComparator2(A1,A2):
    try:
        m1 = int(A1)
        m2 = int(A2)
    except Exception,e:
        print e
        print A1
        print A2
        sys.exit(-1)

    return cmp(m1,m2)

def apnMatch(i, j):
    l1 = apnlist2[i]
    l2 = apnlist2[j]

    for one in APNFILES2:
        m = 0
        if l1.has_key(one):
            m += 1
        if l2.has_key(one):
            m += 1
        if m == 1:
            return False
        elif m == 2:
            if one == "mnc":
                continue
            if l1[one].strip()!= l2[one].strip():
                return False
    return True

def genApnList(filename):
    node = parse(filename)
    for n in node.childNodes:
        if n.nodeType != n.ELEMENT_NODE:
            continue
        if n.nodeName == "apns":
            node2 = n
            break

    for n in node2.childNodes:
        if n.nodeType != n.ELEMENT_NODE:
            continue
        if n.nodeName == "apn":
            as1 = n.attributes
            as2 = {}
            for one in as1.items():
                as2[one[0].strip()] = one[1].encode("utf-8").strip()
            if as2.has_key("mcc") and as2.has_key("mnc") and as2.has_key("carrier"):
                as2["mnc"] = as2["mnc"].split(",")
                apnlist2.append(as2)

def optApnList():
    i = 0
    while i < len(apnlist2):
        map1 = apnlist2[i].copy()
        j = i + 1
        while j < len(apnlist2):
            if apnMatch(i,j):
                map1["mnc"] += apnlist2[j]["mnc"]
                apnlist2.pop(j)
            else:
                j += 1
        list1 = list(set(map1["mnc"]))
        list1.sort(myComparator2)
        map1["mnc"]=list1
        apnlist3.append(map1)
        i += 1

def outputApn(NEW_APN_PATH):
    F=open(NEW_APN_PATH,"w")
    i = 0
    while not "apns" in apnlist[i]:
        F.write(apnlist[i])
        i += 1
    F.write(apnlist[i])
    F.write("\n")

    unknownfields = set()

    for one in apnlist3:
        if one.has_key("carrier"):
            if ("&" in one["carrier"].strip()):
                F.write("  <apn carrier=\""+ one["carrier"].strip().replace("&","&amp;") +"\"\n")
            else:
                F.write("  <apn carrier=\""+ one["carrier"].strip() +"\"\n")
        else:
            continue

        for onefield in APNFILES:
            if onefield == "mnc":
                list1 = one[onefield]
                mncs2 = str(list1[0])
                for two in list1[1:]:
                    mncs2 = mncs2 + "," + str(two)
                F.write(" "*6 + onefield + "=\"" + mncs2 + "\"\n")
            elif one.has_key(onefield):
                if ("&" in one[onefield]):
                    F.write(" "*6 + onefield + "=\"" + one[onefield].strip().replace("&","&amp;") + "\"\n")
                else:
                    F.write(" "*6 + onefield + "=\"" + one[onefield] + "\"\n")
        F.write("  />\n\n")
        keys1 = one.keys()
        for three in keys1:
            if (not three in APNFILES) and (not three == "carrier"):
                unknownfields.add(three)

    F.write(apnlist[-1])
    F.close()

    if len(unknownfields) > 0:
        print "Warning!!! Unknown fileld: "
        print unknownfields

def mergerapn(NEW_APN_PATH):
    for line in open(NEW_APN_PATH):
        apnlist.append(line)

    genApnList(NEW_APN_PATH)
    optApnList()
    outputApn(NEW_APN_PATH)

def update_spn_from_db(project_info):
    if project_info["age"] <  PROJECT_INFO["mt6571jb7"]["age"]:
        return

    cmd1 = "cd mediatek/frameworks;git status base/telephony/etc/spn-conf.xml"
    out1 = commands.getstatusoutput(cmd1)[1].strip()
    if "modified" in out1:
        return
    mydefaultapndb = "../../database/myspn.xml"
    if not os.path.exists(mydefaultapndb):
        return
    my_sys("cp -f %s mediatek/frameworks/base/telephony/etc/spn-conf.xml" % mydefaultapndb)

def update_apns_from_db(project_info):
    if project_info["age"] <  PROJECT_INFO["mt6571jb7"]["age"]:
        return
    cmd1 = "cd mediatek/frameworks;git status base/telephony/etc/apns-conf.xml"
    out1 = commands.getstatusoutput(cmd1)[1].strip()
    if "modified" in out1:
        return
    #TODO, need modify

    mydefaultapndb = "../../database/mydefaultapn.db"
    if not os.path.exists(mydefaultapndb):
        return
    defaultDbcon = sqlite3.connect(mydefaultapndb)
    defaultDbcur = defaultDbcon.cursor()

    if project_info["android"] in ("45", "44"):
        outF = open("apns-conf.xml","w")
        outF.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        outF.write("<apns version=\"8\">\n\n")
    elif project_info["android"] == "42":
        outF = open("apns-conf.xml","w")
        outF.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        outF.write("<apns version=\"7\">\n\n")
    else:
        print "\nWrong version!!!\n"

    defaultDbcur.execute('SELECT * FROM apns ORDER BY mcc,mnc')
    for one in defaultDbcur.fetchall():
        apn_carrier = one[1].encode("utf-8").strip()
        apn_mcc = one[2].encode("utf-8").strip()
        apn_mnc = one[3].encode("utf-8").strip()
        apn_apn = one[4].encode("utf-8").strip()
        apn_mmsc = one[5].encode("utf-8").strip()
        apn_mmsproxy = one[6].encode("utf-8").strip()
        apn_mmsport = one[7].encode("utf-8").strip()
        apn_type = one[8].encode("utf-8").strip()
        apn_user = one[9].encode("utf-8").strip()
        apn_password = one[10].encode("utf-8").strip()
        apn_proxy= one[11].encode("utf-8").strip()
        apn_port = one[12].encode("utf-8").strip()
        apn_authtype = one[13].encode("utf-8").strip()
        apn_spn = one[14].encode("utf-8").strip()
        apn_server = one[15].encode("utf-8").strip()
        apn_protocol = one[16].encode("utf-8").strip()
        apn_roaming_protocol = one[17].encode("utf-8").strip()
        if apn_carrier != "":
            if "&" in apn_carrier:
                apn_carrier = apn_carrier.replace("&","&amp;")
            outF.write("  <apn carrier=\""+ apn_carrier +"\"\n")
        else:
            outF.write("  <apn\n")
        if apn_mcc != "":
            outF.write("\t  mcc=\""+ apn_mcc +"\"\n")
        if apn_mnc != "":
            outF.write("\t  mnc=\""+ apn_mnc +"\"\n")
        if apn_apn != "":
            if "&" in apn_apn:
                apn_apn = apn_apn.replace("&","&amp;")
            outF.write("\t  apn=\""+ apn_apn +"\"\n")
        if apn_mmsc != "":
            outF.write("\t  mmsc=\""+ apn_mmsc +"\"\n")
        if apn_mmsproxy != "":
            outF.write("\t  mmsproxy=\""+ apn_mmsproxy +"\"\n")
        if apn_mmsport != "":
            outF.write("\t  mmsport=\""+ apn_mmsport +"\"\n")
        if apn_type != "":
            outF.write("\t  type=\""+ apn_type +"\"\n")
        if apn_user != "":
            outF.write("\t  user=\""+ apn_user +"\"\n")
        if apn_password != "":
            outF.write("\t  password=\""+ apn_password +"\"\n")
        if apn_proxy != "":
            outF.write("\t  proxy=\""+ apn_proxy +"\"\n")
        if apn_port != "":
            outF.write("\t  port=\""+ apn_port +"\"\n")
        if apn_authtype != "":
            outF.write("\t  authtype=\""+ apn_authtype +"\"\n")
        if apn_spn != "":
            outF.write("\t  spn=\""+ apn_spn +"\"\n")
        if apn_server != "":
            outF.write("\t  server=\""+ apn_server +"\"\n")
        if apn_protocol != "":
            outF.write("\t  protocol=\""+ apn_protocol +"\"\n")
        if apn_roaming_protocol != "":
            outF.write("\t  roaming_protocol=\""+ apn_roaming_protocol +"\"\n")
        outF.write("  />\n\n")

    outF.write("</apns>")
    outF.close()
    mergerapn("./apns-conf.xml")
    my_sys("mv -f apns-conf.xml mediatek/frameworks/base/telephony/etc/apns-conf.xml")

def gen_so_from_apk(project):
    apk_list = []
    file1 = "vendor/google/3rdapp/Android.mk"
    if os.path.exists(file1):
        with open(file1) as in_file:
            for line in in_file:
                if ".apk" in line and not "/" in line:
                    apk = line.replace("\\","").strip()
                    apk_list.append("vendor/google/3rdapp/%s" % apk)

    apk_list.extend(glob.glob("vendor/google/3rdapp/custom/*.apk"))
    apk_list.extend(glob.glob("vendor/google/*.apk"))
    [_gen_so_from_apk(project, apk) for apk in apk_list]

def _gen_so_from_apk(project, apk):
    tmpdir = tempfile.mkdtemp(dir='/tmp')
    destdir = 'vendor/mediatek/{0}/artifacts/out/target/product/{0}/system/lib'.format(project)
    my_sys('unzip {0} -d {1} >/dev/null'.format(apk, tmpdir))
    so_list = []
    basename_list=[]
    if project in ('vanzo13_6626_gb', 'vanzo73_gb'):
        so_list = glob.glob('{0}/lib/armeabi/*.so'.format(tmpdir))
    else:
        so_list = glob.glob('{0}/lib/armeabi-v7a/*.so'.format(tmpdir))
        so_list.extend(glob.glob('{0}/lib/armeabi/*.so'.format(tmpdir)))
    for so in so_list:
        basename=os.path.basename(so)
        if basename not in basename_list:
            basename_list.append(basename)
        else:
            continue
        dest_so = os.path.join(destdir, os.path.basename(so))
        if not os.path.exists(dest_so):
            shutil.copy(so, dest_so)
        else:
            if not is_same_file(so,dest_so):
                print "Warning!%s lib: %s already exists,this maybe a error!"%(apk,dest_so)
                #sys.exit(-1)
    shutil.rmtree(tmpdir, True)

def get_git_user():
    return commands.getstatusoutput("git config --get user.name")[1].strip()

def ensure_recommend_apks_repo():
    if not os.path.exists("recommend_apks"):
        my_sys("git clone vanzo:tools/recommend_apks.git")
    else:
        my_sys("cd recommend_apks;git clean -fd;git checkout . > /dev/null; git pull > /dev/null")

def get_current_apks(project_name=None):
    ensure_recommend_apks_repo()
    if project_name is None or not _is_ophone(project_name):
        file1 = "./recommend_apks/current.txt"
    else:
        file1 = "./recommend_apks/ophone_current.txt"
    list1 = []
    if os.path.exists(file1):
        with open(file1) as in_file:
            for one in in_file:
                list1.append(one.strip())
    return list1

def is_core_apks(one):
    list1 = glob.glob("./recommend_apks/apks/%s_*" % one)
    if "_optional_" in list1[0]:
        return False
    return True

def load_policies(project_name):

    #change_time1 = _get_change_time(".repo/manifests/%s.xml" % project_name)
    if os.path.exists(".repo/manifests/%s.xml" % project_name):
        change_time1 = _get_change_time(".repo/manifests/%s.xml" % project_name)
    else:
        custom_file = project_custom_config_fallback(project_name)
        if not custom_file:
            print "Error:can not get the custom file"
            return []
        change_time1 = _get_change_time(custom_file)

    list1 = glob.glob("recommend_apks/ophone_phistory*.txt" if _is_ophone(project_name) else "recommend_apks/phistory*.txt")
    list_files  = []
    for one in list1:
        list2 = one.split("-")
        time1 = datetime.datetime(int(list2[1]), int(list2[2]), int(list2[3]), int(list2[4]), int(list2[5]), int(list2[6]))
        list_files.append([time1, one])
    list_files.sort(lambda one,two: cmp(one[0], two[0]))
    file1 = "./recommend_apks/ophone_policy.txt" if _is_ophone(project_name) else "./recommend_apks/policy.txt"
    for one in list_files:
        if change_time1 < one[0]:
            file1 = one[1]
            break

    map1 = {}
    with open(file1) as in_file:
        for line in in_file:
            pos1 = line.find(":")
            key1 = npn(line[:pos1])
            map2 = eval(line[pos1+1:].strip())
            map1[key1] = map2
    return map1

def add_policy(map1, key1, map_old):
    if not map1.has_key(key1):
        return
    assert map1.has_key(key1)
    map_new =  map1[key1]
    for one in map_new:
        if map_old.has_key(one):
            if map_new[one] != 0:
                map_old[one] = map_new[one]
        else:
            map_old[one] = map_new[one]

def _do_get_fallback_project2(map1, one):
    list1 = [one]
    while len(list1) > 0:
        two = list1.pop(0)
        for onerule in fallback_rules_keys:
            if _does_fallback_rule_match(onerule, two):
                three = two.replace(onerule, fallback_rules_maps[onerule])
                if map1.has_key(three):
                    return three
                else:
                    list1.append(three)
    return None

def _do_get_fallback_project(map1, project1):
    if not os.path.exists(".repo"):
        _project_custom_ensure_overlay_and_patchset_repos(project1)
    project1 = npn(project1)
    if len(fallback_rules_keys) <= fallback_rules_len:
        assert os.path.exists("%s/fallback_extra.txt" % gCustomRootRO)
        project_custom_build_fallback_list("%s/fallback_extra.txt" % gCustomRootRO)
    if map1.has_key(project1):
        return project1
    project2 = _do_get_fallback_project2(map1, project1)
    return project2

def project_custom_config_fallback(project_name):
    project_info = get_project_info(project_name)
    cust1 = "%s/mediatek/config/%s/ProjectConfig.mk.bsp.overlay.%s" % (gOverlayRootRO, project_info["project"], npn(project_name))
    if project_info["age"] >=  PROJECT_INFO["mt6572jb3"]["age"]:
        cust1 = cust1.replace(".bsp", ".custom")
    return project_custom_get_fallback(cust1)

def project_bsp_config_fallback(project_name):
    project_info = get_project_info(project_name)
    bsp = "%s/mediatek/config/%s/ProjectConfig.mk.bsp.overlay.%s" % (gOverlayRootRO, project_info["project"], npn(project_name))
    return project_custom_get_fallback(bsp)

def _load_apks():
    project_name = get_project_name()

    wvga = True
    d1 = get_dimension_from_project_config(project_custom_config_fallback(project_name))
    if d1 != None and d1[0] * d1[1] < 800 * 480:
        wvga = False

    if os.path.exists(".repo/manifests/%s.xml" % project_name):
        change_time1 = _get_change_time(".repo/manifests/%s.xml" % project_name)
    else:
        custom_file = project_custom_config_fallback(project_name)
        if not custom_file:
            print "Error:can not get the custom file"
            return []
        change_time1 = _get_change_time(custom_file)

    list1 = glob.glob("recommend_apks/history*.txt")
    list_files  = []
    for one in list1:
        list2 = one.split("-")
        time1 = datetime.datetime(int(list2[1]), int(list2[2]), int(list2[3]), int(list2[4]), int(list2[5]), int(list2[6]))
        list_files.append([time1, one])
    list_files.sort(lambda one,two: cmp(one[0], two[0]))
    file1 = "recommend_apks/ophone_current.txt" if _is_ophone(project_name) else "recommend_apks/current.txt"
    for one in list_files:
        if change_time1 < one[0]:
            file1 = one[1]
            break

    list1 = []
    with open(file1) as in_file:
        for line in in_file:
            if _is_aephone(project_name) and "aphone" not in line:
                continue
            elif "aphone" in line:
                continue

            if "wvga" in line and not wvga:
                continue
            elif "hvga" in line and wvga:
                continue

            list1.append(line.strip())

    list2 = []
    for one in list1:
        list3 = glob.glob("recommend_apks/apks/%s*" % one)
        list3.sort()
        list2.append(list3[-1])

    return list2

def _filter_apks_by_conflict(list1, list2):
    list3 = []
    for one in list1:
        for two in list2:
            three = "neiz_%s" % two
            if three in one:
                my_dbg(_red("ignore apk:%s" % one))
                break
        else:
            list3.append(one)
    return list3

def _filter_apks_by_accept(list1, map1):
    accept1 = map1["Accept"]
    if accept1 == 0:
        return list1
    elif accept1 == 1:
        list2 = []
        for one in list1:
            if "_core" in one:
                list2.append(one)
        return list2
    elif accept1 == 2:
        list_select = my_split(map1["selected_apks"])
        list2 = []
        list3 = []
        for one in list1:
            for two in list_select:
                if two in one:
                    list2.append(one)
                    list3.append(two)
                    break
        for one in list_select:
            if not one in list3:
                list4 = glob.glob("recommend_apks/apks/%s*" % one)
                list4.sort()
                list2.append(list4[-1])
        return list2
    elif accept1 == 4:
        list2 = []
        return list2

    elif accept1 == 3:
        list_select = my_split(map1["selected_apks"])
        list2 = []
        for one in list1:
            for two in list_select:
                if one.find(two) >= 0:
                    break
            else:
                list2.append(one)
        return list2
    else:
        print "not supported yet"
        assert False

def _get_by_placement(list2, place1):
    list_system = []
    list_userdata = []
    for one in list2:
        if "_system" in one:
            list_system.append(one)
        elif "_userdata" in one:
            list_userdata.append(one)
        elif place1 == 0:
            #by default, install on userdata
            list_userdata.append(one)
        elif place1 == 1:
            list_system.append(one)
        elif place1 == 2:
            list_userdata.append(one)
        elif place1 == 3:
            if "_core" in one:
                list_system.append(one)
            else:
                list_userdata.append(one)
        else:
            assert False
    return (list_system, list_userdata)

def apply_policy(map2, project_name, project_info):
    dir1 = "vendor/google/3rdapp/custom"
    if not os.path.exists(dir1):
        os.makedirs(dir1)

    dir2 = "vendor/google/userdata/custom"
    if not os.path.exists(dir2):
        os.makedirs(dir2)

    list1 = glob.glob("%s/*.apk" % dir1)
    list1.extend(glob.glob("%s/*.apk" % dir2))
    list_current_apks = []
    for one in list1:
        list_current_apks.append(os.path.basename(one).replace(".apk",""))

    def rm_apks_4440(dir4440):
        if os.path.exists("%s/Android.mk" % dir4440):
            my_sys("mv -f %s/Android.mk %s/Android.mk_" % (dir4440, dir4440))
    def is_mul_apks(one4400):
        mul_apks = ("com.opera.branding", "com.baidu.browser.inter", "im.ecloud.ecalendar")
        for two4400 in mul_apks:
            if two4400 in one4400:
                return True
        return False
    if map2["Freeze"] != 1:
        list1 = _load_apks()
        #list1 = _filter_apks_by_conflict(list1, list_current_apks)
        list1 = _filter_apks_by_accept(list1, map2)
        if list1 == None:
            return
        (list3, list4) = _get_by_placement(list1, map2["Placement"])
        my_sys("echo system: >> r1.txt")
        for one in list3:
            if _is_mul(project_name) and not is_mul_apks(one):
                continue
            if not _is_mul(project_name) and is_mul_apks(one):
                continue
            if "com.android.browser" in one or "com.baidu.browser.inter" in one:
                if not ge_kk(project_name): continue
                if "com.baidu.browser.inter" in one:
                    ret = my_sys("cd packages/apps/Browser/; git status | grep modified")
                    if ret == 0:
                        continue
                rm_apks_4440("packages/apps/Browser")
            elif "com.v5music" in one:
                if not ge_kk(project_name): continue
                if _is_tphone(project_name) and  os.path.exists("packages/apps/MusicTphone"):
                    ret = my_sys("cd packages/apps/MusicTphone/; git status | grep modified")
                    if ret == 0: continue
                    rm_apks_4440("packages/apps/MusicTphone")
                else:
                    ret = my_sys("cd packages/apps/Music/; git status | grep modified")
                    if ret == 0:
                        continue
                    rm_apks_4440("packages/apps/Music")
                rm_apks_4440("packages/apps/MusicFX")
            elif "cn.etouch.ecalendarTIATPA" in one or "im.ecloud.ecalendar" in one:
                if not ge_kk(project_name): continue
                if os.path.exists("vendor/google/apps/CalendarGoogle.apk"):continue
                ret = my_sys("cd packages/apps/Calendar/; git status | grep modified")
                if ret == 0:
                    continue
                rm_apks_4440("packages/apps/Calendar")
            elif "com.kanbox.filemanager" in one:
                ret = my_sys("cd mediatek/packages/apps/FileManager/; git status | grep modified")
                if ret == 0:
                    continue
                rm_apks_4440("mediatek/packages/apps/FileManager")

            my_sys("echo %s >> r1.txt" % one)
            my_sys("cp -f %s %s" % (one, dir1))

        my_sys("echo userdata: >> r1.txt")
        for one in list4:
            if _is_mul(project_name) and not is_mul_apks(one):
                continue
            if not _is_mul(project_name) and is_mul_apks(one):
                continue
            my_sys("echo %s >> r1.txt" % one)
            my_sys("cp -f %s %s" % (one, dir2))


def do_add_aphone_apks(project_name):
    if not "_ephone" in project_name and not "_aphone" in project_name:
        return
    list_ephone_apks = glob.glob("recommend_apks/aphone/*.apk")
    dir1 = "vendor/google/3rdapp/custom"
    dir2 = "vendor/google/userdata/custom"
    list_current_apks = glob.glob("%s/*.apk" % dir1)
    list_current_apks.extend(glob.glob("%s/*.apk" % dir2))
    for one in list_ephone_apks:
        two = os.path.basename(one)[:-4]
        for three in list_current_apks:
            four = os.path.basename(one).replace("neiz_", "")
            if four.startswith(two):
                break
        else:
            my_sys("cp -f %s %s" % (one, dir1))


#added by wf for get the current project recommented apks
def do_get_recommented_apks(project_name):
    project_info = get_project_info(project_name)
    def _ensure_recommend_apks_repo():
        if not os.path.exists("../../recommend_apks"):
            my_sys("cd ../..;git clone vanzo:tools/recommend_apks.git")
        else:
            my_sys("cd ../../recommend_apks;git clean -fd;git checkout . > /dev/null; git pull > /dev/null")
        my_sys("ln -sf ../../recommend_apks .")
    _ensure_recommend_apks_repo()
    if _is_cta(project_name):
        return []
    if _is_ali(project_name):
        return []
    if "mt15cmcc" in project_name:
        return []
    if "_twog" in project_name:
        return []
# Vanzo:yucheng on: Mon, 19 May 2014 23:33:54 +0800
# Delete 3rd-party Apps for CMCC projects
    if "cmcc_" in project_name:
        return []
# End of Vanzo: yucheng
    '''
    if not os.path.exists("vendor/google"):
        print "Error,no directory vendor/google"
        return []
    '''
    if project_info["age"] < PROJECT_INFO["mt6517td"]["age"]:
        return
    if "_mul" in project_name:
        #strange why foreign do put apks
        return []
    map1 = load_policies(project_name)
    list1 = project_name.split("_")
    map2 = {}
    #default policy
    add_policy(map1, "default", map2)
    #big platform policy
    add_policy(map1, list1[0], map2)
    #small platform policy
    add_policy(map1, "%s_%s" % (list1[0], list1[1]), map2)
    #UI policy
    if _is_aephone(project_name):
        add_policy(map1, "aphone", map2)
    elif _is_vphone(project_name):
        add_policy(map1, "vphone", map2)
    #customer policy
    add_policy(map1, list1[3], map2)
    #project policy
    project1 = _do_get_fallback_project(map1, project_name)
    if project1 and not _is_ophone(project1):
        add_policy(map1, project1, map2)

    '''
    dir_3rdapp = "vendor/google/3rdapp/custom"
    dir_userapp = "vendor/google/userdata/custom"
    list1=[]
    list_current_apks = []
    if os.path.exists(dir_3rdapp):
        list1 = glob.glob("%s/*.apk" % dir_3rdapp)
    if os.path.exists(dir_userapp):
        list1.extend(glob.glob("%s/*.apk" % dir_userapp))
    for one in list1:
        list_current_apks.append(os.path.basename(one).replace(".apk",""))
    '''

    results_list=[]
    if map2["Freeze"] != 1:
        list1 = _load_apks()
        print "list1:",list1
        list1 = _filter_apks_by_accept(list1, map2)
        print "after _filter_apks_by_accept:",list1
        if list1 == None:
            return []
        (list3, list4) = _get_by_placement(list1, map2["Placement"])
        print "list3:",list3
        print "list4:",list4
        list3.extend(list4)
        results_list=list3

    return results_list

def do_copy_vanzo_team_base(project_name):
    project_info = get_project_info(project_name)
    if not ge_kk(project_name) or _is_ali(project_name):
        return
    if os.path.exists("vanzo_custom_base"):
        my_sys("cd vanzo_custom_base;git clean -fd; git checkout . > /dev/null;git pull > /dev/null")
    else:
        my_sys("git clone vanzo:tools/vanzo_custom_base")
    my_sys("cp -af vanzo_custom_base/* vendor/vanzo_custom/")
    my_sys("cd vendor/vanzo_custom;git st > gitignore")

    if not os.path.exists("./vendor/vanzo_custom/.gitignore"):
        with open("./vendor/vanzo_custom/gitignore") as inF:
            with open("./vendor/vanzo_custom/.gitignore", "w+") as outF:
                outF.write(".gitignore\n")
                begin = False
                for one in inF:
                    if begin and not "gitignore" in one:
                        if not "#" in one:
                           break
                        two = one.replace("#", "").strip()
                        if len(two) > 0:
                            outF.write("%s\n" % two)
                    else:
                        if "include in what will be committed" in one:
                            begin = True
    my_sys("rm -f ./vendor/vanzo_custom/gitignore")

def do_add_recommended_apks(project_name):
    project_info = get_project_info(project_name)

    def _ensure_recommend_apks_repo_4647():
        if not os.path.exists("../../recommend_apks"):
            my_sys("cd ../..;git clone vanzo:tools/recommend_apks.git")
        else:
            my_sys("cd ../../recommend_apks;git clean -fd;git checkout . > /dev/null; git pull > /dev/null")
        my_sys("ln -sf ../../recommend_apks .")
    _ensure_recommend_apks_repo_4647()

    #add security module
    #if project_info["id"] in ("mt6589jb2", "mt6589jb2cta", "mt6572jb3", "mt6572jb3nand", "mt6582jb5", ) and not _is_mul(project_name):
#    if project_info["id"] in ("mt6589jb2cta", ):
#        dir0 = "security"
#        if "cta" in project_info["id"]:
#            dir0 = "security_cta"
#
#        dir1 = "vendor/google/3rdapp/custom"
#        cmd1 = "mkdir -p %s" % dir1
#        my_sys(cmd1)
#
#        if "cta" in project_info["id"]:
#            cmd1 = "cp -a ./recommend_apks/%s/safe.apk vendor/mediatek/%s/artifacts/out/target/product/%s/system/app" % (dir0, project_info["project"], project_info["project"])
#        else:
#            cmd1 = "cp -a ./recommend_apks/%s/safe.apk %s/" % (dir0, dir1)
#        my_sys(cmd1)
#
#        cmd1 = "cp -a ./recommend_apks/%s/nac_server vendor/mediatek/%s/artifacts/out/target/product/%s/system/bin" % (dir0, project_info["project"], project_info["project"])
#        my_sys(cmd1)
#
#        cmd1 = "echo '# nac_server loader begin\n service nac_server /system/bin/nac_server\n class main\n user root\n # nac_server loader end' >> mediatek/config/%s/init.rc" % project_info["id"][:6]
#        my_sys(cmd1)
#
    if _is_cta(project_name):
        return

    if "_cphone" in project_name:
        return

    if _is_ali(project_name):
        return

    if "_twog" in project_name:
        return

    if "cmcc_" in project_name:
        return

    if not os.path.exists("vendor/google"):
        return

    if _is_vphone(project_name):
        my_sys("rm -rf vendor/google/app")
        my_sys("rm -rf vendor/google/lib")
        my_sys("rm -rf vendor/google/face*")
    elif project_info["age"] < PROJECT_INFO["mt6517td"]["age"]:
        return

    map1 = load_policies(project_name)
    list1 = project_name.split("_")
    map2 = {}

    #default policy
    add_policy(map1, "default", map2)

    #big platform policy
    add_policy(map1, list1[0], map2)

    #small platform policy
    add_policy(map1, "%s_%s" % (list1[0], list1[1]), map2)

    #UI policy
    if _is_aephone(project_name):
        add_policy(map1, "aphone", map2)
    elif _is_vphone(project_name):
        add_policy(map1, "vphone", map2)
    #customer policy
    add_policy(map1, list1[3], map2)

    #project policy
    project1 = _do_get_fallback_project(map1, project_name)
    if project1 and not _is_ophone(project1):
        add_policy(map1, project1, map2)

    apply_policy(map2, project_name, project_info)
    #do_add_aphone_apks(project_name)

#whether two fallback to one
def is_relative(target, one):
    if one == target:
        return True
    list1 = [one]
    while len(list1) > 0:
        two = list1.pop(0)
        for onerule in fallback_rules_keys:
            if _does_fallback_rule_match(onerule, two):
                three = two.replace(onerule, fallback_rules_maps[onerule])
                if three == target:
                    return True
                else:
                    list1.append(three)
    return False

def get_project_class_list(file1):
    def _get_normalized_apk2(two, list1):
        project_info2 = get_project_info(two)
        if project_info2 == None:
            return True
        for one in list1:
            project_info1 = get_project_info(one)
            if project_info2 != project_info1:
                continue

            hit = False
            for three in ("_aphone", "_ephone", "_sphone", "_vphone", "_tphone", "_ophone", "_cphone"):
                if three in two:
                    hit = True
                    if three in one:
                        return True
            if not hit:
                return True
        return False

    list1 = []
    with open(file1) as in_file:
        for line in in_file:
            two = line.strip()
            list1.append(two)
    list1.reverse()

    list2 = []
    for one in list1:
        if not _get_normalized_apk2(one, list2):
            list2.append(one)
    return list2

def do_check_all_patchsets():
    global gPatchsetRootRO # pylint: disable=W0603
    gPatchsetRootRO = "vendor/vanzo_custom/patch_projects"
    project_name = get_project_name()
    cmd = """find %s -type f  | grep '%s' | sort | uniq""" % (gPatchsetRootRO, PATCHSET_KEY)
    uniq_patchsets = commands.getstatusoutput(cmd)[1].split()
    for one in uniq_patchsets:
        two = os.path.dirname(one)
        dir1 = two[len(gPatchsetRootRO)+1:]

        if not os.path.exists(dir1):
            continue

        if ".delete" in os.path.basename(one):
            continue

        if ".keep" in os.path.basename(one):
            continue

        hit = False
        for three in ("_aphone", "_ephone", "_sphone", "_vphone", "_tphone", "_ophone", "_cphone"):
            if three in os.path.basename(one) and not three in project_name:
                hit = True
        if hit:
            continue

        cmd = "cd %s; patch -p1 < %s" % (dir1, os.path.abspath(one))
        if commands.getstatusoutput(cmd)[0]:
            print one
        cmd = "cd %s; git clean -fd;git checkout . > /dev/null" % dir1
        my_sys(cmd)

def _get_normalized_apk(one, name1, project_info):
    str1 = "apks"
    if project_info["age"] >=  PROJECT_INFO["mt6592jb9"]["age"]:
        str1 = "apks92"
    list1 = glob.glob("../../%s/%s*.apk" % (str1, name1))
    if len(list1) == 0:
        return
    for two in list1:
        cmd1 = "cmp %s %s" % (one, two)
        if commands.getstatusoutput(cmd1)[0] == 0:
            return two
    return

def _normalize_one_apk(one, name1, project_info):
    str1 = "apks"
    if project_info["age"] >=  PROJECT_INFO["mt6592jb9"]["age"]:
        str1 = "apks92"
    for i in range(1000):
        name2 = "../../%s/%s_%.3d.apk" % (str1, name1, i)
        if os.path.exists(name2):
            continue

        my_sys("cp -f %s %s" % (one, name2))
        return name2

def _get_package_name_from_apk(apk):
    stdout = subprocess.Popen(['aapt', 'd', 'badging', apk], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    try:
        return "%s" % stdout.splitlines()[0].split()[1].split("=")[1].replace("'","")
    except: # pylint: disable=W0702
        my_dbg(_yellow('abnormal apk: ' + apk))

"""run above vanzo_custom"""
def do_normalize_apks(project_info):
    def _ensure_apks_repo_4470():
        str1 = "apks"
        if project_info["age"] >=  PROJECT_INFO["mt6592jb9"]["age"]:
            str1 = "apks92"

        if not os.path.exists("../../%s" % str1):
            my_sys("cd ../..;git clone vanzo:tools/%s.git" % str1)
        else:
            my_sys("cd ../../%s;git clean -fd;git checkout . > /dev/null; git pull > /dev/null" % str1)

    _ensure_apks_repo_4470()
    commands.getstatusoutput("rm -rf vanzo_custom; ln -s rw/%s/vanzo_custom ."%get_project_info(get_project_name())['repo'])
    list1 = commands.getstatusoutput("find vanzo_custom/* -type f -name *.apk | grep google|grep -E '3rdapp|userdata'")[1].split("\n")
    list1.extend(commands.getstatusoutput("find vanzo_custom/* -type f -name *.apk.* | grep google|grep -E '3rdapp|userdata'")[1].split("\n"))
    len1 = len(list1)
    print "List1:",list1
    for i, one in enumerate(list1):
        if len(one.strip()) == 0:
            continue
        print "%d/%d" % (i, len1)
        name1 = _get_package_name_from_apk(one)
        two = _get_normalized_apk(one, name1, project_info)
        if not two:
            two = _normalize_one_apk(one, name1, project_info)
        c1 = one.count("/") - 1
        str1 = "../" * c1
        two = two.replace("apks92", "apks")
        cmd1 = "ln -sf %s%s %s" % (str1, two, one)
        my_sys(cmd1)


def do_normalize_fallback(file1):
    file2 = "%s.tmp" % file1
    with open(file1) as in_file:
        with open(file2, "w+") as out_file:
            for line in in_file:
                list1 = line.split(":")
                if len(list1) == 2:
                    line = "%s:%s\n" % (npn(list1[0].strip()), npn(list1[1].strip()))
                out_file.write(line)
    my_sys("mv -f %s %s" % (file2, file1))

def do_normalize_buildinfo_custom(file1):
    map1 = {}
    with open(file1) as myfile:
        for line in myfile:
            if '#' in line:
                line2 = line[:line.find('#')]
            else:
                line2 = line
            a = line2.strip().split(":")
            if len(a) >= 5:
                map1[a[0].strip()] = a[1:]
    map2 = {}
    for one in map1:
        map2[npn(one)] = map1[one]
    map1 = map2

    list1 = map1.keys()
    list2 = []
    for one in list1:
        for two in list1:
            if one == two:
                continue
            if is_relative(one, two):
                if map1[one] == map1[two]:
                    if not two in list2:
                        list2.append(two)
    for one in list2:
        map1.pop(one)

    file2 = "%s.tmp" % file1
    list2 = map1.keys()
    list2.sort()
    with open(file2, "w+") as out_file:
        for one in list2:
            list3 = map1[one]
            out_file.write("%s:%s:%s:%s:%s\n" % (one, list3[0], list3[1], list3[2], list3[3]))
    my_sys("mv -f %s %s" % (file2, file1))

_only_local_apk_list = (
    "cn.kuwo.player.apk",
    "cn.msn.messenger.apk",
    "com.UCMobile.apk",
    "com.aedesign.deskclock.apk", #时钟
    "com.android.yes2metodolist.apk",#提醒事项
    "com.chaozh.iReaderFree15.apk",
    "com.cooguo.memo.apk",#备忘录
    "com.dayingjia.stock.activity.apk",
    "com.flyfish.gs.ui.apk",
    "com.fone.player.apk",
    "com.hiapk.marketpho.apk",
    "com.hskj.iphoneweather.apk",
    "com.sina.weibo.apk",
    "com.sohu.inputmethod.sogou.apk",
    "com.sohu.newsclient.apk",
    "com.tencent.mobileqq.apk",
    "com.zzcm.yyassistant.client.home.apk",
    "neiz_AndroidMarket.apk",
    "neiz_BaiduSearch.apk",
    "neiz_ChannelInfom.apk",
    "neiz_Sogou.apk",
    "neiz_UCBrowser.apk",
    "neiz_UCBrowser_s.apk",
    "neiz_appchina.apk",
    "neiz_baidumapv.apk",
    "neiz_baidumusicv.apk",
    "neiz_iReader.apk",
    "neiz_qqguanjia.apk",
    "neiz_sanguoage_joyfan_c.apk",
    "neiz_sinawebo.apk",
    "neiz_yyzl.apk",
    "com.baidu.input.apk",
    "com.tencent.qqpimsecure.apk",
    "com.tencent.mtt.apk",
)

def _remove_one_apk(one):
    two = os.path.dirname(one) + "/Android.mk"
    if os.path.exists(two):
        cmd1 = "sed -i '/%s/d' %s" % (os.path.basename(one), two)
        my_sys(cmd1)
    else:
        cmd1 = "rm -f %s" % one
        my_sys(cmd1)

def _remove_some_apks_for_mul2(onedir):
    list2 = glob.glob("%s/*.apk" % onedir)
    for one in list2:
        two = os.path.basename(one)
        if two in _only_local_apk_list:
            _remove_one_apk(one)
        else:
            my_dbg(two)

def remove_some_apks_for_mul(project_name):
    if not "_mul" in project_name:
        return

    if "mt82_a9cl_x5_ousheng_jb5_sw_wcdma_mul" in project_name:
        return
    if "mt92_s9_x8_ousheng_wcdma_jb9_sw_mul" in project_name:
        return
    if "mt92_s9_x5s_ousheng_wcdma_jb9_sw_mul" in project_name:
        return
    if "mt82_a25_xtremeu7_sbyh_kk_wcdma_mul" in project_name:
        return
    if "mt82_a6cl_bliss5_gfiveydl_jb5_wcdma_mul" in project_name:
        return
    if "mt82_a25_l518_qiwen2_cc_kk_wcdma_mul" in project_name:
        return
    if "mt82_a25_a6_qiwen2_cc_kk_wcdma_mul" in project_name:
        return

    list1 = ("vendor/google/3rdapp","vendor/google/userdata")
    for onedir in list1:
        _remove_some_apks_for_mul2(onedir)
        _remove_some_apks_for_mul2(onedir + "/custom")

def gen_so_list_from_apk(apk):
    tmpdir = tempfile.mkdtemp(dir='/tmp')
    my_sys('unzip {0} -d {1} >/dev/null'.format(apk, tmpdir))
    so_list = glob.glob('{0}/lib/armeabi-v7a/*.so'.format(tmpdir))
    so_list.extend(glob.glob('{0}/lib/armeabi/*.so'.format(tmpdir)))
    shutil.rmtree(tmpdir, True)
    return so_list

def remove_redudant_google_libs():
    if not os.path.exists("vendor/google/app/Android.mk"):
        return
    list_app = get_keyed_list_from_file("vendor/google/app/Android.mk","copy_from")
    if len(list_app) == 0:
        for one in ("etc", "face", "framework", "lib", "tts", "usr"):
            my_sys("mv -f vendor/google/%s/Android.mk vendor/google/%s/Android.mk_" % (one, one))
        return

    list_app2 = glob.glob("vendor/google/app/*.apk")
    list_app3 = [os.path.basename(one) for one in list_app2]
    list_app4 = list(set(list_app3) - set(list_app))
    list_so = []
    for one in list_app4:
        two = "vendor/google/app/%s" % one
        list_so.extend(gen_so_list_from_apk(two))
    list_so2 = ["vendor/google/lib/%s" % os.path.basename(one) for one in list_so]

    def has5095(str1):
        cmd1 = "grep -i %s vendor/google/app/Android.mk" % str1
        return commands.getstatusoutput(cmd1)[0] == 0
    if not has5095("facelock"):
        list1 = glob.glob("vendor/google/lib/*face*.so")
        for one in list1:
            if not one in list_so2:
                list_so2.append(one)
        my_sys("rm -rf vendor/google/face*")

    hit5108 = False
    with open("vendor/google/lib/Android.mk") as inF:
        with open("t2.mk", "w+") as outF:
            for line in inF:
                for one in list_so2:
                    two = os.path.basename(one)
                    if two in line:
                        hit5108 = True
                        break
                else:
                    outF.write(line)
    if hit5108:
        my_sys("mv -f t2.mk vendor/google/lib/Android.mk")
    else:
        my_sys("rm -f t2.mk")

def adjust_project_folders_for_vphone(project_name, project_info):
    if not _is_vphone(project_name):
        return

    project = project_info["project"]
    one = "mediatek/config/%s/ProjectConfig.mk" % project
    two = project_custom_config_fallback(project_name)
    file1 = "t1.txt"
    my_sys("cp -f %s %s" % (one, file1))
    if two != None:
        my_sys("cat %s >> %s" % (two, file1))

    str1 = get_image_format_from_size(get_dimension_from_project_config(file1), project_name)
    my_dbg("adjust_project_folders_for_vphone:" + str1)
    list2 = glob.glob("baidu/prebuilt/*_baidu_apps_fanzhuo")
    for one in list2:
        if not str1 in one:
            my_sys("rm -rf %s" % one)
        else:
            cmd1 = "mv -f %s baidu/prebuilt/baidu_apps_fanzhuo" % one
            my_dbg(cmd1)
            my_sys(cmd1)
    my_sys("rm -rf %s" % file1)

def fixup_project_storage(project_name, project_info):
    one = "mediatek/config/%s/ProjectConfig.mk" % project_info["project"]
    two = project_bsp_config_fallback(project_name)
    if two == None:
        return
    if not os.path.exists(one) or not os.path.exists(two):
        return

    list1 = []
    with open(one) as inF:
        list1.extend(inF.readlines())

    one_b = "%s.global" % one
    if os.path.exists(one_b):
        with open(one_b) as inF:
            list1.extend(inF.readlines())
    one_c = "%s.global2" % one
    if os.path.exists(one_c):
        with open(one_c) as inF:
            list1.extend(inF.readlines())

    with open(two) as inF:
        list1.extend(inF.readlines())
    list1.reverse()

    """try best""" # pylint: disable=W0105
    if project_info["storage"] != "unknown":
        return

    for line in list1:
        if "MTK_EMMC_SUPPORT" in line:
            list1 = line.split("=")
            if len(list1) != 2:
                continue
            one = list1[0].strip()
            two = list1[1].strip()
            if "MTK_EMMC_SUPPORT" == one:
                break
    else:
        assert False

    if "no" == two:
        project_info["storage"] = "nand"
    elif "yes" == two:
        project_info["storage"] = "emmc"

def fixup_dpi_setting(project_info):
    if "vanzo73" in project_info["project"] or "vanzo13" in project_info["project"]:
        return
    lcm_width, lcm_height = get_dimension_from_project_config("./mediatek/config/%s/ProjectConfig.mk" % project_info["project"])
    lcm_density = get_resolution_from_dimension((lcm_width, lcm_height), project_info)

    if project_info["age"] >= PROJECT_INFO["mt6572jb3"]["age"]:
        targetfile1 = "./mediatek/config/%s/ProjectConfig.mk" % project_info["project"]
        if "xhdpi" == lcm_density:
            str1 = "MTK_PRODUCT_AAPT_CONFIG=xhdpi hdpi"
        elif "xxhdpi" == lcm_density:
            str1 = "MTK_PRODUCT_AAPT_CONFIG=xxhdpi xhdpi hdpi"
        else:
            str1 = "MTK_PRODUCT_AAPT_CONFIG=%s" % lcm_density
        if "nand" in project_info["id"] or "lca" in  project_info["id"]:
             str1 = "%s -sw600dp -sw720dp" % str1
#            min4977 = min(lcm_width, lcm_height)
#            if min4977 >= 720:
#                str1 = "%s -sw720dp" % str1
#            elif min4977 >= 600:
#                str1 = "%s -sw600dp" % str1
#            elif min4977 >= 480:
#                str1 = "%s -sw480dp" % str1
#            elif min4977 >= 320:
#                str1 = "%s -sw320dp" % str1
        msg0 = "#" * 78
        msg1 = "#" * 8 + "Below Setting is auto generated by script, dont edit directly" + "#" * 8
        my_sys("echo '" + msg0 + "' >> " + targetfile1)
        my_sys("echo '" + msg0 + "' >> " + targetfile1)
        my_sys("echo '" + msg1 + "' >> " + targetfile1)
        my_sys("echo '" + msg0 + "' >> " + targetfile1)
        my_sys("echo '" + msg0 + "' >> " + targetfile1)
        my_sys("echo '" + str1 + "' >> " + targetfile1)
        return

    file1 = "build/target/product/%s.mk" % project_info["project"]
    file2 = "%s.tmp" % file1
    with open(file1) as in_file:
        list1 = in_file.readlines()
    pos1 = -1
    len1 = len(list1)
    for i in range(len1 - 1, 0, -1):
        if "dpi" in list1[i] and len(list1[i].replace("dpi","").replace("\\","").strip()) < 3:
            pos1 = i
            break
    if pos1 <= 0:
        return
    if "dpi" in list1[pos1-1]:
        pos2 = pos1 - 1
    else:
        pos2 = pos1
    list2 = []
    for line in list1[:pos2]:
        list2.append(line)

    if "xhdpi" == lcm_density:
        list2.append("        xhdpi \\\n")
        list2.append("        hdpi\n")
    elif "xxhdpi" == lcm_density:
        list2.append("        xxhdpi\\\n")
        list2.append("        xhdpi \\\n")
        list2.append("        hdpi\n")
    else:
        list2.append("        %s\n" % lcm_density)

    for line in list1[pos1+1:]:
        list2.append(line)

    with open(file2, "w+") as out_file:
        for line in list2:
            out_file.write(line)
    os.rename(file2, file1)

def fixup_recovery_fstab(project_info):
    file1 = "./mediatek/config/%s/recovery.fstab.nand" % project_info["project"]
    file2 = "./mediatek/config/%s/recovery.fstab" % project_info["project"]
    if not os.path.exists(file1):
        return
    if project_info["storage"] == "nand":
        my_sys("ln -sf %s %s" % (os.path.basename(file1), file2))

def _add_keep_list_for_nand(project_name):
    project_info = get_project_info(project_name)

    if project_info['id'] not in ('mt6515', 'mt6515mtd', 'mt6575gbr2', 'mt6575icsr2', 'mt6517td', 'mt6577ics', 'mt6577jb', 'mt6575jb', 'mt6572jb3nand', 'mt6572jb3nandcta'):
        return

    # nand only
    if project_info['storage'] != 'nand':
        return

    # change nothing if it has no userdata at all
    apk_files = glob.glob('vendor/google/userdata/*.apk')
    apk_files.extend(glob.glob('vendor/google/userdata/custom/*.apk'))
    if len(apk_files) == 0:
        return

    keep_list_dir = 'mediatek'
    if project_info['android'] == '23':
        keep_list_dir = 'vendor/mediatek/etc'

    # add keep_list
    keep_list_file = os.path.join(keep_list_dir, 'keep_list')
    with open(keep_list_file, 'w') as txt:
        txt.writelines(['/data/app/'+os.path.basename(x)+'\n' for x in apk_files])

    # append macro to ProjectConfig.mk
    projectconfig = 'mediatek/config/{0}/ProjectConfig.mk'.format(project_info['project'])
    with open(projectconfig, 'a') as txt:
        txt.write('\nMTK_SPECIAL_FACTORY_RESET = yes\n')

    # add a line to vanzoxx_xx.mk to copy keep_list to /data/.keep_list
    mk_file = 'build/target/product/{0}.mk'.format(project_info['project'])
    with open(mk_file, 'a') as txt:
        txt.write('\nPRODUCT_COPY_FILES += {0}:data/app/.keep_list\n'.format(keep_list_file))

def _remove_google_apps_from_non_mul_projects(project_name, project_info):
    def _is_89_project():
        return project_info['id'] in ('mt6589jb', 'mt6589jb2')

    def _is_77jb_nand_project():
        return project_info['id'] == 'mt6577jb' and project_info['storage'] == 'nand'

    # only domestic projects
    if _is_mul(project_name):
        return

    # 89 and 77jb nand projects
    if not (_is_89_project() or _is_77jb_nand_project()):
        return

    # Do continue, only if it does not have customized app/Android.mk
    app_mk = '{0}/vendor/google/app/Android.mk.overlay.{1}'.format(gOverlayRootRO, npn(project_name))
    if project_custom_get_fallback(app_mk):
        return

    mkdir_p(os.path.dirname(app_mk))
    with open(app_mk, 'wt') as mk:
        mk.write('''LOCAL_PATH:= $(call my-dir)

copy_from := \\
    GoogleContactsSyncAdapter.apk \\
    GoogleLoginService.apk \\
    GoogleServicesFramework.apk \\
    NetworkLocation.apk \\
    Phonesky.apk \\


$(call add-prebuilt-files, APPS, $(copy_from))
''')

def _get_all_apks():
    # apks under google/
    apks = glob.glob('vendor/google/*.apk')

    # apks in app/Android.mk
    if os.path.exists('vendor/google/app/Android.mk'):
        app_apks = get_keyed_list_from_file('vendor/google/app/Android.mk', 'copy_from')
        apks.extend([os.path.join('vendor/google/app', i) for i in app_apks])

    # apks in 3rdapp/Android.mk and 3rdapp/custom
    if os.path.exists('vendor/google/3rdapp/Android.mk'):
        erdapp_apks = get_keyed_list_from_file('vendor/google/3rdapp/Android.mk', 'copy_from')
        apks.extend([os.path.join('vendor/google/3rdapp', i) for i in erdapp_apks])
        apks.extend(glob.glob('vendor/google/3rdapp/custom/*.apk'))

    # apks in userdata/Android.mk and userdata/custom
    if os.path.exists('vendor/google/userdata/Android.mk'):
        userdata_apks = get_keyed_list_from_file('vendor/google/userdata/Android.mk', 'copy_from')
        apks.extend([os.path.join('vendor/google/userdata', i) for i in userdata_apks])
        apks.extend(glob.glob('vendor/google/userdata/custom/*.apk'))

    # return a list of (apk_file_path, apk_package_name)
    all_ = [(apk, _get_package_name_from_apk(apk)) for apk in apks]
    # return a list of above tuple which has valid apk_package_name
    return [i for i in all_ if i[1]]

def _exclusive_apk_check(all_apks):
    lists = {'searchbox':('com.baidu.searchbox_ktouch',
                          'com.baidu.searchbox',
                          'com.android.quicksearchbox',
                          'com.google.android.googlequicksearchbox')}

    # if more than one apk fall into the same category, panic
    error = False
    for name, list_ in lists.items():
        potential_conflicts = []
        potential_packages = []
        for apk, package in all_apks:
            if package in list_:
                potential_conflicts.append(apk)
                potential_packages.append((apk, package, list_.index(package)))

        if len(potential_conflicts) > 1:
            my_dbg(_yellow('Warning: {0} fall into the {1} category'.format(' '.join(potential_conflicts), name)))
            potential_packages.sort(lambda one,two: cmp(one[2], two[2]))
            """not remove
            for apk in potential_packages[1:]:
                apk1= apk[0]
                my_dbg(_yellow('remove {0}'.format(apk1)))
                my_sys("rm -rf {0}".format(apk1))
                if not "custom" in apk1:
                    androidmk1 = "%s/Android.mk" % os.path.dirname(apk1)
                    cmd1 = "sed -i '/{0}/d' {1}".format(os.path.basename(apk1), androidmk1)
                    my_sys(cmd1)
            """

            #error = True
    if error:
        sys.exit(1)

def _delete_duplicated_apks(all_apks):
    def _is_customers_apk(apk):
        if _is_app_apk(apk):
            return False
        if _is_neiz_apk(apk):
            return False
        return True

    def _is_neiz_apk(apk):
        basename = os.path.basename(apk[0])
        if basename in ('MediaTekBackup.apk', 'MediaTekData.apk'):
            return True
        if basename.startswith('neiz_'):
            return True
        return False

    def _is_app_apk(apk):
        return apk[0].startswith('vendor/google/app')

    def _delete_from_makefile(filename):
        if '/custom/' in filename:
            return
        basename = os.path.basename(filename)
        makefile = None
        if filename.startswith('vendor/google/app'):
            makefile = 'vendor/google/app/Android.mk'
        elif filename.startswith('vendor/google/3rdapp'):
            makefile = 'vendor/google/3rdapp/Android.mk'
        elif filename.startswith('vendor/google/userdata'):
            makefile = 'vendor/google/userdata/Android.mk'
        else:
            makefile = 'vendor/google/Android.mk'

        org_lines = []
        with open(makefile) as file_:
            org_lines = file_.readlines()

        with open(makefile, 'w') as file_:
            for index, line in enumerate(org_lines):
                if re.match(r'^\s*{0}\W'.format(basename), line):
                    file_.writelines(org_lines[index+1:])
                    break
                else:
                    file_.write(line)
            else:
                my_dbg(_red('Error: cannot find {0} in {1}'.format(filename, makefile)))
                sys.exit(1)

    def _remove_apk(apk, list_):
        while True:
            for i in list_:
                if apk[0] != i[0] and apk[1] == i[1]:
                    my_dbg(_yellow('Warning: already has ' + apk[0]))
                    my_dbg(_yellow('Warning: delete ' + i[0]))
                    # delete file from disk
                    os.remove(i[0])
                    # delete it from corresponding Android.mk
                    _delete_from_makefile(i[0])
                    # remove it from lists
                    list_.remove(i)
                    all_apks.remove(i)
                    break
            else:
                break

    apks = set(all_apks)
    # remove neiz/app apks have the same package name with customer's apks
    customers_apk = [i for i in apks if _is_customers_apk(i)]
    apks.difference_update(customers_apk)
    [_remove_apk(i, apks) for i in customers_apk]

    # remove app apks have the same name package name with neiz apks
    neiz_apk = [i for i in apks if _is_neiz_apk(i)]
    apks.difference_update(neiz_apk)
    [_remove_apk(i, apks) for i in neiz_apk]

    return all_apks

def _duplicated_apk_check():
    all_apks = _get_all_apks()
    # delete apks have the same package name
    _delete_duplicated_apks(all_apks)
    # panic if multiple apks fall into the same category
    _exclusive_apk_check(all_apks)

def get_wallpaper_list_from_wallpaper_xml(xml):
    wallpapers = []
    with open(xml) as txt:
        for line in txt:
            m = re.match(r'^\s*<item>\s*(.+)\s*</item>\s*$', line)
            if m:
                wallpapers.append(m.group(1))
    return wallpapers

def _replace_default_wallpaper(project_name):
    # 23 does not have uniformed WallpaperChooser path, it is
    # difficult to find out which drawable folder it is using
    project_info = get_project_info(project_name)
    if project_info['android'] == '23':
        return

    if project_name.startswith("mt72ali_") or project_name.startswith("mt82ali_"):
        return

    wallpaper_dir = os.path.join(_get_project_wallpaper_dir(project_name), 'res')
    # some repo does not have WallpaperChooser, cmcc etc
    if not os.path.exists(wallpaper_dir):
        return

    dimension = _project_custom_gen_project_dimension(project_name)
    res = get_resolution_from_dimension(dimension, project_info)
    customized = project_custom_get_fallback('%s/frameworks/base/core/res/res/drawable-%s/default_wallpaper.jpg.overlay.%s' % (gOverlayRootRO, res, npn(project_name)))
    # if current project has customized default wallpaper already,
    # nothing will be done
    if customized:
        return

    xml = os.path.join(wallpaper_dir, 'values/wallpapers.xml')
    wallpapers = sorted(get_wallpaper_list_from_wallpaper_xml(xml))
    cjpg = [i for i in wallpapers if i.startswith('wallpaper_c')]
    # if customer provided wallpaper, then use one of them as default
    wallpaper = wallpapers[0]
    if cjpg:
        wallpaper = cjpg[0]
    src = os.path.join(wallpaper_dir,
                       'drawable-{0}/{1}.jpg'.format(res, wallpaper))

    dst = 'frameworks/base/core/res/res/drawable-%s/default_wallpaper.jpg' % res
    shutil.copy2(src, dst)
#must invoke this after the true defalut wallpaper is set
def remove_defalut_wallpaper_from_chooser(project_name):
    project_info = get_project_info(project_name)
    if not ge_kk(project_name):
        return
    if _is_tphone(project_name) or _is_ophone(project_name):
        print "for tphone project donot delete the wallpaper"
        return
    print "here to remove kk duplicate default wallpaper"
    dimension = _project_custom_gen_project_dimension(project_name)
    res1 = get_resolution_from_dimension(dimension, project_info)
    wallpaper_dir = os.path.join(_get_project_wallpaper_dir(project_name), 'res')
    dst_folder = os.path.join(wallpaper_dir, 'drawable-{0}'.format(res1))
    wallpapers = glob.glob(os.path.join(dst_folder, '*.jpg'))
    default_wallpaper="frameworks/base/core/res/res/drawable-%s/default_wallpaper.jpg"%(res1)
    for item in wallpapers:
        if is_same_file(item,default_wallpaper):
            os.remove(item)
            small_item=item.replace('.jpg', '_small.jpg')
            if os.path.exists(small_item):
                os.remove(small_item)
            '''
            #here need remove the xml
            src_file=os.path.join(wallpaper_dir,"values/wallpapers.xml")
            if not os.path.exists(src_file):
                print "Strange!why can not find %s"%(src_file)
                return False
            base_name,_=os.path.splitext(os.path.basename(item))
            cmd="sed -i '/.*%s.*/d' %s"%(base_name,src_file)
            #print "cmd:",cmd
            my_sys(cmd)
            '''
            return True
    return False

def _replace_default_site_nav(project_name):
    def _replaceable(path):
        # if file does not exists, no action should be taken
        '''
        if not os.path.exists(path):
            return False
        '''
        # if file has been changed, no action should be taken
        basename = os.path.basename(path)
        dirname=os.path.dirname(path)
        if not os.path.exists(dirname):
            return False
        #out = subprocess.Popen('git status --porcelain ' + basename, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=os.path.dirname(path)).communicate()[0]
        out = subprocess.Popen('git status --porcelain ' , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=os.path.dirname(path)).communicate()[0]
        if out and len(out):
            modified_files=out.split("\n")
            for item in modified_files:
                if item.find(basename)>=0:
                    return False
        return True

    def _delete_dup_entry(entry):
        # entry's position varies from version to version
        out = subprocess.Popen('''grep -wl '"{0}"' *'''.format(entry), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd='packages/apps/Browser/res/values').communicate()[0]
        if len(out.splitlines()) == 1: # no duplicated entry
            return
        os.system('''sed -i '/"{0}"/ d' packages/apps/Browser/res/values/strings_custom_url.xml'''.format(entry))

    project_info = get_project_info(project_name)
    android_version = project_info['android']
    # this operation requires strings_custom_url.xml contains
    #+predefined_websites_default_optr only, maybe plus an
    #+optional homepage_base
    #if not int(android_version) <= 42:
    #    return

    '''
    files = ('packages/apps/Browser/res/values/strings_custom_url.xml',
             'packages/apps/Browser/res/raw/site_navigation_default_default1.png',
             'packages/apps/Browser/res/raw/site_navigation_default_default2.png',
             'packages/apps/Browser/res/raw/site_navigation_default_default3.png',
             'packages/apps/Browser/res/raw/site_navigation_default_default4.png',
             'packages/apps/Browser/res/raw/site_navigation_default_default5.png',
             'packages/apps/Browser/res/raw/site_navigation_default_default6.png')
    '''
    lcm_width, lcm_height = get_dimension_from_project_config("./mediatek/config/%s/ProjectConfig.mk" % project_info['project'])
    icon_path = 'raw-xxhdpi' if lcm_width == 1080 and lcm_height == 1920 else 'raw'
    files = ('packages/apps/Browser/res/values/strings_custom_url.xml',
             'packages/apps/Browser/res/{0}/site_navigation_default_default1.'.format(icon_path),
             'packages/apps/Browser/res/{0}/site_navigation_default_default2.'.format(icon_path),
             'packages/apps/Browser/res/{0}/site_navigation_default_default3.'.format(icon_path),
             'packages/apps/Browser/res/{0}/site_navigation_default_default4.'.format(icon_path),
             'packages/apps/Browser/res/{0}/site_navigation_default_default5.'.format(icon_path),
             'packages/apps/Browser/res/{0}/site_navigation_default_default6.'.format(icon_path))
    # only if no files has been modified
    if not all([_replaceable(i) for i in files]):
        return
    if _is_cta(project_name):
        return
    if project_name.find("cmcc")>=0:
        return
    #added by wf for remove first
    for item in files:
        real_file=glob.glob(item+'*')
        for one_file in real_file:
            os.remove(one_file)

    # replace default site nav icons and strings_custom_url.xml, affects
    # default nav sites and default home page
    path = os.path.expanduser('~/build_projects/database/{0}/nav'.format('mul' if _is_mul(project_name) else 'domestic'))
    for item in files:
        src = glob.glob(os.path.join(path, item) + '*')[0]
        shutil.copy(src, os.path.dirname(item))

    if not ge_kk(project_name):
        _delete_dup_entry('homepage_base')
        _delete_dup_entry('homepage_for_op02')

def _validate_project(project_name):
    assert project_custom_config_fallback(project_name)

def _do_add_watermark(project_info):
    if project_info["age"] < PROJECT_INFO["mt6589jb2"]["age"]:
        return
    if os.environ.has_key(COMITTER_ENV_KEY):
        comitter_name = os.environ[COMITTER_ENV_KEY]
    else:
        comitter_name = "scm"
    my_dbg("comitter_name:%s" % comitter_name)

    if "deamon" in comitter_name and not "demo" in comitter_name:
        return
    my_sys("cp -f ~/build_projects/database/watermark.* /tmp/;rm -f /tmp/*.bmp")
    with open("./mediatek/config/%s/ProjectConfig.mk" % project_info["project"]) as inF:
        for line1 in inF:
            if "BOOT_LOGO" in line1 and "=" in line1:
                logo1 = line1.split("=")[1].strip()
    file1 = "./mediatek/custom/common/lk/logo/%s/%s_uboot.bmp" % (logo1, logo1)
    cmd1 = "phatch -c /tmp/watermark.phatch %s" % file1
    my_sys(cmd1)
    cmd1 = "mv -f /tmp/%s %s" % (os.path.basename(file1), file1)
    my_sys(cmd1)

def add_to_python_path():
        my_home=os.path.expanduser('~')
        config_file=os.path.join(my_home,".bashrc")
        regex=re.compile("export.*PYTHONPATH.*git/vanzo_team2/wangfei")
        find=False
        with open(config_file) as in_file:
            lines=in_file.readlines()
            for line in lines:
                if re.match(regex,line):
                    find=True
                    break
        if find == False:
            with open(config_file,"a+") as out_file:
                line="export PYTHONPATH=$PYTHONPATH:%s/git/vanzo_team2/wangfei/python_tools/\n"%(my_home)
                out_file.write(line)
                line="source %s/git/vanzo_team2/wangfei/python_tools/main_entry\n"%(my_home)
                out_file.write(line)
        path=os.path.join(os.getcwd(),"python_tools")
        if not os.path.exists(path):
            path="%s/git/vanzo_team2/wangfei/python_tools/"%(my_home)
            if not os.path.exists(path):
                return False
        for item in sys.path:
            if item == path:
                return True
        sys.path.insert(0,path)
        return True

def fixup_battery_capacity(project_name, project_info):
    def __fix_file(file_name):
        #Check whether the file has modified.
        ret = my_sys("cd %s; git status | grep %s" % (os.path.dirname(file_name), os.path.basename(file_name)))
        if ret != 0:
            is_batthv = False
            battery_cap = 0
            custom_file = project_custom_config_fallback(project_name)
            list1 = []
            with open(custom_file) as in_file:
                lines = in_file.readlines()
                for line in lines:
                    if line.startswith("VANZO_CUSTOM_BATTERYCAP"):
                        battery_cap = int(line.split("=")[1].split()[0].strip())
                    if line.startswith("HIGH_BATTERY_VOLTAGE_SUPPORT"):
                        if cmp(line.split("=")[1].split()[0].strip(), "yes") == 0:
                            is_batthv = True
            if battery_cap == 0:
                my_dbg(_red("Please Set VANZO_CUSTOM_BATTERYCAP in file %s" % custom_file))
                assert False,"battery error !!!!!!!!!!!!!!!!!!!!!"
            if is_batthv:
                list1 = glob.glob("vendor/vanzo_custom/overlay_projects/%s.overlay.*mah.hv" % file_name)
            else:
                list1 = glob.glob("vendor/vanzo_custom/overlay_projects/%s.overlay.*mah" % file_name)
            list1.sort()
            for file1 in list1:
                if battery_cap <= int(file1.split(".")[3].split()[0].strip().strip("mah")):
                    print "modify battery capacity using file %s" % file1
                    my_sys("cp %s %s" % (file1, file_name))
                    break
    if project_info["age"] < 2700:
        return
    time1 = datetime.datetime(2014, 9, 25, 8, 0, 0)
    if os.path.exists(".repo/manifests/%s.xml" % project_name):
        change_time1 = _get_change_time(".repo/manifests/%s.xml" % project_name)
    else:
        custom_file = project_custom_config_fallback(project_name)
        if not custom_file:
            print "Error:can not get the custom file"
            return
        change_time1 = _get_change_time(custom_file)
    if change_time1 > time1:
        if os.path.exists("mediatek/custom/%s/kernel/battery/battery/cust_battery_meter.h" % project_info["project"]):
            __fix_file("mediatek/custom/%s/kernel/battery/battery/cust_battery_meter.h" % project_info["project"])
        elif os.path.exists("mediatek/custom/%s/kernel/battery/battery/cust_battery_meter.h" % project_info["id"][0:6]):
            __fix_file("mediatek/custom/%s/kernel/battery/battery/cust_battery_meter.h" % project_info["id"][0:6])
        if os.path.exists("mediatek/custom/%s/kernel/battery/battery/cust_battery_meter_table.h" % project_info["id"][0:6]):
            __fix_file("mediatek/custom/%s/kernel/battery/battery/cust_battery_meter_table.h" % project_info["id"][0:6])

#partial: false:only apply patch
#essential: false:for export code to  3rd party
def do_update_overlay(partial=False, essential=False):
    if not partial:
        normalize_cwd(".repo")
    add_success=add_to_python_path()
    project_custom_build_fallback_list("vendor/vanzo_custom/fallback_extra.txt")
    project_name = get_project_name()
    project_info = get_project_info(project_name)
    if project_info == None:
        my_dbg("The project has not project info!")
    print "before _project_custom_ensure_overlay_and_patchset_repos"
    _project_custom_ensure_overlay_and_patchset_repos(project_name)
    print "after _project_custom_ensure_overlay_and_patchset_repos"
    if not partial:
        _validate_project(project_name)
    fixup_project_storage(project_name, project_info)
    print "project_info:",project_info
    assert project_info["storage"] != "unknown"

    """
    cmd1 = "find -L vendor/vanzo_custom -type l"
    list1 = commands.getstatusoutput(cmd1)[1].split()
    assert len(list1) == 1, "found dead link by:find -L vendor/vanzo_custom -type l!"
    """

    my_dbg("project name:" + project_name)
    if not partial:
        adjust_project_folders_for_vphone(project_name, project_info)
        if not essential:
            update_buildinfo()
            _remove_google_apps_from_non_mul_projects(project_name, project_info)

    do_copy_vanzo_team_base(project_name)

    project_patchsets=None
    project_overlays=None
    use_new_update=False
    if not ge_kk(project_name):
        uniq_patchsets = gen_unique_patchset_list(project_name)
        project_patchsets = gen_project_patchset_list(project_name, uniq_patchsets)
    else:
        use_new_update=True
        try:
            from vanzo_worker import VanzoWorker
            print "here use new update_overlay"
            worker=VanzoWorker()
            list_all=worker.list_patchset_overlay_fast(project_name,"False",True)
            project_patchsets,project_overlays=worker.transer_to_vanzo_interface(list_all)
        except Exception, e:
            print e
            assert False, "Something wrong with kk po scripts"

    update_patchsets(project_patchsets, project_info["project"], partial)


    if not partial:
        if use_new_update==False:
            uniq_overlays = gen_unique_overlays_list(project_name)
            project_overlays = gen_project_overlays_list(project_name, uniq_overlays)

        update_overlays(project_overlays)

        do_concat_files(project_name)

        if not essential:
            if project_info["id"] in ("mt6573v3", "mt6513r4",):
                remove_other_res(project_info["project"])
            else:
                remove_other_res2(project_info["project"])

            remove_redundant_wallpapers(project_name)
            update_geocoding_db(project_name, project_info)
            #for app grouper request ,do not modify apn for cmcc
            if "cmcc" not in project_name and "cmcc" not in project_info["project"]:
                update_apns_from_db(project_info)
                update_spn_from_db(project_info)
            _replace_default_wallpaper(project_name)
            remove_defalut_wallpaper_from_chooser(project_name)
            do_add_recommended_apks(project_name)
            remove_some_apks_for_mul(project_name)
            _duplicated_apk_check()
            _replace_default_site_nav(project_name)
            gen_so_from_apk(project_info["project"])
            remove_redudant_google_libs()
            _do_add_watermark(project_info)
            _add_keep_list_for_nand(project_name)
            if ge_kk(project_name):
                try:
                    print "here to invoke auto list script"
                    from request.autolcmlist_request import AutoLcmListRequest
                    request=AutoLcmListRequest()
                    request.realize()
                    from request.autocameralist_request import AutoCameraListRequest
                    request=AutoCameraListRequest()
                    request.realize()
                    from request.routinecheck_request import RoutineCheckRequest
                    request=RoutineCheckRequest()
                    if request.realize()==False:
                        print "routine check error,please modify first!"
                        sys.exit()
                except Exception, e:
                    print e

        fixup_dpi_setting(project_info)
        fixup_recovery_fstab(project_info)
        fixup_battery_capacity(project_name, project_info)

###############################################################################
########@@ The end
###############################################################################
