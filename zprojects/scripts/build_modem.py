#!/usr/bin/python
#! -*-coding: utf-8 -*-

import os
import sys
import glob
import commands
import shutil
import datetime
import time

modem_build_server_ip = "192.168.11.199"
def build_modem_on_win(root1, target1):
    def get_ip_address(ifname):
        import socket,fcntl,struct
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,struct.pack('256s', ifname[:15]))[20:24])
        except:
            return ""
    def get_ip():
        for i in range(100):
            interface = "eth%d" % i
            addr = get_ip_address(interface)
            if len(addr) > 5:
                return addr

    BUILD_TIME = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    client_dir_root = "request_%s_%s" % (get_ip().replace(".", "_"), BUILD_TIME)

    mounted_dir_root = "/tmp/for_modem_build_on_win"
    if mounted_dir_root in commands.getstatusoutput("mount")[1]:
       cmd1 = "sudo umount %s" % mounted_dir_root
       os.system(cmd1)

    if not os.path.exists(mounted_dir_root):
        cmd1 = "mkdir -p %s" % mounted_dir_root
        os.system(cmd1)

    ret = -1
    for i in range(100):
        cmd1 = "sudo mount.cifs //%s/ondemand  %s -o guest,noperm,uid=%s,gid=%s" % (modem_build_server_ip, mounted_dir_root, os.getuid(), os.getgid())
        ret = os.system(cmd1)
        if ret == 0:
            break
        time.sleep(5)
    else:
        print "mount.cifs exceeds max try time"
        return -1

    client_dir_root_full = "%s/%s" % (mounted_dir_root, client_dir_root)
    cmd1 = "mkdir -p %s" % client_dir_root_full
    os.system(cmd1)
    cmd1 = "cp -rL %s %s/code" % (root1, client_dir_root_full)
    os.system(cmd1)
    cmd1 = """touch "%s/%s" """% (client_dir_root_full, target1)
    os.system(cmd1)
    cmd1 = """touch "%s/status_inited.txt" """% (client_dir_root_full)
    os.system(cmd1)

    #wait for build done on server
    status_file = os.path.join(client_dir_root_full, "status_built.txt")
    status_file2 = os.path.join(client_dir_root_full, "status_err.txt")
    time1 = 0
    while not os.path.exists(status_file) and not os.path.exists(status_file2):
        time1 =  time1 + 1
        if time1 > 60:
            print "could not see status_built.txt or status_err.txt"
            return -1
        time.sleep(5)

    cmd1 = "cp -af %s/code/build %s/" % (client_dir_root_full, root1)
    os.system(cmd1)

    if os.path.exists(status_file2):
        print "status_err.txt, windows rvct build modem err"
        return -1

    status_file2 = os.path.join(client_dir_root_full, "status_copied.txt")
    cmd1 = "mv -f %s %s" % (status_file , status_file2)
    os.system(cmd1)

    #clean up, umount
    cmd1 = "sudo umount %s" % (mounted_dir_root)
    os.system(cmd1)
    return 0

def get_modem_c2k(modem_root, board_name,item):
    dst_path="vendor/mediatek/proprietary/modem/%s"%(item)
    if os.path.exists(dst_path):
        return 0

    pwd=os.getcwd()
    path=os.path.join(modem_root,item)
    if not os.path.exists(path):
        print "Error Can not find %s\n"%(path)
        return -1
    os.chdir(path)

    make_file = "{}.mak".format(item.upper())
    make_path=glob.glob("stack/CP/make/*.mak")
    make_path.extend(glob.glob("stack/CP/make/projects/*.mak"))
    make_file=None
    find = False
    for each_make in make_path:
        make_file=os.path.basename(each_make)
        if make_file.lower().startswith(item):
            find = True
            break
    if not find:
        print "Error,Can not find make file:%s.mak,pwd:%s"%(item,os.getcwd())
        return -1

    cmd = "rm -rf stack/CP/build"
    os.system(cmd)

    res = build_modem_on_win("stack/CP", make_file)
    if res != 0:
        print "Compile %s error"%(make_file)
        return -1
    os.chdir(pwd)

    cmd="""device/mediatek/build/build/tools/modemRenameCopy.pl %s/stack/CP "%s" """%(path, make_file)
    res = os.system(cmd)
    if res != 0:
        return -1
    img_path=os.path.join("%s/stack/CP" % path,"temp_modem")
    if not os.path.exists(img_path):
        return -1
    cmd="cp -a %s %s"%(img_path,dst_path)
    res = os.system(cmd)
    if res != 0:
        return -1
    return 0

