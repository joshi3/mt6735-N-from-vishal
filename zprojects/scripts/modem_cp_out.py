#!/usr/bin/python
#! -*-coding: utf-8 -*-

import re
import os
import sys
import glob
import datetime
import time
import commands
from modem_config import all_projects

starttime = time.localtime()
strStartTime = time.strftime('%Y%m%d-%H%M', starttime)
pwd_current = os.getcwd()

def GetParentPath(strPath):
    if not strPath:
        return None
    lsPath = os.path.split(strPath);
    if lsPath[1]:
        return lsPath[0]
    lsPath = os.path.split(lsPath[0])
    return lsPath[0]

pwd_parent = GetParentPath(pwd_current)

def list_forward_dict(onelist):	#列表转字典,输入序号,获取对应列表值
    end_dict = {}
    for l in onelist:
        end_dict[onelist.index(l)] = l
    for d in end_dict:
        print d, end_dict[d]
    num = int(raw_input("input num: "))
    return end_dict[num]

def parentheses_split_underscore(astr):	#有()的字符串,转为以_链接
    l =  []
    if '(' or ')' in astr:
        ll = astr.split('(')
        for i in ll:
            if ')' in i:
                for k in i.split(')'):
                    if k:
                        l.append(k)
            else:
                l.append(i)
    return '_'.join(l)

def copy_files(build_project):
    momdem_out_path = pwd_parent + "/" + build_project + "-" + strStartTime +"/"

    file_dir_db = "build/" + build_project + "/DEFAULT/tst/database/"
    file_dir_bin = "build/" + build_project + "/DEFAULT/bin/"

    if os.path.exists(file_dir_db):
        os.system("mkdir -p %s" % momdem_out_path)
        print momdem_out_path
    else:
        print 'copy %s not exist' % build_project
        sys.exit()
    print "#"*80

    os.chdir(file_dir_bin)
    print '#'* 30 + "copy bin files"
    filename = glob.glob('DbgInfo*')[0]
    m = re.match(r'^(DbgInfo.+)_P\d+_(\d{4}_\d{2}_\d{2}_\d{2}_\d{2})', filename)
    cp_cmd ="cp"+" -vpfH " + filename +" " + momdem_out_path + all_projects[build_project]['images'][2]

    os.system(cp_cmd)
    filename2 = glob.glob('*.bin')[0]
    cp_cmd ="cp"+" -vpfH " + filename2 +" " + momdem_out_path + all_projects[build_project]['images'][3]

    os.system(cp_cmd)
    filename3 = sorted(glob.glob('VANZO*.mak'))[0]
    cp_cmd ="cp"+" -vpfH " + filename3 +" " + momdem_out_path + all_projects[build_project]['images'][4]

    os.system(cp_cmd)
    filename4 = glob.glob('*.elf')[0]
    cp_cmd ="cp"+" -vpfH " + filename4 +" " + momdem_out_path + all_projects[build_project]['images'][5]
    os.system(cp_cmd)

    os.chdir(pwd_current)
    os.chdir(file_dir_db)
    b = os.getcwd()
    print '#'* 30 + "copy databases files"
    filename5 = glob.glob('BPLGUInfo*')[0]
    cp_cmd ="cp"+" -vpfH " + filename5 +" " + momdem_out_path + all_projects[build_project]['images'][0]
    os.system(cp_cmd)

    filename6 = "catcher_filter.bin"
    cp_cmd ="cp"+" -vpfH " + filename6 +" " + momdem_out_path + all_projects[build_project]['images'][1]
    os.system(cp_cmd)

def copy_files_lt(build_project):
    momdem_out_path = pwd_parent + "/" + build_project + "-" + strStartTime +"/"

    build_type = all_projects[build_project]['code_build_type']
    if '('  in build_type:
        lt = build_type.split('(')
        file_dir_db = 'build/' + lt[0] + '/' + lt[-1].split(')')[0] + '/bin/'
        file_dir_bin = 'build/' + lt[0] + '/' + lt[-1].split(')')[0] + '/dhl/database/'
    else:
        lt = build_type.split('.')
        file_dir_db = 'build/' + lt[0] + '/bin/'
        file_dir_bin = 'build/' + lt[0] + '/dhl/database/'

    if os.path.exists(file_dir_db):
        os.system("mkdir -p %s" % momdem_out_path)
        print momdem_out_path
    else:
        print 'copy %s not exist' % build_project
        sys.exit()

    print '#'* 15 + "copy bin files" + '#'* 15
    filename = commands.getoutput('find %s -maxdepth 1 -name "DbgInfo*" ' % file_dir_db)
    cp_cmd ='cp -vpfH "%s" "%s"' % (filename, momdem_out_path + all_projects[build_project]['images'][2])
    os.system(cp_cmd)

    filename2 = commands.getoutput('find %s -maxdepth 1 -name "*DSP*.bin" ' % file_dir_db)
    cp_cmd ='cp -vpfH "%s" "%s"' % (filename2, momdem_out_path + all_projects[build_project]['images'][3])
    os.system(cp_cmd)

    if 'VANZO95' in build_project.split('_') or 'VANZO6752' in build_project.split('_'):
        filename3 = commands.getoutput('find %s -maxdepth 1 -name "*PCB*.bin" ' % file_dir_db)
    else:
        filename3 = commands.getoutput('find %s -maxdepth 1 -name "modem.img" ' % file_dir_db)
    cp_cmd ='cp -vpfH "%s" "%s"' % (filename3, momdem_out_path + all_projects[build_project]['images'][4])
    os.system(cp_cmd)

    filename4 = commands.getoutput('find %s -maxdepth 1 -name "~VANZO*.mak" ' % file_dir_db)
    cp_cmd ='cp -vpfH "%s" "%s"' % (filename4, momdem_out_path + all_projects[build_project]['images'][5])
    os.system(cp_cmd)

    filename5 = commands.getoutput('find %s -maxdepth 1 -name "*PCB*.elf" ' % file_dir_db)
    cp_cmd ='cp -vpfH "%s" "%s"' % (filename5, momdem_out_path + all_projects[build_project]['images'][6])
    os.system(cp_cmd)

    print '#'* 15 + "copy database files" + '#'* 15
    filename6 = commands.getoutput('find %s -maxdepth 1 -name "BPLGUInfo*" ' % file_dir_bin)
    cp_cmd ="cp"+" -vpfH " + filename6 +" " + momdem_out_path + all_projects[build_project]['images'][0]
    os.system(cp_cmd)

    filename7 = commands.getoutput('find %s -maxdepth 1 -name "catcher_filter.bin" ' % file_dir_bin)
    cp_cmd ="cp"+" -vpfH " + filename7 +" " + momdem_out_path + all_projects[build_project]['images'][1]
    os.system(cp_cmd)

if __name__ == '__main__':
    select_list = commands.getoutput("ls make |grep -i VANZO").split()
    list_project = list_forward_dict(select_list)
    build_project = parentheses_split_underscore(list_project.split('.mak')[0])
    print build_project
    if 'LT' in build_project.split('_') or 'LWT' in build_project.split('_'):
        copy_files_lt(build_project)
    else:
        copy_files(build_project)
