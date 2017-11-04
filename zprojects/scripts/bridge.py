import sys
import os
from vanzo_common2 import npn, get_project_info,my_sys,normalize_cwd,PROJECT_INFO,fallback_rules_keys,fallback_exclude_list,PATCHSET_KEY2,OVERLAY_KEY2,get_project_ui , remove_other_res, remove_other_res2, remove_redundant_wallpapers, _replace_default_wallpaper, do_add_recommended_apks, remove_some_apks_for_mul, _duplicated_apk_check, _replace_default_site_nav, gen_so_from_apk, remove_redudant_google_libs, _do_add_watermark, _add_keep_list_for_nand, fixup_dpi_setting, fixup_recovery_fstab,update_overlays,update_patchsets,do_concat_files, _project_custom_gen_project_dimension,get_resolution_from_dimension,_get_project_wallpaper_dir,update_geocoding_db,update_apns_from_db,remove_defalut_wallpaper_from_chooser,get_all_project_info
#_project_custom_exists_any,_project_custom_get_fallback2,fallback_rules_len,project_custom_build_fallback_list,get_project_name,get_project_ui
import commands
from dateutil import parser
import glob
import re
import shutil
import filecmp
import subprocess
import datetime
import errno
from git import git_get_last_author, git_get_last_date
import termcolor
from termcolor import *
from const import *

def npn_vanzo(project):
    return npn(project)
def get_project_info_vanzo(project_name):
    return get_project_info(project_name)
def my_sys_vanzo(cmd):
    return my_sys(cmd)
def my_dbg(msg, logit=False):
    print(msg)
    if logit:
        my_log(msg)