def get_modem(modem_root,board_name,modem_config):
    request_modem_list=modem_config
    #cmd1 = 'find make -maxdepth 1 -name VANZO*.mak'
    pwd=os.getcwd()
    for item in request_modem_list:
        item=item.strip().lower()
        #here to filter out the c2k ,becase the c2k compile in the windows
        if item.find('irat')>0:
            # Vanzo:songlixin on: Mon, 07 Sep 2015 16:03:45 +0800
            # to build c2k modem on windows
            #print 'here do not compile c2k modem'
            print 'here compile c2k modem'
            res = get_modem_c2k(modem_root, board_name,item)
            assert res == 0, "build c2k modem failed!"
            # End of Vanzo: songlixin
            continue
        path=os.path.join(modem_root,item)
        if not os.path.exists(path):
            print "Error Can not find %s\n"%(path)
            return -1
        os.chdir(path)
        make_path=glob.glob("make/V*.mak")
        make_path.extend(glob.glob("make/projects/V*.mak"))
        make_path.extend(glob.glob("make/mt*.mak"))
        make_path.extend(glob.glob("make/MT*.mak"))
        #print 'make_path:',make_path
        make_file=None
        find = False

        #Find make file from CUSTOM_MODEM
        for each_make in make_path:
            make_file=os.path.basename(each_make)
            #print 'make_file:%s,item %s'%(make_file.lower(),item)
            tmp_make = make_file
            if tmp_make.lower() == item+".mak":
                find = True
                break
            else:
                tmp_make = tmp_make.lower().replace("(","_")
                tmp_make = tmp_make.lower().replace(")","")
                #print 'tmp_make:',tmp_make
                if tmp_make == item+".mak":
                    find = True
                    break
        if not find:
            print "Error,Can not find make file:%s.mak,pwd:%s"%(item,os.getcwd())
            return -1
        
        cmd = "./m '%s' new" % make_file
        print 'build modem cmd:',cmd
        res = os.system(cmd)
        if res != 0:
            print "Compile %s error"%(make_file)
            return -1
        os.chdir(pwd)
        make_file = make_file.replace(".mak","")
        cmd="device/mediatek/build/build/tools/modemRenameCopy.pl %s \"%s\""%(path,make_file)
        print 'copy modem cmd:',cmd
        res = os.system(cmd)
        if res != 0:
            return -1
        img_path=os.path.join(path,"temp_modem")
        if not os.path.exists(img_path):
            return -1
        dst_path="vendor/mediatek/proprietary/modem/%s"%(item)

        # Vanzo:yucheng on: Fri, 08 Jan 2016 22:58:23 +0800
        #If directory not existed, create it
        # End of Vanzo: yucheng
        if not os.path.exists(dst_path):
            os.system("mkdir -p %s" % (dst_path))

        shutil.rmtree(dst_path)
        cmd="cp -a %s %s"%(img_path,dst_path)
        res = os.system(cmd)
        if res != 0:
            return -1
        #copy Android.mk automatically
        cp_android_mk = "cp device/mediatek/build/build/tools/modem/modem_Android.mk  vendor/mediatek/proprietary/modem/Android.mk"
        res = os.system(cp_android_mk)
        if res != 0:
            return -1

    return 0

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print "Usage:%s modem_root board_name modem_config"%(sys.argv[0])
        sys.exit(-1)
    else:
        modem_root=sys.argv[1]
        board_name=sys.argv[2]
        modem_config=sys.argv[3:]
    res = get_modem(modem_root,board_name,modem_config)
    sys.exit(res)