def mkdir_p_vanzo(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno != errno.EEXIST or not os.path.isdir(path):
            raise
def my_dbg_vanzo(msg,level=LEVEL_DBG,logit=False):
    if level >= LEVEL_WARNING:
        return my_dbg(termcolor.red(msg),logit)
    elif level == LEVEL_IMPORTANT:
        return my_dbg(termcolor.yellow(msg),logit)
    elif level == LEVEL_HINT:
        return my_dbg(termcolor.cyan(msg),logit)
    elif DEBUG_LOG == 1:
        return my_dbg(msg,logit)


def normalize_cwd_vanzo(dir):
    return normalize_cwd(dir)
def project_custom_get_fallback_file_vanzo(project_name,input_file):
    project_name=project_name.lower().strip()
    #project_name=npn_vanzo(project_name)
    project_list = do_get_fallback_project_list(project_name) #need rewrite
    #print "the project_list is %s,fallback_file is  %s"%(project_list,fallback_file)
    index=input_file.rfind(".overlay.")
    if index<0:
        index=input_file.rfind(".patchset.")
        if index>=0:
            index+=len(".patchset.")
        else:
            index=len(input_file)
    else:
        index+=len(".overlay.")
    fallback_file=input_file[:index]
    #print "fallback_file:",fallback_file
    for item in project_list:
        path=fallback_file+item
        path=os.path.realpath(path)
        if os.path.exists(path):
            return path
            
def get_project_ui_vanzo(project_name):
    return get_project_ui(project_name)


def fixup_project_storage_vanzo(platform_config,custom_config):
    list_config = []
    value="no"
    if custom_config!=None and  os.path.exists(custom_config):
        with open(custom_config) as inF:
            #list_config.extend(inF.readlines())
            list_content=inF.readlines()
            list_content.reverse()
            list_config.extend(list_content)

    global_backup = "%s.global2" % platform_config
    if os.path.exists(global_backup):
        with open(global_backup) as inF:
            #list_config.extend(inF.readlines())
            list_content=inF.readlines()
            list_content.reverse()
            list_config.extend(list_content)

    global_config = "%s.global" % platform_config
    if os.path.exists(global_config):
        with open(global_config) as inF:
            #list_config.extend(inF.readlines())
            list_content=inF.readlines()
            list_content.reverse()
            list_config.extend(list_content)

    if platform_config != None and os.path.exists(platform_config):
        with open(platform_config) as inF:
            #list_config.extend(inF.readlines())
            list_content=inF.readlines()
            list_content.reverse()
            list_config.extend(list_content)

    for line in list_config:
        if "MTK_EMMC_SUPPORT" in line:
            list_item = line.split("=")
            if len(list_item) != 2:
                continue
            key = list_item[0].strip()
            value = list_item[1].strip()
            if "MTK_EMMC_SUPPORT" == key:
                break
    return value
def git_get_author_date_vanzo(filename):
    cwd=os.getcwd()
    os.chdir(os.path.dirname(filename))
    basename = os.path.basename(filename)
    try:
        author=git_get_last_author(basename)
        last_date=git_get_last_date(basename)
        os.chdir(cwd)
        return author,last_date
    except:
        os.chdir(cwd)
        return 'unknown', 'unknown'
#for compatible with old affects show format
class Apply_vanzo(object):
    
    def __init__(self):
        self.name = None
        self.conflict = False


class Patchset_vanzo(object):

    def __init__(self):
        self.name = None
        self.date = None
        self.author = None
        self.applies = []


class Overlay_vanzo(object):
    
    def __init__(self):
        self.name = None
        self.date = None
        self.author = None


class Project_vanzo(object):

    def __init__(self):
        self.name = None
        self.patchsets = []
        self.overlays = []

def _parse_argv_vanzo(para):
    if len(para) != 4:
        print('{0} project_name <--alpha|--apply|--time|--rtime> <--parsable|--nonparsable>'.format(
                white(os.path.basename(para[0]))))
    return para[1], para[2], para[3]

def patch_applies_vanzo(patch):
    if patch.endswith('.keep') or patch.endswith('.delete'):
        return []

    applied_files = []
    #print "the patch is %s"%(patch)

    if not os.path.exists(patch):
        return []
    for line in [x.rstrip() for x in open(patch) if x.strip()]:
        apply_ = Apply_vanzo()
        tokens = line.split()
        try:
            if tokens[0] != 'diff' or len(tokens) < 4:
                continue
            if tokens[2].partition('/')[2] != tokens[3].partition('/')[2]:
                apply_.name = '*'
            else:
                apply_.name = tokens[2].partition('/')[2]
        except IndexError:
            apply_.name = '*'
        applied_files.append(apply_)
    return applied_files

def Parse_patch_applies_vanzo(patchsets=[]):
    pathset = dict()
    for x in patchsets:
        dir_name = os.path.dirname(x.name)
        for y in x.applies:
            path = os.path.join(dir_name, y.name)
            pathset[path] = pathset.get(path, 0) + 1
    for x in patchsets:
        dir_name = os.path.dirname(x.name)
        for y in x.applies:
            path = os.path.join(dir_name, y.name)
            if pathset[path] > 1:
                y.conflict = True

def Print_header_vanzo(title, ch):
    print(white(ch*80))
    print('{0:^80}'.format(title))
    print(white(ch*80))


def Print_top_header_vanzo(title):
    Print_header_vanzo(title, '=')


def Print_sub_header_vanzo(title):
    Print_header_vanzo(title, '-')


def Print_overlay_header_vanzo():
    Print_sub_header_vanzo(' overlay ')


def Print_patchset_header_vanzo():
    Print_sub_header_vanzo(' patchset ')


def _sort_patches(patches, sort):
    if sort in ('--time', '--rtime'):
        patches = sorted(patches, key=lambda d : d.date,
                         reverse = (sort=='--rtime'))
    elif sort == '--apply':
        pass
    else:
        patches = sorted(patches, key=lambda d : d.name)
    return patches


def Print_patch_git_info_vanzo(project_name, patch, sep):
    tokens = os.path.basename(patch.name).partition(sep)
    color_deco = magenta if tokens[2].split('.')[0] == npn(project_name) else cyan
    print(os.path.dirname(patch.name) + os.sep + green(tokens[0]) + tokens[1] + color_deco(tokens[2]))
    print('{0:>25}{1:>40}'.format(yellow(patch.author), blue(patch.date)))


def Print_patch_git_info_parsable_vanzo(project, patch, sep):
    print('{0} {1} {2}'.format(patch.name, patch.author, patch.date))


def Print_overlays_vanzo(project_name,overlays, sort):
    for overlay in _sort_patches(overlays, sort):
        Print_patch_git_info_vanzo(project_name, overlay, OVERLAY_KEY2)


def Print_patch_applies_vanzo(patch):
    for x in patch.applies:
        if x.name == '*':
            print('    > ...')
        elif x.conflict:
            print('    ' + red('>') + ' ' + red(x.name))
        else:
            print('    > ' + x.name)


def Print_patchsets_vanzo(project_name,patchsets, sort):
    for patchset in _sort_patches(patchsets, sort):
        Print_patch_git_info_vanzo(project_name, patchset, PATCHSET_KEY2)
        if patchset.name.endswith('.delete') or patchset.name.endswith('.keep'):
            continue
        Print_patch_applies_vanzo(patchset)


def Print_project_vanzo(project,sort="--alpha"):
    #print "the project.name is %s"%(project.name)
    Print_top_header_vanzo(project.name)
    Print_patchset_header_vanzo()
    Print_patchsets_vanzo(project.name,project.patchsets, sort)
    Print_overlay_header_vanzo()
    Print_overlays_vanzo(project.name,project.overlays, sort)

def remove_other_res_vanzo(project):
    return remove_other_res(project)
def remove_other_res2_vanzo(project):
    return remove_other_res2(project)
def remove_redundant_wallpapers_vanzo(project):
    return remove_redundant_wallpapers(project)
def get_root(file_name):
    from vanzo_worker import VanzoWorker
    worker=VanzoWorker() 
    file_path=worker.VANZO_PREFIX+file_name
    return file_path
def get_wallpaper_list_from_wallpaper_xml(xml):
    wallpapers = []
    with open(xml) as txt:
        for line in txt:
            m = re.match(r'^\s*<item>\s*(.+)\s*</item>\s*$', line)
            if m:
                wallpapers.append(m.group(1))
    return wallpapers
def replace_default_wallpaper_vanzo(project_name):
    # 23 does not have uniformed WallpaperChooser path, it is
    # difficult to find out which drawable folder it is using
    project_info = get_project_info_vanzo(project_name)
    if project_info['android'] == '23':
        return

    if project_name.startswith("mt72ali_") or project_name.startswith("mt82ali_"):
        return

    wallpaper_dir = os.path.join(_get_project_wallpaper_dir(project_name), 'res')
    # some repo does not have WallpaperChooser, cmcc etc
    #print "the wallpaper_dir is %s"%(wallpaper_dir)
    if not os.path.exists(wallpaper_dir):
        return

    dimension = _project_custom_gen_project_dimension(project_name)
    res = get_resolution_from_dimension(dimension, project_info)

    #customized = project_custom_get_fallback_file_vanzo(project_name,'%s/frameworks/base/core/res/res/drawable-%s/default_wallpaper.jpg.overlay.%s' % (gOverlayRootRO, res, npn(project_name)))
    overlay_root=get_root("overlay_projects")
    customized = project_custom_get_fallback_file_vanzo(project_name,'%s/frameworks/base/core/res/res/drawable-%s/default_wallpaper.jpg.overlay.' % (overlay_root, res))
    #print "the customized is %s"%(customized)
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

#from vanzo
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
def add_policy(map_in, key, map_out):
    if not map_in.has_key(key):
        return
    assert map_in.has_key(key)
    map_new =  map_in[key]
    for one in map_new:
        if map_out.has_key(one):
            if map_new[one] != 0:
                map_out[one] = map_new[one]
        else:
            map_out[one] = map_new[one]
def _get_change_time(file1):
    cmd1 = "cd " + file1[:file1.rfind("/")] + "; git log " + file1[file1.rfind("/")+1:]
    list1 = commands.getstatusoutput(cmd1)[1].split("\n")
    if len(list1) < 3:
        return
    for one in list1:
        if one.startswith("Date:"):
            line2 = one[5:].strip()[:-5]
            return parser.parse(line2)
def load_policies(project_name):

    change_time1 = _get_change_time(".repo/manifests/%s.xml" % project_name)
    list1 = glob.glob("recommend_apks/phistory*.txt")
    list_files  = []
    for one in list1:
        list2 = one.split("-")
        time1 = datetime.datetime(int(list2[1]), int(list2[2]), int(list2[3]), int(list2[4]), int(list2[5]), int(list2[6]))
        list_files.append([time1, one])
    list_files.sort(lambda one,two: cmp(one[0], two[0]))
    file1 = "./recommend_apks/policy.txt"
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
def _token_in_project(project, token):
    return project.endswith('_' + token) or '_' + token + '_' in project

def _is_mul(project):
    return project.endswith('_mul') or '_mul_' in project

def _is_cta(project):
    return _token_in_project(project, 'cta')

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

def my_split(str1, splitter=","):
    """
    split always return one element even if you give it empty str,we don't need it
    """
    return [one for one in str1.split(splitter) if len(one.strip()) > 0]

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
        elif place1 == 0:
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
def _load_apks(project_name):
    wvga = True
    from vanzo_worker import VanzoWorker
    worker=VanzoWorker() 
    config_name=worker.project_custom_config_fallback(project_name)
    dimension = get_dimension_from_project_config(config_name)
    if dimension != None and dimension[0] * dimension[1] < 800 * 480:
        wvga = False

    change_time1 = _get_change_time(".repo/manifests/%s.xml" % project_name)
    list1 = glob.glob("recommend_apks/history*.txt")
    list_files  = []
    for one in list1:
        list2 = one.split("-")
        time1 = datetime.datetime(int(list2[1]), int(list2[2]), int(list2[3]), int(list2[4]), int(list2[5]), int(list2[6]))
        list_files.append([time1, one])
    list_files.sort(lambda one,two: cmp(one[0], two[0]))
    file1 = "recommend_apks/current.txt"
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

def apply_policy(map2, project_name, project_info):

    #print "enter apply_policy,project_name %s"%(project_name)
    dir1 = "vendor/google/3rdapp/custom"
    if not os.path.exists(dir1):
        os.makedirs(dir1)

    dir2 = "vendor/google/userdata/custom"
    if not os.path.exists(dir2):
        os.makedirs(dir2)

    if "_mul" in project_name:
        return

    list1 = glob.glob("%s/*.apk" % dir1)
    list1.extend(glob.glob("%s/*.apk" % dir2))
    list_current_apks = []
    for one in list1:
        list_current_apks.append(os.path.basename(one).replace(".apk",""))

    #print "map2 freeze %d"%(map2["Freeze"])
    if map2["Freeze"] != 1:
        list1 = _load_apks(project_name)
        #print "after _load_apks list1 %s"%(list1)
        #list1 = _filter_apks_by_conflict(list1, list_current_apks)
        list1 = _filter_apks_by_accept(list1, map2)
        #print "after _filter_apks_by_accept list1 %s"%(list1)
        if list1 == None:
            return
        (list_system, list_userdata) = _get_by_placement(list1, map2["Placement"])
        print "recommend apks: %s" % list_system
        print "recommend apks: %s" % list_userdata
        for one in list_system:
            my_sys("cp -f %s %s" % (one, dir1))
        for one in list_userdata:
            my_sys("cp -f %s %s" % (one, dir2))

    if map2["Autoupdate"] != 2:
        list1 = glob.glob("recommend_apks/autoupdate/*.apk")
        for one in list1:
            my_sys("cp -f %s %s" % (one, dir1))
        for one in ("native_svc", "upgraded"):
            cmd1 = "cp -a ./recommend_apks/autoupdate/%s vendor/mediatek/%s/artifacts/out/target/product/%s/system/bin" % (one, project_info["project"], project_info["project"])
            my_sys(cmd1)

        cmd1 = "grep upgraded mediatek/config/%s/init.rc" % project_info["id"][:6]
        ret2 = commands.getstatusoutput(cmd1)[0]
        if ret2 != 0:
            cmd1 = "echo '# Vanzo:chenjingcheng on: Wed, 27 Jun 2012 21:07:35 +0800\n service upgraded /system/bin/upgraded\n user root\n class main\n socket upgraded stream 777 root root\n# End of Vanzo:chenjingcheng\n' >> mediatek/config/%s/init.rc" % project_info["id"][:6]
            my_sys(cmd1)

def do_get_fallback_project_list(project_name):
    from vanzo_worker import VanzoWorker
    worker=VanzoWorker() 
    list_ancestor=worker.list_relatives(project_name,KIND_PARENT,True)
    full_list=[]
    for item in list_ancestor:
        full_list.append(item)
        full_list.append(item+".delete")
        full_list.append(item+".keep")
    
    long_name=worker.npn_to_long_project(project_name)
    special_list=worker.get_project_special_fallback_str(long_name)
    special_list.reverse()
    full_list.reverse()
    full_list.extend(special_list)
    return full_list
    
def do_add_recommended_apks_vanzo(project_name):
    #print "enter do_add_recommended_apks_vanzo"
    project_info = get_project_info_vanzo(project_name)
    if not os.path.exists("../../recommend_apks"):
        my_sys("cd ../..;git clone vanzo:tools/recommend_apks.git")
    else:
        my_sys("cd ../../recommend_apks;git clean -fd;git checkout . > /dev/null; git pull > /dev/null")
    my_sys("ln -sf ../../recommend_apks .")

    if _is_cta(project_name):
        return

    if "_cphone" in project_name:
        return

    if "ali_" in project_name[:8]:
        return

    if "mt15cmcc" in project_name:
        return

    if "_twog" in project_name:
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
    project_list = do_get_fallback_project_list(project_name) #need rewrite
    fallback_project=""
    for item in project_list:
        if map1.has_key(item):
            fallback_project=item
            break

    print "the fallback_project is %s"%(fallback_project)
    add_policy(map1, fallback_project, map2)

    apply_policy(map2, project_name, project_info)

    do_add_aphone_apks(project_name)


def remove_some_apks_for_mul_vanzo(project_name):
    return remove_some_apks_for_mul(project_name)
def duplicated_apk_check_vanzo():
    return _duplicated_apk_check()
def replace_default_site_nav_vanzo(project_name):
    return _replace_default_site_nav(project_name)
def gen_so_from_apk_vanzo(project):
    return gen_so_from_apk(project)
def remove_redudant_google_libs_vanzo():
    return remove_redudant_google_libs()
def do_add_watermark_vanzo(project_info):
    return _do_add_watermark(project_info)
def add_keep_list_for_nand_vanzo(project_name):
    return _add_keep_list_for_nand(project_name)
def fixup_dpi_setting_vanzo(project_info):
    return fixup_dpi_setting(project_info)
def fixup_recovery_fstab_vanzo(project_info):
    return fixup_recovery_fstab(project_info)
def normalize_size(size1):
    return int(size1[0]), int(size1[1])
def get_image_format_from_size(size1, project_name):
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
        if any(id_.startswith(i) for i in ('mt6589', 'mt6572jb3', 'mt6582')):
            ret1 = "hd720"
        else:
            ret1 = "hd"
    elif size2 == (240, 320):
        ret1 =  "qvga"
    elif size2 == (1080, 1920):
        ret1 =  "fhd"
    if id_.startswith('mt6572') and ('_td_' in project_name or project_name.endswith('_td')):
        ret1 = 'cmcc_' + ret1
    return ret1
def adjust_project_folders_for_vphone_vanzo(project_name,project_info):
    if not _is_vphone(project_name):
        return

    project = project_info["project"]
    one = "mediatek/config/%s/ProjectConfig.mk" % project
    from vanzo_worker import VanzoWorker
    worker=VanzoWorker() 
    two=worker.project_custom_config_fallback(project_name)
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

def _get_project_buildinfo(map1, one):
    list1 = [one]
    while len(list1) > 0:
        two = list1.pop(0)
        for onerule in fallback_rules_keys:
            if _does_fallback_rule_match(onerule, two):
                three = two.replace(onerule, fallback_rules_maps_vanzo[onerule])
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

    project_list = do_get_fallback_project_list(project_name) #need rewrite
    for item in project_list:
        if map1.has_key(item):
            return map1[item]

def update_buildinfo_vanzo(project_name,project_info):
    ret = my_sys("cd build/; git status | grep buildinfo")
    if ret == 0:
        return False

    list1 = project_name.split("_")
    device = list1[1].upper()
    model = list1[2].upper()
    manufaturer = list1[3].upper()
    display = model
    notshowdate = False

    file1 = get_root("overlay_projects/build/tools/buildinfo.custom")
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

def xphone_filter_out_vtrunk_patchset_vanzo(npn_project, patchset):
    def _xphone_needs_filter_out(dir_name, ui):
        return os.path.exists(dir_name + '/no_vtrunk_patch_for_' + ui) or \
            os.path.exists(dir_name + '/no_vtrunk_patch_for_xphone')

    xphones = ('aphone', 'ephone', 'vphone', 'tphone')
    for suffix in ('_' + x for x in xphones):
        if patchset.endswith(suffix):
            return patchset
        if patchset.endswith(suffix+".keep"):
            return patchset
        if patchset.endswith(suffix+".delete"):
            return patchset

    dir_name = os.path.dirname(patchset)

    for suffix in xphones:
        if globals()['_is_' + suffix](npn_project):
            if _xphone_needs_filter_out(dir_name, suffix):
                return None
    return patchset


def remove_google_apps_from_non_mul_projects_vanzo(project_name,project_info):
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
    app_mk = '{0}/vendor/google/app/Android.mk.overlay.'.format(get_root("overlay_projects"))
    if project_custom_get_fallback_file_vanzo(project_name,app_mk):
        return
    else:
        app_mk = '{0}/vendor/google/app/Android.mk.overlay.{1}'.format(get_root("overlay_projects"), npn(project_name))


    mkdir_p_vanzo(os.path.dirname(app_mk))
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


def remove_defalut_wallpaper_from_chooser_vanzo(project_name):
    return remove_defalut_wallpaper_from_chooser(project_name)
def do_pre_ugly_things_vanzo(project_name,project_info):
    adjust_project_folders_for_vphone_vanzo(project_name, project_info)
    update_buildinfo_vanzo(project_name,project_info)
    remove_google_apps_from_non_mul_projects_vanzo(project_name, project_info)

def do_post_ugly_things_vanzo(project_name,project_info):
    if project_info["id"] in ("mt6573v3", "mt6513r4",):
        remove_other_res_vanzo(project_info["project"])
    else:
        remove_other_res2_vanzo(project_info["project"])

    remove_redundant_wallpapers_vanzo(project_name)
    update_geocoding_db_vanzo(project_name,project_info)
    if "cmcc" not in project_name and "cmcc" not in project_info["project"]:
        update_apns_from_db_vanzo(project_info)
    replace_default_wallpaper_vanzo(project_name)
    remove_defalut_wallpaper_from_chooser_vanzo(project_name)
    do_add_recommended_apks_vanzo(project_name)
    remove_some_apks_for_mul_vanzo(project_name)
    duplicated_apk_check_vanzo()
    replace_default_site_nav_vanzo(project_name)
    gen_so_from_apk_vanzo(project_info["project"])
    remove_redudant_google_libs_vanzo()
    do_add_watermark_vanzo(project_info)
    add_keep_list_for_nand_vanzo(project_name)

    if project_info["age"] >=  PROJECT_INFO["mt6582kk"]["age"]:
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

    fixup_dpi_setting_vanzo(project_info)
    fixup_recovery_fstab_vanzo(project_info)
    
    #for makeMtk need this file
    dst_path="build/tools/update_overlay_files.py"
    if not os.path.exists(dst_path):
        if os.path.exists("./update_overlay_files"):
            shutil.copy('./update_overlay_files',dst_path)
        else:
            src_path=os.path.expanduser('~')+"/build_projects/scripts/update_overlay_files.py"
            if os.path.exists(src_path):
                shutil.copy(src_path,dst_path)
def do_concat_files_vanzo(project_name):
    return do_concat_files(project_name)
def update_patchsets_vanzo(project_patchsets, project,get_result=False):
    if get_result == False:
        return update_patchsets(project_patchsets,project)
    #here to get the result
    for one in project_patchsets:
        if os.path.exists(one[1] + ".keep"):
            continue
        elif os.path.getsize(one[1]) < 10:
            continue
        elif not os.path.exists(one[0]):
            continue
        else:
            cmd = "cd " + one[0] + "; patch -p1 < " + one[1]
            if commands.getstatusoutput(cmd)[0]:
                pos1 = one[1].find("patch_projects")
                cmd2 = "cd %s;git log --pretty=%%aN:%%ad -1 --date='iso' %s" % (one[1][:pos1], one[1][pos1:])
                msg2 = commands.getstatusoutput(cmd2)[1][:-6]
                msg1 = "Error! %s, %s" % (one[1][pos1:], msg2)
                my_dbg(termcolor.red(msg1))
                return False
            else:
                cmd = "cd " + one[0] + "; find . -name '*.orig' -type f | xargs rm -rf"
                my_sys(cmd)
    return True
def update_overlays_vanzo(project_overlays):
    return update_overlays(project_overlays)
def do_concat_files_vanzo(project_name):
    return do_concat_files(project_name)
def update_geocoding_db_vanzo(project_name,project_info):
    return update_geocoding_db(project_name,project_info)
def update_apns_from_db_vanzo(project_info):
    return update_apns_from_db(project_info)
fallback_rules_maps_vanzo = { "_dev":"", "_v3":"", "_r4":"", "_ics":"", "_kk":"", "_jb7":"", "_jb9":"", "_tdd":"", "_lte":"", "_ds5":"","_ds3":"","_ds":"", "_jb5":"", "_jb3":"", "_jb2":"", "_jb":"", "_mul":"", "_twog":"", "_cta":"",
# Vanzo:yucheng on: Sun, 19 Jan 2014 15:17:13 +0800
# Added for freezed projects
    "_freeze":"",
# End of Vanzo: yucheng
    "_aphone":"", "_ephone":"", "_sphone":"", "_vphone":"", "_tphone":"", "_cphone":"","_ophone":"",
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

