#!/usr/bin/env python
import commands
import sys
import os
import shutil
import copy
from const import *
from tree import Tree
from node import Node
from mtk_worker import MTKWorker
import json
import shlex
import time
import re
import traceback
#traceback.print_stack()

#from bridge import npn_vanzo, get_project_info_vanzo,my_sys_vanzo,my_dbg_vanzo
from bridge import *

class VanzoWorker(MTKWorker):
    def __init__(self,project_name="",force=True):
        MTKWorker.__init__(self,project_name,force)
        self.VANZO_PREFIX="vendor/vanzo_custom/"
        self.tool_dir="/git/vanzo_team/wangfei/python_tools/"
        self.parent_path="parent_dir/"
        self.modified_project=[]
        self.exclude_target=[]
        self.exclude_regex=[]
        self.exclude_custom=[]
        self.fallback_tree=None
        self.ugly_internal_fallback_tree=None
        self.dict_patch_overlay={}
        self.all_projects_list=[]
        self.use_cache=False
        self.current_long_project=""
        self.recent_project_list=None
        self.status_list=[]
        self.npn_to_long_dict={}
        self.care_list=[".py",".java",".xml",".mp3",".ogg",".cpp",".c",".mk",".h"]
    def to_root_dir(self,root_dir=None):
        cwd=os.getcwd()
        '''
        for new custom tool we must add this to adapt
        '''
        if root_dir!=None:
            self.VANZO_PREFIX=os.path.abspath(root_dir)+"/"
            os.chdir(self.VANZO_PREFIX)
            self.set_force(True)
            return cwd

        fallback_file=os.path.join(self.VANZO_PREFIX,"fallback_extra.txt")
        #print "self.VANZO_PREFIX:",self.VANZO_PREFIX
        result=""
        if os.path.exists(fallback_file):
            #self.VANZO_PREFIX=os.path.join(os.getcwd(),self.VANZO_PREFIX)
            if not self.VANZO_PREFIX.startswith("/"):
                self.VANZO_PREFIX=os.path.join(os.getcwd(),self.VANZO_PREFIX)
            result=cwd
        root_file=".repo"
        while not os.path.exists(root_file) or not os.path.exists(fallback_file):
            os.chdir("../")
            if os.getcwd() == "/":
                os.chdir(cwd)
                if result!="":
                    self.set_force(True)
                    return result
                root_dir = self.find_root_dir()
                if root_dir =="":
                    return ""
                else:
                    os.chdir(root_dir)
                    #self.VANZO_PREFIX=os.path.join(root_dir,"/")
                    self.VANZO_PREFIX=root_dir+"/"
                    #print "self.VANZO_PREFIX:",self.VANZO_PREFIX
                    self.set_force(True)
                    return os.getcwd()
        #self.VANZO_PREFIX=os.getcwd()+"/"+self.VANZO_PREFIX
        self.VANZO_PREFIX=os.path.join(os.getcwd(),self.VANZO_PREFIX)
        #print "self.VANZO_PREFIX:",self.VANZO_PREFIX
        return cwd

    def read_all_projects(self):
        dailybuild_list=os.path.expanduser('~')+"/build_projects/scripts/dailybuild_all_projects.txt"
        if not os.path.exists(dailybuild_list):
            my_dbg_vanzo("Warning!Can not find the dailybuild_all_projects!",LEVEL_WARNING)
            return []
        with open(dailybuild_list) as in_file:
            lines = in_file.readlines()
            for item in lines:
                item=item.lower().strip()
                if item not in self.all_projects_list:
                    self.all_projects_list.append(item)
        list_old_file = glob.glob(os.path.expanduser('~')+"/build_projects/scripts/deprecated*.txt")
        for deprecated_file in list_old_file:
            with open(deprecated_file) as in_file:
                lines = in_file.readlines()
                for item in lines:
                    item=item.lower().strip()
                    if item not in self.all_projects_list:
                        self.all_projects_list.append(item)

        return self.all_projects_list
    def exist_project(self,project_name):
        if len(self.all_projects_list)<= 0:
            self.read_all_projects()
        
        npn_name=npn_vanzo(project_name)
        for item in self.all_projects_list:
            if npn_name==npn_vanzo(item):
                return True
            
        return False

    def get_repo_from_id(self,id_name):
        project_info_map=get_all_project_info()
        for key,value in project_info_map.items():
            if value["id"] == id_name:
                return value["repo"]
    def get_platform_project(self,long_list):
        #print "long_list:",long_list
        repo_name=None
        if not self.current_project or len(self.current_project)<1:
            self.current_project=self.get_current_prj()
        if self.current_project == None:
            #my_dbg_vanzo("this is in custom tool case,we use ugly way to guess platform",LEVEL_WARNING)
            cwd=os.getcwd()
            path_list=cwd.split("/")
            '''
            for path in path_list:
                segs_list=path.split("_")
                for seg in segs_list:
                    if seg.startswith("mt"):
                        repo_name=self.get_repo_from_id(seg)
                        break
            '''
            for path in path_list:
                segs_list=path.split("_")
                for seg in segs_list:
                    if seg.startswith("platfrom"):
                        repo_name=seg
                        break
        else:
            project_info = get_project_info_vanzo(self.current_project.strip().lower())
            if project_info:
                repo_name=project_info["repo"]
        #print "repo_name:",repo_name
        if not repo_name:
            my_dbg_vanzo("Error,sorry I cannot guess the platform of current project!")
            return None
        #print "long_list:",long_list
        for project in long_list:
            project_info = get_project_info_vanzo(project)
            if project_info["repo"] == repo_name:
                #fixme for sometimes there still has more resutls,but I just ignore
                return project 
                    
                
    def npn_to_long_project(self,npn_name,ignore=False):
        if not npn_name:
            return ""
        npn_name=npn_name.strip()
        long_list=[]
        if npn_name in self.npn_to_long_dict:
            long_list=self.npn_to_long_dict[npn_name]
            if ignore or (len(long_list)==1):
                return long_list[0]
            long_name=self.get_platform_project(long_list)
            if not long_name:
                return npn_name
        if len(self.all_projects_list)<= 0:
            self.read_all_projects()
        
        for item in self.all_projects_list:
            if npn_name==npn_vanzo(item):
                long_list.append(item)
                #self.npn_to_long_dict[npn_name]=item
                #return item
        long_name=npn_name
        if len(long_list)<1:
            self.npn_to_long_dict[npn_name]=[long_name]
        else:
            if ignore:
                return long_list[0]
            self.npn_to_long_dict[npn_name]=long_list
            if (len(long_list)==1):
                return long_list[0]
            long_name=self.get_platform_project(long_list)
        if not long_name:
            return npn_name
        return long_name

    def dump_project_parent(self,project_name,parent_map={}):
        if parent_map == None or len(parent_map) < 1:
            return
        path=os.path.expanduser('~')+self.tool_dir+self.parent_path
        path=path.strip()
        if not os.path.exists(path):
            my_sys_vanzo("mkdir -p " + path)
        path=path+project_name
        path=path.strip()
        with open(path,"w+") as outb:
            json.dump(parent_map,outb)
            outb.close()
            

    def load_project_parent(self,project_name,quiet=False):
        path=os.path.expanduser('~')+self.tool_dir+self.parent_path+project_name
        path=path.strip()
        parent_dict={} 
        if os.path.exists(path):
            inf=open(path,"r").read().decode('utf-8')
            parent_dict=json.loads(inf)
        else:
            return None
        for key,value in parent_dict.items():
            parent_list=parent_dict[key]
            if quiet == False:
                for item in parent_list:
                    my_dbg_vanzo(item,LEVEL_IMPORTANT)
            return parent_list
        return None
         
    def project_bsp_config_fallback(self,project_name,project_info=None):
        if not project_info:
            project_info = self.get_project_info(project_name)
            if not project_info:
                return
        bsp = "%soverlay_projects/mediatek/config/%s/ProjectConfig.mk.bsp.overlay." % (self.VANZO_PREFIX, project_info["project"])
        list_ancestor=self.list_relatives(project_name,KIND_PARENT,True)
        list_ancestor.reverse()
        for item in list_ancestor:
            item=bsp+item
            if os.path.exists(item):
                return item

    def project_custom_config_fallback(self,project_name):
        project_info = self.get_project_info(project_name)
        if not project_info:
            return
        bsp = "%soverlay_projects/mediatek/config/%s/ProjectConfig.mk.bsp.overlay." % (self.VANZO_PREFIX, project_info["project"])
        if project_info["age"] >=  PROJECT_INFO["mt6572jb3"]["age"]:
            bsp = bsp.replace(".bsp", ".custom")
        list_ancestor=self.list_relatives(project_name,KIND_PARENT,True)
        list_ancestor.reverse()
        for item in list_ancestor:
            item=bsp+item
            if os.path.exists(item):
                return item
        
    def create_fallback_tree(self):
        fallback_file=os.path.join(self.VANZO_PREFIX,"fallback_extra.txt")
        #print "fallback_file:",fallback_file
        self.fallback_tree = Tree()
        self.fallback_tree.create_node("root", "root")  # root node
        with open(fallback_file) as in_file:
            lines = in_file.readlines()
            for item in lines:
                pair=item.split(":")
                if not self.fallback_tree.contains(pair[1].strip()):
                    self.fallback_tree.create_node(pair[1].strip(),pair[1].strip(),parent="root")
                if not self.fallback_tree.contains(pair[0].strip()):
                    self.fallback_tree.create_node(pair[0].strip(),pair[0].strip(),parent=pair[1].strip())
                else:
                    self.fallback_tree.move_node(pair[0].strip(),pair[1].strip())
        return self.fallback_tree
    def create_ugly_internal_rules_tree(self):
        self.ugly_internal_fallback_tree = Tree()
        self.ugly_internal_fallback_tree.create_node("root", "root")  # root node
        for key,value in fallback_rules_maps_vanzo.items():
            if value == "":
                value="self"
            if not self.ugly_internal_fallback_tree.contains(value.strip()):
                self.ugly_internal_fallback_tree.create_node(value.strip(),value.strip(),parent="root")
            if not self.ugly_internal_fallback_tree.contains(key.strip()):
                self.ugly_internal_fallback_tree.create_node(key.strip(),key.strip(),parent=value.strip())
            else:
                self.ugly_internal_fallback_tree.move_node(key.strip(),value.strip())
        return self.ugly_internal_fallback_tree
    def get_exclude_target_list(self,project_name):
        try:
            project_info = self.get_project_info(project_name)
            if not project_info:
                return []
            custom_name=project_info["project"]
            cmd="cd %soverlay_projects/mediatek/custom;ls -d vanzo* | grep -v %s;cd ->/dev/null"%(self.VANZO_PREFIX,custom_name)
            excludes= commands.getstatusoutput(cmd)[1].split()
            return excludes
        except Exception, e:
            #my_dbg_vanzo("Error,please check the project_name %s"%(project_name),LEVEL_ERROR)
            #my_dbg_vanzo(e)
            return []
        
    def get_project_info(self,npn_project_name,quiet=True):
        if npn_project_name == None:
            npn_project_name = self.get_current_prj()
        else:
            npn_project_name=npn_project_name.strip()
            if len(npn_project_name) < 1:
                npn_project_name = self.get_current_prj()
        project_name=self.npn_to_long_project(npn_project_name)
        project_info = get_project_info_vanzo(project_name.strip().lower()) #origin place
        if not project_info:
            my_dbg_vanzo("Error get_project_info error!",LEVEL_ERROR)
            return None
        if project_info["storage"] == "unknown":
            custom_config=self.project_bsp_config_fallback(project_name,project_info)
            platform_config = "mediatek/config/%s/ProjectConfig.mk" % project_info["project"]
            if os.path.exists(platform_config):
                emmc_config=fixup_project_storage_vanzo(platform_config, custom_config)
                if "no" == emmc_config:
                    project_info["storage"] = "nand"
                elif "yes" == emmc_config:
                    project_info["storage"] = "emmc"
        if quiet==False:
            my_dbg_vanzo("project_info of %s : %s"%(project_name,project_info),LEVEL_IMPORTANT)
        return project_info

    def get_custom_exclude_list(self):
        return self.exclude_custom[:]
    '''
    deprecated
    '''
    def list_po_file(self,name,project_name,exclude_target=[],result_dict={}):
        excludes=""
        for item in exclude_target:
            excludes=excludes+"-name *%s* -prune -o "%(item)
        cmd="find %s %s -name .repo -prune -o -name .git -prune  -o -regextype posix-egrep -iregex '(%s)'  -print"%(self.VANZO_PREFIX,excludes,name)
        list_file = commands.getstatusoutput(cmd)[1].split()
        try:
            for item in list_file:
                key=item.replace(self.VANZO_PREFIX+"patch_projects/","").replace(self.VANZO_PREFIX+"overlay_projects/","")
                suffix_index=key.rfind(".overlay.")
                if suffix_index >= 0:
                    key=key[:suffix_index]
                else:
                    suffix_index=key.rfind(".patchset.")  
                    if suffix_index >= 0:
                        key=key[:suffix_index]
                result_dict[key]=item
        except Exception, e:
            my_dbg_vanzo(e)
            sys.exit()
        
        return result_dict

    def get_match_files(self,match_list,dirname,filename):
        #print "the dirname is %s,filename %s"%(dirname,filename)
        #print "self.exclude_target:",self.exclude_target
        for excludes in self.exclude_target:
            for item in filename[:]:
                if item==excludes:
                    filename.remove(item)
        for regex in self.exclude_regex:
            for item in filename[:]:
                if re.search(regex,item):
                    filename.remove(item)
        len_matchs=len(match_list)
        for item in filename[:]:
            for i in xrange(0,len_matchs):
                if item.endswith(match_list[i]):
                    #work_item=dirname+item
                    #print "item:",item
                    work_item=os.path.join(dirname,item)
                    work_item=work_item.replace("//","/")
                    key=work_item.replace(self.VANZO_PREFIX+"patch_projects/","").replace(self.VANZO_PREFIX+"overlay_projects/","")
                    #key=work_item.replace("./patch_projects/","").replace("./overlay_projects/","")
                    suffix_index=key.rfind(".overlay.")
                    if suffix_index >= 0:
                        key=key[:suffix_index]
                    else:
                        suffix_index=key.rfind(".patchset.")  
                        if suffix_index >= 0:
                            key=key[:suffix_index]
                    if suffix_index < 0:
                        continue
                    if xphone_filter_out_vtrunk_patchset_vanzo(npn_vanzo(self.long_project_name),work_item) == None:
                        continue 
                    #print "find item %s endswith %s,value work_item %s"%(item,match_list[i],work_item)
                    #for vanzo old interface use the absolute path
                    work_item=work_item.replace(self.VANZO_PREFIX,"")
                    self.dict_patch_overlay[key+"$%d"%(i)]=work_item
                    filename.remove(item)
                #else:
                #    print "item %s not endswith %s"%(item,match_list[i])


    def list_po_file_fast(self,begin_dir,match_list=[],exclude_target=[]):
        #print "match_list is %s"%(match_list)
        #print "begin_dir:%s,cwd %s"%(begin_dir,os.getcwd())
        os.path.walk(begin_dir,self.get_match_files,match_list)
        #print "1 self.dict_patch_overlay:",self.dict_patch_overlay
        key_list=self.dict_patch_overlay.keys()
        if len(key_list) <= 0:
            #my_dbg_vanzo("Error,not find any patch or overlay",LEVEL_ERROR)
            return  {}
        key_list.sort(self.cmp_digit)
        last_key=key_list[0]
        last_value=self.dict_patch_overlay[last_key]
        last_index=last_key.rfind("$")
        last_key=last_key[:last_index]
        clean_dict={}
        clean_key=last_key
        #print "self.VANZO_PREFIX 2:",self.VANZO_PREFIX
        #print "key_list:",key_list
        #index=self.VANZO_PREFIX.find("vendor")
        for key in key_list[1:]:
            if self.dict_patch_overlay[key].startswith("vendor"):
                index=self.dict_patch_overlay[key].find("vendor/")
                index+=len("vendor/")+1
                self.dict_patch_overlay[key]=self.dict_patch_overlay[key][index:]
                index=self.dict_patch_overlay[key].find("/")
                index+=1
                self.dict_patch_overlay[key]=self.dict_patch_overlay[key][index:]
            if not os.path.exists(os.path.join(self.VANZO_PREFIX,self.dict_patch_overlay[key])):
                my_dbg_vanzo("Error do not exists:%s,please fix it before commit!"%(os.path.join(self.VANZO_PREFIX,self.dict_patch_overlay[key])),LEVEL_ERROR)
                sys.exit(-1)
                self.dict_patch_overlay.pop(key)
                continue
            #if xphone_filter_out_vtrunk_patchset_vanzo(npn_vanzo(self.long_project_name),os.path.join(self.VANZO_PREFIX,self.dict_patch_overlay[key])) == None:
                #continue 
            old_index=key.rfind("$")
            clean_key=key[:old_index]
            if clean_key != last_key:
                clean_dict[last_key]=last_value
            last_key=clean_key
            last_value=self.dict_patch_overlay[key]

            
        if clean_key == last_key:
            clean_dict[last_key]=last_value

        return clean_dict

    def get_project_special_fallback(self,project_name,result_dict={}):
        item="all_projects"
        item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
        result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        list_segs = project_name.split("_")
        list_npn_segs = (npn_vanzo(project_name)).split("_")
        if list_npn_segs[3] != list_segs[3]:
            item="all_%s_projects"%(list_npn_segs[3])
            item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
            result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        item="all_%s_projects"%(list_segs[3])
        item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
        result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        for one in ("mt6735_3m_tdd_cs","mt6735_5m_cs","mt6735_3m_fdd_cs","ldata","gsm","wcdma","td","sgsm","swcdma","std", ):
            if project_name.endswith('_' + one) or '_' + one + '_' in project_name:
                item="all_%s_projects"%(one)
                item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
                result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        for one in ("mt17", "mt15", "mt13"):
            if project_name.startswith(one):
                item="all_%s_projects"%(one)
                item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
                result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        project_info = self.get_project_info(project_name) #origin place
        if not project_info:
            return {}
        if project_info["storage"] == "unknown":
            custom_config=self.project_bsp_config_fallback(project_name)
            platform_config = "mediatek/config/%s/ProjectConfig.mk" % project_info["project"]
            emmc_config=fixup_project_storage_vanzo(platform_config, custom_config)
            if "no" == emmc_config:
                project_info["storage"] = "nand"
            elif "yes" == emmc_config:
                project_info["storage"] = "emmc"
        for one in ("nand", "emmc"):
            if project_info["storage"] == one:
                item="all_%s_projects"%(one)
                item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
                result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        #list_segs = project_name.split("_")
        #result_dict = self.list_po_file("all_%s_%s_projects" % (list_segs[0], list_segs[1]),project_name,result_dict)

        #ui = get_project_ui_vanzo(project_name)
        #if ui != "vtrunk":
            #result_dict = self.list_po_file("all_%s_%s_%s_projects" % (list_segs[0], list_segs[1], ui),project_name,result_dict)

        for one in ('mul', 'tphone', 'vphone', 'sphone', 'ephone', 'aphone', 'project_nameg', 'cphone',):
            if one in project_name:
                item="all_%s_projects"%(one)
                item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
                result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        if "_mul_" in project_name and "_tphone_" in project_name:
            item="all_mul_tphone_projects"
            item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
            result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        if (list_npn_segs[0] != list_segs[0]) or (list_npn_segs[1] != list_segs[1]):
            item="all_%s_%s_projects" % (list_npn_segs[0], list_npn_segs[1])
            item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
            result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        item="all_%s_%s_projects" % (list_segs[0], list_segs[1])
        item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
        result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        ui = get_project_ui_vanzo(project_name)
        #if ui != "vtrunk":
        if (list_npn_segs[0] != list_segs[0]) or (list_npn_segs[1] != list_segs[1]):
                item="all_%s_%s_%s_projects" % (list_npn_segs[0], list_npn_segs[1], ui)
                item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
                result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        item="all_%s_%s_%s_projects" % (list_segs[0], list_segs[1], ui)
        item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
        result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        if (list_npn_segs[0] != list_segs[0]) or (list_npn_segs[1] != list_segs[1]) or (list_npn_segs[3] != list_segs[3]):
            item="all_%s_%s_%s_projects" % (list_npn_segs[0], list_npn_segs[1], list_npn_segs[3])
            item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
            result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        item="all_%s_%s_%s_projects" % (list_segs[0], list_segs[1], list_segs[3])
        item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
        result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)

        #project_info = get_project_info(project_name) #origin place
        #for one in ("nand", "emmc"):
            #if project_info["storage"] == one:
                #result_dict = self.list_po_file("all_%s_projects" % one,project_name,result_dict)

        #for one in ("project_nameg","cphone"):#origin place
            #if one in project_name:
            #    result_dict=self.list_po_file("all_%s_projects" % one,project_name,result_dict)
        return self.dict_patch_overlay



    def get_project_special_fallback_str(self,project_name,result_dict={}):
        list_result=[]
        item="all_projects"
        item="%s|%s.delete|%s.keep"%(item,item,item)
        list_result.extend(item.split("|"))
        #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        list_segs = project_name.split("_")
        list_npn_segs = (npn_vanzo(project_name)).split("_")

        for one in ("mt6735_3m_tdd_cs","mt6735_5m_cs","mt6735_3m_fdd_cs","ldata","gsm","wcdma","td","sgsm","swcdma","std", ):
            if project_name.endswith('_' + one) or '_' + one + '_' in project_name:
                item="all_%s_projects"%(one)
                item="%s|%s.delete|%s.keep"%(item,item,item)
                #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
                list_result.extend(item.split("|"))
        
        for one in ("mt17", "mt15", "mt13"):
            if project_name.startswith(one):
                item="all_%s_projects"%(one)
                item="%s|%s.delete|%s.keep"%(item,item,item)
                #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
                list_result.extend(item.split("|"))

        for one in ("mul",):
            if one in project_name:
                item="all_%s_projects"%(one)
                item="%s|%s.delete|%s.keep"%(item,item,item)
                #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
                list_result.extend(item.split("|"))

        project_info = self.get_project_info(project_name) 
        if not project_info:
            return []
        if project_info["storage"] == "unknown":
            custom_config=self.project_bsp_config_fallback(project_name)
            platform_config = "mediatek/config/%s/ProjectConfig.mk" % project_info["project"]
            emmc_config=fixup_project_storage_vanzo(platform_config, custom_config)
            if "no" == emmc_config:
                project_info["storage"] = "nand"
            elif "yes" == emmc_config:
                project_info["storage"] = "emmc"
        for one in ("nand", "emmc"):
            if project_info["storage"] == one:
                item="all_%s_projects"%(one)
                item="%s|%s.delete|%s.keep"%(item,item,item)
                #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
                list_result.extend(item.split("|"))

        #list_segs = project_name.split("_")
        #result_dict = self.list_po_file("all_%s_%s_projects" % (list_segs[0], list_segs[1]),project_name,result_dict)

        #ui = get_project_ui_vanzo(project_name)
        #if ui != "vtrunk":
            #result_dict = self.list_po_file("all_%s_%s_%s_projects" % (list_segs[0], list_segs[1], ui),project_name,result_dict)


        vtrunk=True
        #for one in ('tphone', 'vphone', 'sphone', 'ephone', 'aphone', 'project_nameg', 'cphone',):
        for one in ('tphone', 'vphone', 'sphone', 'ephone', 'aphone', 'cphone',):
            if one in project_name:
                vtrunk=False
                item="all_%s_projects"%(one)
                item="%s|%s.delete|%s.keep"%(item,item,item)
                #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
                list_result.extend(item.split("|"))
        if vtrunk == True:
                item="all_%s_projects"%("vtrunk")
                item="%s|%s.delete|%s.keep"%(item,item,item)
                #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
                list_result.extend(item.split("|"))

        if list_npn_segs[3] != list_segs[3]:
            item="all_%s_projects"%(list_npn_segs[3])
            item="%s|%s.delete|%s.keep"%(item,item,item)
            list_result.extend(item.split("|"))

        item="all_%s_projects"%(list_segs[3])
        item="%s|%s.delete|%s.keep"%(item,item,item)
        list_result.extend(item.split("|"))
        

        if "_mul_" in project_name and "_tphone_" in project_name:
            item="all_mul_tphone_projects"
            item="%s|%s.delete|%s.keep"%(item,item,item)
            #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
            list_result.extend(item.split("|"))

        if (list_npn_segs[0] != list_segs[0]) or (list_npn_segs[1] != list_segs[1]):
            item="all_%s_%s_projects" % (list_npn_segs[0], list_npn_segs[1])
            item="%s|%s.delete|%s.keep"%(item,item,item)
            #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
            list_result.extend(item.split("|"))

        item="all_%s_%s_projects" % (list_segs[0], list_segs[1])
        item="%s|%s.delete|%s.keep"%(item,item,item)
        #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
        list_result.extend(item.split("|"))

        ui = get_project_ui_vanzo(project_name)
        #if ui != "vtrunk":
        if (list_npn_segs[0] != list_segs[0]) or (list_npn_segs[1] != list_segs[1]):
            item="all_%s_%s_%s_projects" % (list_npn_segs[0], list_npn_segs[1], ui)
            item="%s|%s.delete|%s.keep"%(item,item,item)
            #result_dict = self.list_po_file(item,project_name,self.exclude_target,result_dict)
            list_result.extend(item.split("|"))
        item="all_%s_%s_%s_projects" % (list_segs[0], list_segs[1], ui)
        item="%s|%s.delete|%s.keep"%(item,item,item)
        list_result.extend(item.split("|"))

        if (list_npn_segs[0] != list_segs[0]) or (list_npn_segs[1] != list_segs[1]) or (list_npn_segs[3] != list_segs[3]):
            item="all_%s_%s_%s_projects" % (list_npn_segs[0], list_npn_segs[1], list_npn_segs[3])
            item="%s|%s.delete|%s.keep"%(item,item,item)
            list_result.extend(item.split("|"))
        item="all_%s_%s_%s_projects" % (list_segs[0], list_segs[1], list_segs[3])
        item="%s|%s.delete|%s.keep"%(item,item,item)
        list_result.extend(item.split("|"))

        #project_info = get_project_info(project_name) #origin place
        #for one in ("nand", "emmc"):
            #if project_info["storage"] == one:
                #result_dict = self.list_po_file("all_%s_projects" % one,project_name,result_dict)

        #for one in ("project_nameg","cphone"):#origin place
            #if one in project_name:
            #    result_dict=self.list_po_file("all_%s_projects" % one,project_name,result_dict)
        return list_result


    def list_patchset_overlay_fast(self,project_name,detail="True",quiet=False,search_dir=None):
        cwd=os.getcwd()
        #if os.path.exists("./fallback_extra.txt"):
            #self.VANZO_PREFIX=cwd+"/"
        #else:
            #res=self.to_root_dir()
            #if res == "":
                #root_dir = self.find_root_dir()
                #if root_dir != "":
                    #self.VANZO_PREFIX=root_dir
                #else:
                    #self.VANZO_PREFIX=cwd+"/"
        res=self.to_root_dir()
        if res =="":
            #my_dbg_vanzo("Error,can not find patch and overlay!",LEVEL_ERROR)
            return []
        
        #print "in list_patchset_overlay_fast res:%s,self.VANZO_PREFIX %s"%(res,self.VANZO_PREFIX)
        project_name=self.npn_to_long_project(project_name)
        #print "project_name is %s"%(project_name)
        project_name=project_name.lower().strip()
        self.long_project_name=project_name
        self.exclude_target=self.get_custom_exclude_list()
        self.exclude_target.extend(self.get_exclude_target_list(project_name))
        self.exclude_target=self.unique(self.exclude_target)
        if "tphone" in project_name:
            self.exclude_regex.append(re.compile("_forvtrunk\."))
        else:
            self.exclude_regex.append(re.compile("_fortphone\."))
        match_list=[]
        match_list=self.get_project_special_fallback_str(project_name,self.dict_patch_overlay)
        list_ancestor=self.list_relatives(project_name,KIND_PARENT,True)
        for item in list_ancestor:
            item="%s|%s.delete|%s.keep"%(item,item,item)
            match_list.extend(item.split("|"))

        if search_dir == None:
            search_dir=self.VANZO_PREFIX
        else:
            search_dir=search_dir.strip()
            if len(search_dir)<1:
                search_dir=self.VANZO_PREFIX

        self.dict_patch_overlay={}

        #print "search_dir:%s,match_list:%s,exclude_target:%s"%(search_dir,match_list,self.exclude_target)
        self.dict_patch_overlay=self.list_po_file_fast(search_dir,match_list,self.exclude_target)
        #print "self.dict_patch_overlay:",self.dict_patch_overlay
        
        if len(self.dict_patch_overlay) < 1:
            return []
        if detail == "False":
            list_value=self.dict_patch_overlay.values()
            list_value.sort()
            if quiet == False:
                for value in list_value:
                    res=""
                    full_path=os.path.join(self.VANZO_PREFIX,value)
                    if os.path.isfile(full_path):
                        res+="F " 
                    elif os.path.islink(full_path):
                        res+="L->" 
                        cmd="ls -l %s"%(full_path)
                        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
                        if returncode == 0:
                            index=stdoutdata.find("->")
                            if index>0:
                                index+=2
                                refname=stdoutdata[index:].strip()
                                refname=os.path.abspath(refname)
                                res+=refname
                    elif os.path.isdir(full_path):
                        res+="D " 
                    res+=value
                    cmd="md5sum %s"%(full_path)
                    returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
                    if returncode == 0:
                        md5sum=stdoutdata.split()[0]
                        res+=" "+md5sum
                    #print value
                    print res
            return list_value

        #for compatible with old affects format
        #below to show the author and the date
        values_list=self.dict_patch_overlay.values() 
        values_list.sort()
        origin_overlay_list=[]
        origin_patchset_list=[]
        for item in values_list:
            if item.find("overlay_projects")>=0:
                origin_overlay_list.append(item)
            else:
                origin_patchset_list.append(item)

        os.chdir(self.VANZO_PREFIX) 
        cmd="git log --pretty=format:'%aN %ai' --name-only"
        for value in values_list:
            cmd=cmd+" "+value

        #result = commands.getstatusoutput(cmd)[1].split()
        result = commands.getstatusoutput(cmd)[1].split("\n")
        filter_results=[]
        for item in result:
            if item.find("overlay_projects")>=0  or item.find("patch_projects")>=0:
                filter_results.append(item)
            else:
                filter_results.extend(item.split())
        result=filter_results
        one_item=""
        clean_patch_list=[]
        clean_overlay_list=[]
        one_line=[]
        last_section=False
        filename_list=[]
        for item in result:
            item=item.strip()
            overlay_index=item.find("overlay_projects")
            patch_index=item.find("patch_projects")
            #print "item %s,last_section %s"%(item,last_section)
            if overlay_index >=0 or patch_index >= 0:
                file_name=os.path.basename(item)
                dir_name=os.path.dirname(item)
                find=False
                while find == False and dir_name != "overlay_index" and dir_name != "patch_projects":
                    for suffix in match_list:
                        if file_name.endswith(suffix):
                            find=True
                            break
                    if find == False:
                        file_name=os.path.basename(dir_name)
                        dir_name=os.path.dirname(dir_name)
                if find == False:
                    my_dbg_vanzo("Error %s why in git log but not in patchlist?"%(item),LEVEL_ERROR)
                    continue
                else:
                    #print dir_name,file_name
                    item=os.path.join(dir_name,file_name)

                if not os.path.exists(item):
                    #print "item not exists"
                    continue

                if filename_list.__contains__(item):
                    #print "item already"
                    continue

                #print "the item is %s"%item
                filename_list.append(item)

                if last_section==False:
                    one_line.append(item)
                    one_line.reverse()
                    line=""
                    for section in one_line:
                        line=line+section+" "
                    if patch_index>= 0:
                        clean_patch_list.append(line)
                    else:
                        clean_overlay_list.append(line)
                    last_section=True
                else:
                    one_line=one_line[1:]
                    one_line.insert(0,item)
                    line=""
                    for section in one_line:
                        line=line+section+" "
                    if patch_index>= 0:
                        clean_patch_list.append(line)
                    else:
                        clean_overlay_list.append(line)
            else:
                if last_section==True:
                    one_line=[]
                    last_section=False
                one_line.append(item)
                    

        overlay_list_diff=list(set(origin_overlay_list).difference(set(filename_list)))
        patchset_list_diff=list(set(origin_patchset_list).difference(set(filename_list)))
            
        clean_patch_list=self.unique(clean_patch_list)
        clean_overlay_list=self.unique(clean_overlay_list)
        project = Project_vanzo()
        project.name=project_name
        for x in clean_patch_list:
            patchset = Patchset_vanzo()
            patch_segs=x.split()
            patchset.name = patch_segs[0]
            patchset.date = patch_segs[3]+" "+patch_segs[2]+" "+patch_segs[1]
            patchset.author = patch_segs[4]
            patchset.applies = patch_applies_vanzo(patchset.name)
            project.patchsets.append(patchset)

        for item in patchset_list_diff:
            patchset = Patchset_vanzo()
            patchset.name = item
            patchset.date = "unknown"
            patchset.author = "unknown"
            patchset.applies = patch_applies_vanzo(patchset.name)
            project.patchsets.append(patchset)

        Parse_patch_applies_vanzo(project.patchsets)

        for x in clean_overlay_list:
            overlay = Overlay_vanzo()
            patch_segs=x.split()
            overlay.name = patch_segs[0]
            overlay.date = patch_segs[3]+" "+patch_segs[2]+" "+patch_segs[1]
            overlay.author = patch_segs[4]
            project.overlays.append(overlay)

        for item in overlay_list_diff:
            overlay = Overlay_vanzo()
            overlay.name = item
            overlay.date = "unknown"
            overlay.author = "unknown"
            project.overlays.append(overlay)

        if quiet == False:
            Print_project_vanzo(project)

        #for item in clean_list:
            #print item
            
        os.chdir(cwd) 
        return self.dict_patch_overlay.values()[:]
        
    '''
    deprecated
    '''
    def list_patchset_overlay(self,project_name):
        self.exclude_target=self.get_custom_exclude_list()
        self.exclude_target.extend(self.get_exclude_target_list(project_name))
        project_name=project_name.lower().strip()
        self.dict_patch_overlay=self.get_project_special_fallback(project_name,self.dict_patch_overlay)
        list_ancestor=self.list_relatives(project_name,KIND_PARENT,True)
        for item in list_ancestor:
            item=".*%s|.*%s.delete|.*%s.keep"%(item,item,item)
            self.dict_patch_overlay=self.list_po_file(item,project_name,self.exclude_target,self.dict_patch_overlay)

        for key,value in self.dict_patch_overlay.items():
            my_dbg_vanzo(self.dict_patch_overlay[key])
        return self.dict_patch_overlay
        
    def get_possible_ancestor(self,project_name):
        if self.ugly_internal_fallback_tree == None:
            self.create_ugly_internal_rules_tree();
        work_tree=copy.deepcopy(self.ugly_internal_fallback_tree)
        parent_list=[]
        while True:
            leaves_list=work_tree.leaves()
            if len(leaves_list) <= 1:
                break
            for leave in leaves_list:
                item=leave.identifier
                if item == "root":
                    break
                if project_name.find(item)>=0:
                    iterator=item
                    work_name=project_name
                    while iterator != "root" and work_tree.parent(iterator).identifier != "root":
                        parent_identifier=work_tree.parent(iterator).identifier
                        if parent_identifier != "self":
                            parent_name=work_name.replace(iterator,parent_identifier)
                        else:
                            parent_name=work_name.replace(iterator,"")
                        #if self.exist_project(parent_name):
                        parent_list.append(parent_name)
                        iterator=parent_identifier
                        work_name=parent_name
                work_tree.remove_node(item)
        result_list=[]
        for item in parent_list:
            result_list.extend(self.list_relatives(item,KIND_PARENT,True))
            result_list.append(item)
            
        return result_list
                        

    def list_relatives(self,long_project_name,kind=KIND_ALL,quiet=False):
        if self.use_cache == True:
            if kind == KIND_PARENT:
                parent_list=self.load_project_parent(long_project_name,True)
                if parent_list != None and len(parent_list)>=1:
                    parent_list=self.unique(parent_list)
                    if quiet == False:
                        my_dbg_vanzo("Parents:\n",LEVEL_HINT)
                        my_dbg_vanzo("load from cache:",LEVEL_IMPORTANT)
                        for item in parent_list:
                            my_dbg_vanzo(item,LEVEL_IMPORTANT)
                    return parent_list
        cwd=os.getcwd()
        try:
            fallback_file=self.VANZO_PREFIX+"fallback_extra.txt"
            if not os.path.exists(fallback_file):
                root_dir=self.to_root_dir()
        except Exception, e:
            pass 
        project_name=npn_vanzo(long_project_name.lower().strip())
        list_result=[]
        if self.fallback_tree is None:
            self.create_fallback_tree()
        if kind == KIND_PARENT:
            list_result=[]
            if not self.fallback_tree.contains(project_name):
                npn_name=npn_vanzo(project_name)
                list_result.append(npn_name)
                list_result.append("root")
            else:
                for node in self.fallback_tree.rsearch(project_name):
                    list_result.append(self.fallback_tree[node].identifier.strip())
                #if quiet == False:
                   #my_dbg_vanzo(self.fallback_tree[node].identifier,LEVEL_IMPORTANT)
            list_result.reverse()
            #print "list_result is %s"%(list_result)
            list_result=list_result[1:]
            #print "before get_possible_ancestor list_result:%s"%(list_result)
            result_list=[] 
            for item in list_result:
                result_list.extend(self.get_possible_ancestor(item))
                #result_list.append(item)
            #print "the result_list of inter is %s"%(result_list)
            result_list.extend(list_result)
            result_list=self.unique(result_list)
            if quiet == False:
                    my_dbg_vanzo("Parents:\n",LEVEL_HINT)
                    for item in result_list:
                        my_dbg_vanzo(item,LEVEL_IMPORTANT)
            if len(result_list) >= 2:
                map_parent={}
                map_parent[long_project_name.strip()]=result_list
                self.dump_project_parent(long_project_name.strip(),map_parent)
            os.chdir(cwd)
            return result_list 
        elif kind == KIND_CHILD:
            #fix me,now only support fallback_extra.txt
            child_list=[]
            project_list=self.read_all_projects()
            first_part_index=project_name.find("_")+3
            first_part=project_name[:first_part_index]
            for item in project_list:
                if item[:first_part_index] == first_part:
                    list_ancestor=self.list_relatives(item,KIND_PARENT,True)
                    #print "list_ancestor is %s"%(list_ancestor)
                    for ances in list_ancestor:
                        if ances == project_name:
                            child_list.append(npn_vanzo(item)) 
                            break
            child_list.sort()
            child_list=self.unique(child_list)
            if quiet == False:
                my_dbg_vanzo("Children:\n",LEVEL_HINT)
                for item in child_list:
                    my_dbg_vanzo(item,LEVEL_IMPORTANT)
            os.chdir(cwd)
            return child_list
        elif kind == KIND_ALL:
            list_ancestor=self.list_relatives(project_name,KIND_PARENT,True)
            list_child=self.list_relatives(project_name,KIND_CHILD,True)
            if quiet == False:
                my_dbg_vanzo("Parents:\n",LEVEL_HINT)
                for item in list_ancestor:
                    my_dbg_vanzo(item,LEVEL_IMPORTANT)
                my_dbg_vanzo("Children:\n",LEVEL_HINT)
                for item in list_child:
                    my_dbg_vanzo(item,LEVEL_IMPORTANT)
            os.chdir(cwd)
            return list_ancestor.extend(list_child)
        else:
            my_dbg_vanzo("Sorry,now not support!",LEVEL_ERROR)
        os.chdir(cwd)
        return []

        
    def do_patch_overlay(self,force=False):
        if not os.path.exists("update_overlay_files.py"):
            my_dbg_vanzo("Error,Can not find update_overlay_files.py",LEVEL_ERROR)
            return
        symbol = self.VANZO_PREFIX+'patch_done_tag.txt'
        if force == True:
            #os.remove(symbol)
            self.clean_dir()
        #elif os.path.exists(symbol):
            #my_dbg_vanzo("patch already Done",LEVEL_HINT)
            #return
        #cmd="cp update_overlay_files.py build/tools/;chmod +x ./update_overlay_files.py;./update_overlay_files.py"
        #my_sys_vanzo(cmd)
        self.update_po()
    def get_current_prj(self):
        current_manifest=".repo/manifest.xml"
        if os.path.exists(current_manifest):
            real_manifest=os.readlink(current_manifest);
            clean_xml=os.path.basename(real_manifest).strip()
            project_name=clean_xml[:-4]
            return project_name
        else:
            return None
        
    def set_env(self,project_name=""):
        self.set_project(project_name)
        self.do_patch_overlay()

    def compile(self,project_name=""):
        if project_name == "":
            project_name=self.get_current_prj()
        self.set_env(project_name)
        project_info = self.get_project_info(project_name)
        if not project_info:
            return
        target_project=project_info["project"]
        dir="mediatek/custom/%s"%(target_project)
        cmd="git config --get user.email"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode!=0 or (stdoutdata and len(stdoutdata)<1):
            address="wangfei@vanzotec.com"
        else:
            address=stdoutdata.strip()
        if os.path.exists(dir):
            cmd="nohup ./makeMtk -t %s n ;mail -s %s:%s:$? %s < /dev/null" %(target_project,os.getcwd(),project_name,address)
            my_dbg_vanzo("compile cmd is %s"%(cmd),LEVEL_DBG)
            my_sys_vanzo(cmd)
        else:
            my_dbg_vanzo("Error,no such project %s"%(target_project),LEVEL_ERROR)
            return
        
        
    def is_platform_file(self,file_name):
        if file_name.find("mediatek")>=0:
            return True
        else:
            return False
    def process_common_list(self,common_list,src_project,dst_project):
        dst_npn_name=npn_vanzo(dst_project);
        src_npn_name=npn_vanzo(src_project);
        src_list=[]
        dst_list=[]
        dst_project_info = self.get_project_info(dst_project)
        src_project_info = self.get_project_info(src_project)
        if not dst_project_info or not src_project_info:
            my_dbg_vanzo("Error not get the project_info!",LEVEL_ERROR)
            return
        mixed=False
        if dst_project_info["project"] != src_project_info["project"]:
            mixed=True
        for item in common_list:
            src_file_name=self.VANZO_PREFIX+item
            target_file_name=src_file_name.replace(src_npn_name,dst_npn_name)
            src_list.append(src_file_name)
            if mixed == True:
                target_file_name=target_file_name.replace(src_project_info["project"],dst_project_info["project"])
            dst_list.append(target_file_name)
        self.copy_file_list(src_list,dst_list,False)

    def process_platform_list(self,platform_list,src_project,dst_project):
        dst_npn_name=npn_vanzo(dst_project);
        src_npn_name=npn_vanzo(src_project);
        src_overlay_list=[]
        src_patch_list=[]
        dst_overlay_list=[]
        dst_patch_list=[]
        src_project_info = self.get_project_info(src_project)
        dst_project_info = self.get_project_info(dst_project)
        if not dst_project_info or not src_project_info:
            my_dbg_vanzo("Error not get the project_info!",LEVEL_ERROR)
            return
        for item in platform_list:
            if item.find("overlay_projects/")>=0:#for overlay
                src_file_name=self.VANZO_PREFIX+item
                src_overlay_list.append(src_file_name)
                dst_file_name=src_file_name.replace(src_npn_name,dst_npn_name).replace(src_project_info["project"],dst_project_info["project"])
                dst_overlay_list.append(dst_file_name)
            elif item.find("patch_projects/")>=0:#for patchset
                src_file_name=self.VANZO_PREFIX+item
                src_patch_list.append(src_file_name)
                dst_file_name=src_file_name.replace(src_npn_name,dst_npn_name).replace(src_project_info["project"],dst_project_info["project"])
                dst_patch_list.append(dst_file_name)
            else:
                my_dbg_vanzo("Warning!file %s not processed"%(item),LEVEL_WARNING)

        self.copy_file_list(src_overlay_list,dst_overlay_list,False)
        self.copy_file_list(src_patch_list,dst_patch_list,False)
        for item in dst_patch_list:
            cmd = "sed -i --follow-symlinks 's#{0}#{1}#' {2}".format(src_project_info["project"],dst_project_info["project"], item)
            my_sys_vanzo(cmd)
                

    def modify_model(self,src_project,dst_project,model=""):
        normal_src_project=npn_vanzo(src_project)    
        normal_dst_project=npn_vanzo(dst_project)
        new_model="" 
        file_name=self.VANZO_PREFIX+"overlay_projects/build/tools/buildinfo.custom"
        if model=="":
            with open(file_name) as in_file:
                lines = in_file.readlines()
                for item in lines:
                    index=item.find(normal_src_project+":")
                    if index==0:
                        index+=len(normal_src_project+":")
                        new_model=item[index:]
                    elif item.find(normal_dst_project+":")>=0:
                        my_dbg_vanzo("Already set model",LEVEL_DBG)
                        return False
        else:
            new_model=model
        new_line=normal_dst_project+":"+new_model
        with open(file_name,"a+") as out_file:
            out_file.write(new_line)
            return True
                        
    def add_fallback(self,child_name,parent_name):
        fallback_file=self.VANZO_PREFIX+"fallback_extra.txt"
        new_line="%s:%s"%(child_name,parent_name)
        with open(fallback_file) as in_file:
            lines = in_file.readlines()
            for item in lines:
                if item.strip() == new_line.strip():
                    my_dbg_vanzo("Warning!line %s has already been added"%(new_line),LEVEL_WARNING)
                    return False
        with open(fallback_file,"a+") as out_file:
            out_file.write(new_line+"\n")
            return True 
        
    def add_dailybuild_list(self,project_name):
        dailybuild_list=os.path.expanduser('~')+"/build_projects/scripts/dailybuild_all_projects.txt"
        if not os.path.exists(dailybuild_list):
            my_dbg_vanzo("Warning!Can not find the dailybuild_all_projects!",LEVEL_WARNING)
            return
        with open(dailybuild_list) as in_file:
            lines = in_file.readlines()
            for item in lines:
                if item.strip() == project_name.strip():
                    my_dbg_vanzo("Warning!file %s has already been added"%(project_name),LEVEL_WARNING)
                    return
        with open(dailybuild_list,"a+") as out_file:
            out_file.write(project_name+"\n")
        self.modified_project.append("~/build_projects")
        
    def create_project_from(self,dst_project,src_project):
        dst_name=dst_project.lower().strip()
        src_name=src_project.lower().strip()
        if not self.is_exist_file(".repo/manifests/%s.xml"%(src_name)):
            my_dbg_vanzo("Error!project %s not exist"%(src_name),LEVEL_ERROR)
            return
        my_dbg_vanzo("parent:%s,child: %s"%(src_name,dst_name),LEVEL_DBG)

        dst_npn_name=npn_vanzo(dst_name);
        src_npn_name=npn_vanzo(src_name);

        self.create_manifest(dst_name)#here new a manifest
        self.add_dailybuild_list(dst_name)#here add to dailybuild file,then compile tools will work
        src_project_info = self.get_project_info(src_name)
        dst_project_info = self.get_project_info(dst_name)
        if not dst_project_info or not src_project_info:
            my_dbg_vanzo("Error not get the project_info!",LEVEL_ERROR)
            return
        mixed=False
        if src_project_info["project"] != dst_project_info["project"]:
            mixed=True
        my_dbg_vanzo("The mixed status is %s"%(mixed),LEVEL_DBG)

        if mixed == True:
            #print "the dst_name is %s,src_name is %s"%(dst_name,src_name)
            #list_dst = commands.getstatusoutput(os.path.expanduser('~')+self.tool_dir+"affects_one -p %s"%(dst_name))[1].split("\n");
            #list_src = commands.getstatusoutput(os.path.expanduser('~')+self.tool_dir+"affects_one -p %s"%(src_name))[1].split("\n");
            list_src=self.list_patchset_overlay_fast(src_name,"False")
            list_dst=self.list_patchset_overlay_fast(dst_name,"False")
            #print "list_dst is %s"%list_dst
            #print "list_src is %s"%list_src
            list_diff=list(set(list_src).difference(set(list_dst)))
            #print "list_diff is %s"%list_diff
            list_src_common=[]
            list_platform=[]
            diff_len=len(list_diff)
            if diff_len > 0:
                for item in list_diff:
                    src_file_name=item.split()[0]
                    if self.is_platform_file(src_file_name):
                        list_platform.append(src_file_name)
                    else:
                        list_src_common.append(src_file_name)
                self.process_common_list(list_src_common,src_name,dst_name)
                self.process_platform_list(list_platform,src_name,dst_name)
                self.modified_project.append(self.VANZO_PREFIX)
            else:
                my_dbg_vanzo("Warning!why has no diff?",LEVEL_WARNING)

            added=self.modify_model(src_name,dst_name)
            if added == True:
                self.modified_project.append(self.VANZO_PREFIX)
        #then modify the fallback
        added=self.add_fallback(dst_npn_name,src_npn_name)#add fallback,then it will use the parent config
        if added == True:
            self.modified_project.append(self.VANZO_PREFIX)
        len_modified=len(self.modified_project)
        if len_modified > 0:
            my_dbg_vanzo("below project You must check and commit:\n",LEVEL_HINT)
            for item in self.modified_project:
                my_dbg_vanzo("\t%s"%(item),LEVEL_IMPORTANT)
        else:
            my_dbg_vanzo("Strange!no change!",LEVEL_WARNING)
    def new_project(self,parameter):
        cwd=self.to_root_dir()
        if cwd == "":
            my_dbg_vanzo("Error, do not find the .repo",LEVEL_ERROR)
            sys.exit()
        list_para=parameter.split(" ")
        if len(list_para)<2:
            my_dbg_vanzo("Error create project from a project,\nUsage:new_project child_project parent_project",LEVEL_ERROR)
            return
        self.create_project_from(list_para[0],list_para[1])
        os.chdir(cwd)

    def git_diff(self,nouse,dirname,filename):
        git_symbol=os.path.join(dirname,".git")
        for item in filename:
            if item.startswith(".") and filename != ".":
                filename.remove(item)
        if not os.path.exists(git_symbol):
            return 
        cwd=os.getcwd()
        my_dbg_vanzo("Project:%s"%(dirname),LEVEL_IMPORTANT)
        os.chdir(dirname)
        cmd="git diff ."
        #results = commands.getstatusoutput(cmd)[1].split()
        results = commands.getstatusoutput(cmd)[1]
        my_dbg_vanzo(results,LEVEL_HINT)
        os.chdir(cwd)
        if not "packages" in filename:
            del filename[:]
            return
        else:
            if dirname == "mediatek":
                del filename[:]
                filename.append("packages")
                return
    def git_status(self,quiet,dirname,filename):
        #print "dirname:",dirname
        #print "filename:",filename
        git_symbol=os.path.join(dirname,".git")
        for item in filename:
            if item.startswith(".") and filename != ".":
                filename.remove(item)
        #if not os.path.exists(git_symbol):
            #return 
        cwd=os.getcwd()
        os.chdir(dirname)
        #print "cwd,",os.getcwd()
        cmd="git status -s ."
        #cmd="git status ."
        #results = commands.getstatusoutput(cmd)[1].split()
        #results = commands.getstatusoutput(cmd)[1].split("\n")
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode!=0:
            return
        #print returncode,stdoutdata,stderrdata
        if len(stdoutdata)>1:
            results=stdoutdata.split("\n")
            #print "results is %s"%(results)
            if len(results)>0:
                if quiet == False:
                    my_dbg_vanzo("Project:%s"%(dirname),LEVEL_IMPORTANT)
                    my_dbg_vanzo("\n".join(results),LEVEL_HINT)
                '''
                fullpath_list=[]
                for item in results:
                    item=item.strip()
                    if len(item)>1:
                        segs=item.split()
                        if len(segs)<2:
                            continue
                        fullpath=os.path.join(dirname,segs[1])
                        fullpath_list.append(segs[0]+" "+fullpath+" ".join(segs[2:]))
                self.status_list.extend(fullpath_list)
                '''
                self.status_list.extend(results)
        os.chdir(cwd)
        if not "packages" in filename:
            del filename[:]
            return
        else:
            if dirname == "mediatek":
                del filename[:]
                filename.append("packages")
                return
            else:
                del filename[:]
                return
                

    def list_real_file(self,parameter):
        list_para=parameter.strip().split(" ")
        file_name=""
        project_name="" 
        if len(list_para)<2:
            file_name=list_para[0]
            project_name=self.get_current_prj()
        else:
            file_name=list_para[0]
            project_name=list_para[1]
        file_name=file_name+".overlay."
        #print "file_name is %s"%(file_name)
        real_file=project_custom_get_fallback_file_vanzo(project_name,file_name)
        #print real_file 
        return real_file
        
    def list_diff_dir(self,dir_name=None):
        if dir_name == None:
            dir_name=os.getcwd()
        else:
            dir_name=dir_name.strip()
            if len(dir_name) < 1:
                dir_name=os.getcwd()
        os.path.walk(dir_name,self.git_diff,None)
    def list_status_dir(self,dir_name=None,quiet=False):
        if dir_name == None:
            dir_name=os.getcwd()
        else:
            dir_name=dir_name.strip()
            if len(dir_name) < 1:
                dir_name=os.getcwd()
        #print "dir_name %s"%(dir_name)
        os.path.walk(dir_name,self.git_status,quiet)
        '''
        cwd=os.getcwd()
        os.chdir(dir_name)
        cmd="git status -s ."
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode ==0:
            if len(stdoutdata)>1:
                results=stdoutdata.split("\n")
                if len(results)>0:
                    if quiet == False:
                        my_dbg_vanzo("Project:%s"%(dir_name),LEVEL_IMPORTANT)
                        my_dbg_vanzo("\n".join(results),LEVEL_HINT)
                self.status_list.extend(results)
        os.chdir(cwd)
        for current_src_root,dirs,files in os.walk(dir_name,False,None,True):
            git_symbol=os.path.join(current_src_root,".git")
            #print "git_symbol:",git_symbol
            if not os.path.exists(git_symbol):
                continue
            os.chdir(current_src_root)
            returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
            #print "returncode %d,stdoutdata %s,stderrdata %s"%(returncode,stdoutdata,stderrdata)
            os.chdir(cwd)
            if returncode !=0:
                my_dbg_vanzo("git status error",LEVEL_ERROR)
                return
            if len(stdoutdata)>1:
                results=stdoutdata.split("\n")
                if len(results)>0:
                    if quiet == False:
                        my_dbg_vanzo("Project:%s"%(current_src_root),LEVEL_IMPORTANT)
                        my_dbg_vanzo("\n".join(results),LEVEL_HINT)
                self.status_list.extend(results)
        '''
                
       
    def get_last_patchset(self,search_dir=None,start_id=None):
        #print "search_dir:%s,start_id:%s"%(search_dir,start_id)
        cwd=os.getcwd()
        if search_dir == None:
            search_dir=os.getcwd()
        os.chdir(search_dir)
        #cmd="git log --pretty=format:'%aN %ai' --name-only"
        if not start_id:
            cmd="git log -n1 --name-only --pretty=oneline"
        else:
            cmd="git log --name-only --pretty=oneline %s..HEAD"%(start_id)

        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            os.chdir(cwd)
            return [],[]
        raw_list=stdoutdata.split("\n")
        #print "raw_list:",raw_list
        if len(raw_list)<2:
            os.chdir(cwd)
            return [],[]
        cmd="git rev-parse --git-dir"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("get git dir error",LEVEL_ERROR)
            os.chdir(cwd)
            return [],[]
        git_dir=stdoutdata.strip().split("\n")[0]
        if git_dir == ".git":
            git_dir = search_dir
        else:
            git_dir=os.path.dirname(git_dir)
        git_dir=os.path.join(cwd,git_dir)
        #print "git_dir:%s,cwd %s"%(git_dir,cwd)
        modified_patchset=[]
        modified_list=[]
        for one_line in raw_list:
            one_line=one_line.strip()
            one_line=os.path.join(git_dir,one_line)
            if one_line.find(".patchset.")>=0:
                if os.path.exists(one_line):
                    if one_line not in modified_patchset:
                        modified_patchset.append(one_line)
            if len(one_line.split())==1:
                if one_line not in modified_list:
                    modified_list.append(one_line)
                
        os.chdir(cwd)
        #print "modified_patchset:%s,modified_list:%s"%(modified_patchset,modified_list)
        return modified_patchset,modified_list
        

    def get_current_modified_file(self,search_dir=None):
        if search_dir == None:
            search_dir=os.getcwd()
        self.list_status_dir(search_dir,True)
        modified_list=[]
        modified_patch=[]
        cached_list=[]
        notracked_list=[]
        #print "self.status_list:",self.status_list
        #print "search_dir:",search_dir
        for item in self.status_list:
            #item=item.strip()
            if len(item)<1:
                continue
            segs_list=item.split()
            #print "item[0] %s,segs_list:%s"%(item[0],segs_list)
            if len(segs_list)<2:
                continue
            for seg in segs_list:
                if seg[0]=="D" or seg[0]=="AD":
                    continue
                if (seg.find(".patchset.") > 0):
                    #if os.path.exists(seg):
                    seg=seg.strip()
                    modified_patch.append(search_dir+"/"+seg)
            #print "segs_list:",segs_list
            if len(segs_list)>1:
                modified_list.append(segs_list[1].strip())
                if segs_list[0]=="??":
                    notracked_list.append(segs_list[1].strip())
                else:
                    cached_status=item[0].strip()
                    #print "cached_status:",cached_status
                    if len(cached_status)>0 and cached_status!="?":
                        if segs_list[1] not in cached_list:
                            cached_list.append(segs_list[1].strip())

        #print "cached_list:",cached_list
        #print "notracked_list:",notracked_list
        #print "modified_list:",modified_list
        return modified_patch,modified_list,cached_list,notracked_list
                

    def get_all_patchset(self,platform=None):
        excludes=[]
        list_old_file = glob.glob(os.path.expanduser('~')+"/build_projects/scripts/deprecated*.txt")
        for deprecated_file in list_old_file:
            with open(deprecated_file) as in_file:
                lines = in_file.readlines()
                for item in lines:
                    if item.find("#") >= 0:
                        continue
                    item=npn_vanzo(item.strip())
                    excludes.append(item)
        match="*.patchset.*%s*"%(platform)
        cmd="find %s -name '%s'"%(self.VANZO_PREFIX+"patch_projects/",match)
        #print "cmd is %s"%(cmd)
        list_file = commands.getstatusoutput(cmd)[1].split()
        #work_list=[]

        #for item in list_file:
        #    find=False
        #    for exclude in excludes:
        #        if item.find(exclude) >= 0:
        #            print "exclude is %s,item %s"%(exclude,item)
        #            find=True
        #            break
        #    if find==False:
        #        work_list.append(item)
            
        #print "len work_list is %d"%(len(work_list))
        return list_file
    def verify_source(self,src_file=None):
        dirname=""
        #print "enter verify_source src_file %s"%(src_file)
        #if src_file==None:
            #dirname=os.getcwd()
        #else:
            #if os.path.isdir(src_file):
                #dirname=src_file
            #else:
                #dirname=os.path.dirname(src_file)
        dirname=self.get_git_pos(src_file)
        if not dirname:
            my_dbg_vanzo("file %s not valid"%(src_file),LEVEL_ERROR)
            return False
        elif not os.path.exists(dirname):
            my_dbg_vanzo("directory %s not exist"%(dirname),LEVEL_ERROR)
            return False
        #print "after get_git_pos dirname %s"%(dirname)
        cwd=os.getcwd()
        os.chdir(dirname)
        cmd="git status -s"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        #print returncode,stdoutdata,stderrdata
        if returncode != 0: 
            my_dbg_vanzo("please ensure %s is a git project"%(dirname),LEVEL_ERROR)
            os.chdir(cwd)
            return False
        if stdoutdata != None and len(stdoutdata)>0:
            if stdoutdata.find("??")>=0:
                my_dbg_vanzo("Error,%s has untracked files,please git add it or remove it first,or else will be cleared!"%(dirname),LEVEL_ERROR)
                os.chdir(cwd)
                return False
        if stderrdata != None and len(stderrdata)>0:
            my_dbg_vanzo("Error occured when git status in %s"%(dirname),LEVEL_ERROR)
            os.chdir(cwd)
            return False

        cmd="git diff ."
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        #print returncode,stdoutdata,stderrdata
        if returncode != 0:
            my_dbg_vanzo("please ensure %s is a git project"%(dirname),LEVEL_ERROR)
            os.chdir(cwd)
            return False
        if stdoutdata != None and len(stdoutdata)>0:
            my_dbg_vanzo("Error,%s has modify,please git add or commit it first,or else will be cleared!"%(dirname),LEVEL_ERROR)
            os.chdir(cwd)
            return False
        if stderrdata != None and len(stderrdata)>0:
            my_dbg_vanzo("Error occured when git status in %s"%(dirname),LEVEL_ERROR)
            os.chdir(cwd)
            return False

        os.chdir(cwd)
        return True

    def get_git_pos(self,src_file):
        #print "enter get_git_pos",src_file
        if not src_file or not os.path.exists(src_file):
            return None
        dir_name=""
        if os.path.isdir(src_file):
            dir_name=src_file
        else:
            dir_name=os.path.dirname(src_file)
        #print "dir_name is %s"%(dir_name)
        git_symbol=os.path.join(dir_name,".git")
        #print dir_name,git_symbol
        while not os.path.exists(git_symbol):
            if dir_name==None or len(dir_name)<1 or dir_name == "/":
                return None
            dir_name=os.path.dirname(dir_name)
            git_symbol=os.path.join(dir_name,".git")
        return dir_name
    def get_related_patch(self,src_file):
        if (not src_file) or (not os.path.exists(src_file)):
            return []
        git_dir=self.get_git_pos(src_file) 
        #print "git_dir:",git_dir
        if not git_dir:
            return []
        patch_dir=self.VANZO_PREFIX+"patch_projects/"+os.path.relpath(git_dir)
        #print "patch_dir is",patch_dir
        if not os.path.exists(patch_dir):
            return []
        cmd="find %s/*"%(patch_dir)
        related_list=commands.getstatusoutput(cmd)[1].split("\n")
        #print "related_list:",related_list
        return related_list

        
        
    def find_root_dir(self):
        symbol="fallback_extra.txt"
        cmd="find %s -name %s"%(os.getcwd(),symbol)
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode !=0:
            return ""
        else:
            #here just return the first position,fixme
            file_list=stdoutdata.strip().split("\n")
            if len(file_list) < 1:
                return ""
            file_list.sort()
            #fixme for customtool has two directory one vanzo_custom_XXX,one vendor/XXX
            file_path=file_list[-1]
            #print "file_path:",file_path
            return os.path.dirname(file_path)
        
    def get_app_chooseable_patchset(self,src_dir):
        cwd=os.getcwd()
        res=self.to_root_dir()
        if res =="":
            my_dbg_vanzo("Error,can not find the patch overlay root dir",LEVEL_ERROR)
            os.chdir(cwd)
            return []
        else:
            root_dir=os.path.join(os.getcwd(),self.VANZO_PREFIX)
        search_dir=os.path.join("patch_projects/",src_dir)
        search_dir=os.path.join(root_dir,search_dir)
        files=glob.glob("%s/*.patchset"%(search_dir))
        os.chdir(cwd)
        print "patchset:",files
        return files
    def get_app_chooseable_overlay(self,src_dir):
        cwd=os.getcwd()
        res=self.to_root_dir()
        if res =="":
            my_dbg_vanzo("Error,can not find the patch overlay root dir",LEVEL_ERROR)
            os.chdir(cwd)
            return []
        else:
            root_dir=os.path.join(os.getcwd(),self.VANZO_PREFIX)

        search_dir=os.path.join("overlay_projects/",src_dir)
        search_dir=os.path.join(root_dir,search_dir)
        cmd="find %s -name '*.overlay'"%(search_dir)
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            os.chdir(cwd)
            return []
        files=stdoutdata.split("\n")
        os.chdir(cwd)
        print "overlays:",files
        return files
        
    def get_app_patchset(self,src_dir,project_name=None):
        if not project_name:
            project_name=self.current_project
        if not project_name:
            project_name=self.get_current_prj()
        if not project_name or len(project_name) < 1:
            return []
        #print "project_name:%s,src_dir %s"%(project_name,src_dir)
        cwd=os.getcwd()
        res=self.to_root_dir()
        if res =="":
            my_dbg_vanzo("Error,can not find the patch overlay root dir",LEVEL_ERROR)
            os.chdir(cwd)
            return []
        else:
            root_dir=os.path.join(os.getcwd(),self.VANZO_PREFIX)
        search_dir=os.path.join("patch_projects/",src_dir)
        search_dir=os.path.join(root_dir,search_dir)
        #print "search_dir:%s,root_dir %s,project_name %s,self.VANZO_PREFIX:%s"%(search_dir,root_dir,project_name,self.VANZO_PREFIX)
        #os.chdir(root_dir)
        list_all=self.list_patchset_overlay_fast(project_name,"False",True,search_dir)
        os.chdir(cwd)
        return list_all
    def get_app_overlay(self,src_dir,project_name=None):
        if not project_name:
            project_name=self.current_project
        if not project_name:
            project_name=self.get_current_prj()
        if not project_name or len(project_name) < 1:
            return []
        cwd=os.getcwd()
        res=self.to_root_dir()
        if res =="":
            my_dbg_vanzo("Error,can not find the patch overlay root dir",LEVEL_ERROR)
            os.chdir(cwd)
            return []
        else:
            root_dir=os.path.join(os.getcwd(),self.VANZO_PREFIX)

        search_dir=os.path.join("overlay_projects/",src_dir)
        search_dir=os.path.join(root_dir,search_dir)
        list_all=self.list_patchset_overlay_fast(project_name,"False",True,search_dir)
        os.chdir(cwd)
        return list_all
    def get_app_patchset_overlay(self,git_project,project_name=None):
        if not project_name:
            project_name=self.current_project
        if not project_name:
            project_name=self.get_current_prj()
        if not project_name or len(project_name) < 1:
            return []
        cwd=os.getcwd()
        res=self.to_root_dir()
        if res =="":
            my_dbg_vanzo("Error,can not find the patch overlay root dir",LEVEL_ERROR)
            os.chdir(cwd)
            return []
        else:
            root_dir=os.path.join(os.getcwd(),self.VANZO_PREFIX)
        search_dir=os.path.join("patch_projects/",git_project)
        search_dir=os.path.join(root_dir,search_dir)

        list_all=self.list_patchset_overlay_fast(project_name,"False",True,search_dir)

        search_dir=os.path.join("overlay_projects/",git_project)
        search_dir=os.path.join(root_dir,search_dir)
        list_overlay=self.list_patchset_overlay_fast(project_name,"False",True,search_dir)
        list_all.extend(list_overlay)
        return list_all

    def patch_one_project(self,git_project,project_name=None,root_dir=None):
        if not project_name:
            project_name=self.current_project
        if not project_name:
            project_name=self.get_current_prj()
        if not project_name or len(project_name) < 1:
            return False
        #print "git_project:%s,project_name %s"%(git_project,project_name)
        cwd=os.getcwd()
        #fallback_file=os.path.join(self.VANZO_PREFIX,"fallback_extra.txt")
        #if not os.path.exists(fallback_file):
        res=self.to_root_dir(root_dir)
        if res =="":
            my_dbg_vanzo("Error,can not find the patch overlay root dir",LEVEL_ERROR)
            os.chdir(cwd)
            return False
        else:
            root_dir=os.path.join(os.getcwd(),self.VANZO_PREFIX)
        search_dir=os.path.join("patch_projects/",git_project)
        search_dir=os.path.join(root_dir,search_dir)
        #print "search_dir:%s,root_dir %s,project_name %s,self.VANZO_PREFIX:%s"%(search_dir,root_dir,project_name,self.VANZO_PREFIX)
        #os.chdir(root_dir)
        list_all=self.list_patchset_overlay_fast(project_name,"False",True,search_dir)
        origin_patchset_list,_=self.transer_to_vanzo_interface(list_all)
        origin_patchset_list.sort(self.cmp_time)
        #print "origin_patchset_list:%s"%(origin_patchset_list)

        search_dir=os.path.join("overlay_projects/",git_project)
        search_dir=os.path.join(root_dir,search_dir)
        list_all=self.list_patchset_overlay_fast(project_name,"False",True,search_dir)
        _,origin_overlay_dict=self.transer_to_vanzo_interface(list_all)
        #print "origin_overlay_dict:",origin_overlay_dict

        if self.checkout_or_clone_dir(git_project,project_name) == False:
            os.chdir(cwd)
            return False

        project_info=self.get_project_info(project_name)
        if not project_info:
            os.chdir(cwd)
            return False
        update_patchsets_vanzo(origin_patchset_list, project_info["project"])

        update_overlays_vanzo(origin_overlay_dict)

        #print "list_all:",list_all

        os.chdir(cwd)

        return True

    def check_patch_conflict(self,patch_list=None,error_stop=False):
        work_cwd=os.getcwd()
        self.set_force(False)
        res=self.to_root_dir()
        #current_prj=self.get_current_prj()
        current_prj=""
        #print "patch_list is %s"%(patch_list)
        if res == "":
            my_dbg_vanzo("Error,Can not find the .repo dir",LEVEL_ERROR)
            os.chdir(work_cwd)
            return  False
            #sys.exit()
        #print "self.VANZO_PREFIX:",self.VANZO_PREFIX
        if patch_list == None:
            patch_list,_,_,_=self.get_current_modified_file(self.VANZO_PREFIX)
        else:
            #patch_list=patch_list.strip()
            if len(patch_list) < 1:
                patch_list,_,_,_=self.get_current_modified_file(self.VANZO_PREFIX)
            #else:
                #patch_list=patch_list.split()

        #print "patch_list is %s"%(patch_list)
        
        #sub_projects=self.list_relatives(project_name,KIND_CHILD,True)
        #match_name=patch_name.replace(self.VANZO_PREFIX,"")
        #match_name=match_name.replace("patch_projects","")
        if len(patch_list) < 1:
            my_dbg_vanzo("No valid patch",LEVEL_ERROR)
            os.chdir(work_cwd)
            return False
             
        work_list=[]
        #this is for control whether check the sub project
        check_all=False
        #this is for control whether checkout clean source code to source dir ,for source check,we can not do this,for it does not repo upload,
        #maybe I should write a new function ,but sorry
        clear_all=True
        if patch_list[0].strip() == "-a":
            check_all=True
            if len(patch_list) > 1:
                platform=patch_list[1].strip()
            else:
                platform=self.get_current_prj().split("_")[0]
            work_list=self.get_all_patchset(platform)
        elif patch_list[0].strip() == "-l":
            work_list,_=self.get_last_patchset(self.VANZO_PREFIX)
        elif patch_list[0].strip() == "-f":
            if len(patch_list) <= 1:
                my_dbg_vanzo(" -f need a inputfile",LEVEL_ERROR)
                os.chdir(work_cwd)
                return
            for file_name in patch_list[1:]:
                with open(file_name) as in_file:
                    lines=in_file.readlines()
                    for item in lines:
                        work_list.append(item.strip())
        elif patch_list[0].strip() == "-s":
            if len(patch_list) <= 1:
                my_dbg_vanzo(" -s need a inputsrc",LEVEL_ERROR)
                os.chdir(work_cwd)
                return
            check_all=True
            clear_all=False
            current_prj=self.get_current_prj()
            for file_name in patch_list[1:]:
                if self.verify_source(file_name) == False:
                    os.chdir(work_cwd)
                    return
                work_list.extend(self.get_related_patch(file_name))
        elif patch_list[0].strip() == "-p":
            project_name=""
            if len(patch_list) <= 1:
                project_name=self.get_current_prj()
            else:
                project_name=patch_list[1]
            input_cmd=raw_input("Warning!this is will clear all current project modify,are you sure?[y/n]\n")
            input_cmd=input_cmd.lower().strip()
            if input_cmd == "y" or input_cmd == "yes":
                if self.switch_to(project_name) == True:
                    self.clean()
                    self.update_po()
                    self.clean()
                    os.chdir(work_cwd)
                    return
                else:
                    my_dbg_vanzo("Error,not valid project_name",LEVEL_ERROR)
                    os.chdir(work_cwd)
                    return
            else:
                os.chdir(work_cwd)
                return
        elif patch_list[0].strip() == "-h":
            my_dbg_vanzo("Usage:check_conflict [-s source_code path] [-p project_name] [-a] or [just patchset path]",LEVEL_IMPORTANT)
            os.chdir(work_cwd)
            return
        else: 
            for patch_name in patch_list:
                if os.path.isdir(patch_name):
                    res,_,_,_=self.get_current_modified_file(patch_name)
                    work_list.extend(res)
                else:
                    if patch_name.find(".patchset.") < 0:
                        my_dbg_vanzo("Error %s format not correct"%(patch_name),LEVEL_ERROR)
                        continue
                    work_list.append(patch_name)
        #print "work_list is %s"%(work_list)
        work_list.sort()
        work_list=self.unique(work_list)
        #print "self.force:",self.force
            #search_dir=os.path.dirname(patch_name)
            #cwd=os.getcwd()
            #os.chdir(search_dir)
            #cmd="git add %s"%(patch_name)
            #my_sys_vanzo(cmd)
            #os.chdir(cwd)
        if len(work_list) < 1:
            my_dbg_vanzo("No valid patch",LEVEL_ERROR)
            os.chdir(work_cwd)
            return

        patch_project_map={}
        patch_list=[]
        if check_all == False:
            my_dbg_vanzo("Checking patch list:\n",LEVEL_HINT)
        for patch_name in work_list:
            if not os.path.exists(patch_name):
                continue
            patch_name=patch_name.strip().replace("//","/")
            patch_list.append(patch_name)
            if check_all == False:
                my_dbg_vanzo(patch_name,LEVEL_IMPORTANT)
        print "\n"
        for patch_name in patch_list:
            dot_index=patch_name.rfind(".")
            if dot_index < 0:
                continue
            suffix=patch_name[dot_index+1:]
            if suffix=="keep":
                continue
            if suffix=="delete":
                continue
            #fixme if this is not a mtk project
            if suffix[0:2] != "mt":
                continue
            dir_name=os.path.dirname(patch_name)
            search_dir=dir_name
            #print "search_dir:",search_dir
            #print "self.VANZO_PREFIX:",self.VANZO_PREFIX
            src_dir=search_dir.replace("//","/")
            if src_dir.startswith("vendor"):
                index=src_dir.find("vendor/")
                if index>=0:
                    index+=len("vendor/")
                    src_dir=src_dir[index:]
                    index=src_dir.find("/")
                    if index>0:
                        index+=1
                        src_dir=src_dir[index:]
            src_dir=src_dir.replace(self.VANZO_PREFIX,"")
            #src_dir=src_dir.replace(self.VANZO_PREFIX,"")
            src_dir=src_dir.replace("patch_projects/","")
            project_name_index=dot_index
            project_name=patch_name[project_name_index+1:]
            if dir_name in patch_project_map:
                if project_name == patch_project_map[dir_name]:
                        continue
            patch_project_map[dir_name]=project_name
            if clear_all==False:
                #here must consider we do not switch the different project,so when two project has the different remote git config,we do nothing
                if self.is_different_git_project(src_dir,current_prj,project_name):
                    my_dbg_vanzo("Warning! %s has different git remote address,so ignore"%(project_name),LEVEL_WARNING)
                    continue
                
            #print "dir_name %s,project_name %s"%(dir_name,project_name)
            if check_all == False:
                sub_projects=self.list_relatives(project_name,KIND_CHILD,True)
            else:
                sub_projects=[project_name]
            my_dbg_vanzo("Patch:%s\nRelated project list:%s"%(patch_name,sub_projects),LEVEL_IMPORTANT)
            for project in sub_projects:
                #print "project:",project
                project_name=self.npn_to_long_project(project)
                #print "Check Project:%s,src_dir %s,clear_all %s"%(project_name,src_dir,clear_all)
                print "Check Project:%s"%(project_name)
                #for this freeze branch do nothing
                if project_name.find("tphone-v1")>=0:
                    continue
                if project_name.find("freeze")>=0:
                    continue
                project_info=self.get_project_info(project_name)
                if not project_info:
                    my_dbg_vanzo("get_project_info error")
                    continue
                if clear_all == True:
                    if self.checkout_or_clone_dir(src_dir,project_name) == False:
                        my_dbg_vanzo("Error no manifest: %s"%(project_name),LEVEL_ERROR)
                        continue
                else:
                    self.clean_dir(src_dir)
                #cwd=os.getcwd()
                #os.chdir(search_dir)
                list_all=self.list_patchset_overlay_fast(project_name,"False",True,search_dir)
                #print "list_all is:",list_all
                origin_patchset_list,origin_overlay_dict=self.transer_to_vanzo_interface(list_all)
                origin_patchset_list.sort(self.cmp_time)
                #print "origin_patchset_list:",origin_patchset_list
                res=update_patchsets_vanzo(origin_patchset_list, project_info["project"],True)
                #os.chdir(cwd)
                #restore to origin branch
                my_dbg_vanzo("\n",LEVEL_IMPORTANT)
                if res == False and error_stop ==True:
                    os.chdir(work_cwd)
                    return res
                self.clean_dir(src_dir)
        os.chdir(work_cwd)
        return True

        #self.patch_files(origin_patchset_list)
    def transer_to_vanzo_interface(self,list_all=[]):
        origin_overlay_dict={}
        origin_patchset_list=[]
        work_cwd=os.getcwd()
#vanzo interface:('packages/apps/Phone', '/home/wangfei/src/codes/mtk_6572/mt72_z16ccl_w330_xindh_jb3_td_tphone_user/vendor/vanzo_custom/patch_projects/packages/apps/Phone/emergency_button_add_keytone.patchset.mt72_z5_c11_niao_gsm_lca')
#mediatek/custom/common/kernel/lcm/ili9488_hsd35_dj_hvga/ili9488.c vendor/vanzo_custom/overlay_projects/mediatek/custom/common/kernel/lcm/ili9488_hsd35_dj_hvga/ili9488.c.overlay.mt72_z5_c11_niao_gsm_lca
#me result:
#overlay_projects/vendor/overlay_res.overlay.all_projects
#patch_projects/frameworks/ipo_off.patchset.all_projects
        #print "self.VANZO_PREFIX:",self.VANZO_PREFIX
        #print "list_all:",list_all
        for item in list_all:
            if item.startswith("vendor"):
                index=item.find("vendor/")
                if index>=0:
                    index+=len("vendor/")+1
                    work_item=item[index:]
                    index=work_item.find("/")
                    index+=1
                    work_item=work_item[index:]
                else:
                    work_item=item
            else:
                work_item=item
            overlay_index=work_item.find("overlay_projects/")
            patchset_index=work_item.find("patch_projects/")
            len_overlay=len("overlay_projects/")
            len_patchset=len("patch_projects/")
            #print "work_item:",work_item
            if overlay_index>=0:
                key=work_item[overlay_index+len_overlay:]
                suffix_index=key.rfind(".overlay.")
                if suffix_index < 0:
                    continue
                key=key[:suffix_index]
                if work_item.endswith(".keep"):
                    if os.path.exists(self.VANZO_PREFIX+work_item):
                       	work_item=work_item[:-5]
                       	origin_overlay_dict[key]=self.VANZO_PREFIX+work_item
                elif work_item.endswith(".delete"):
                    if os.path.exists(self.VANZO_PREFIX+work_item):
                    	work_item=work_item[:-7]
                       	origin_overlay_dict[key]=self.VANZO_PREFIX+work_item
                else:
                    if os.path.exists(self.VANZO_PREFIX+work_item):
                       	origin_overlay_dict[key]=self.VANZO_PREFIX+work_item
            else:
                if work_item.endswith(".keep"):
                    my_dbg_vanzo("Warning...%s with .keep extension"%(work_item),LEVEL_WARNING)
                    continue
                elif work_item.endswith(".delete"):
                    my_dbg_vanzo("Warning...%s with .delete extension"%(work_item),LEVEL_WARNING)
                    continue
                dir_name=work_item[patchset_index+len_patchset:]
                base_index=dir_name.rfind("/")
                dir_name=dir_name[:base_index] 
                #if os.path.exists(work_cwd+"/"+self.VANZO_PREFIX+work_cwd):
                #print "self.VANZO_PREFIX:%s,work_item %s"%(self.VANZO_PREFIX,work_item)
                if os.path.exists(os.path.join(self.VANZO_PREFIX,work_item)):
                    origin_patchset_list.append([dir_name,os.path.join(self.VANZO_PREFIX,work_item)])
 
        #print origin_patchset_list
        #print origin_overlay_dict
        return origin_patchset_list,origin_overlay_dict

    def update_po(self,project_name="",only_check_conflict=False):
        bak_cwd=os.getcwd()
        res=self.to_root_dir()
        work_cwd=os.getcwd()
        if res == "":
            my_dbg_vanzo("Error,Can not find the .repo dir",LEVEL_ERROR)
            return

        tag = self.VANZO_PREFIX+"patch_done_tag.txt"
        if os.path.exists(tag):
            my_dbg_vanzo("already patched,if you want to repatch,pleaes remove %s"%(tag),LEVEL_ERROR)
            return

        if project_name == "":
            project_name=self.get_current_prj()
        else:
            project_name=project_name.lower().strip()
        #must do this before list else will error
        #print "project_name:",project_name
        self.exclude_target=[]
        self.long_project_name=project_name
        project_info=self.get_project_info(project_name)
        if not project_info:
            return
        if not only_check_conflict:
            do_pre_ugly_things_vanzo(project_name,project_info)
            
        list_all=self.list_patchset_overlay_fast(project_name,"False",True)
        origin_patchset_list,origin_overlay_dict=self.transer_to_vanzo_interface(list_all)

        #print "origin_patchset_list:",origin_patchset_list
        #print "origin_overlay_dict:",origin_overlay_dict

        update_patchsets_vanzo(origin_patchset_list, project_info["project"])
        if not only_check_conflict:
            update_overlays_vanzo(origin_overlay_dict)
            do_concat_files_vanzo(project_name)
            do_post_ugly_things_vanzo(project_name,project_info)
            shutil.copy('build/tools/update_overlay_files.py', '.')
            subprocess.check_call(shlex.split('touch ' + tag))
        return
    #def copy_requests(self,src_project_name="",dst_project_name="",src_reqeuest="",src_dir="",dst_request="",dst_dir=""):
    def copy_requests(self,para_list):
        cwd=self.to_root_dir()
        src_project_name=""
        dst_project_name=""
        src_reqeuest=""
        src_dir=""
        dst_request=""
        dst_dir=""
        try:
            src_project_name=para_list[0]
            dst_project_name=para_list[1]
            src_reqeuest=para_list[2]
            src_dir=para_list[3]
            dst_request=para_list[4]
            dst_dir=para_list[5]
        except:
            pass
        if cwd == "":
            my_dbg_vanzo("Error, do not find the .repo",LEVEL_ERROR)
            sys.exit()
        #print "self.VANZO_PREFIX:",self.VANZO_PREFIX
        src_lines=[]
        dst_lines=[]
        if src_project_name=="":
            src_project_name=self.get_current_prj()
        if dst_project_name=="":
            dst_project_name=self.get_current_prj()
        if dst_project_name=="":
            my_dbg_vanzo("Error src_project_name or dst_project_name can only one empty",LEVEL_ERROR)
            return
        if src_reqeuest=="" and dst_request=="":
            src_lines=self.list_patchset_overlay_fast(src_project_name,"False",True)
            dst_lines=self.list_patchset_overlay_fast(dst_project_name,"False",True)
        elif src_reqeuest!="" and dst_request =="":
            if not os.path.exists(src_reqeuest):
                my_dbg_vanzo("Error,src_request must be a file name or empty",LEVEL_ERROR)
                return
            with open(src_reqeuest) as src_file:
                src_lines=src_file.readlines()
            dst_lines=self.list_patchset_overlay_fast(dst_project_name,"False",True)
        elif src_reqeuest=="" and dst_request!="":
            with open(dst_request) as dst_file:
                dst_lines=dst_file.readlines()
            src_lines=self.list_patchset_overlay_fast(src_project_name,"False",True)
        elif src_reqeuest !="" and src_reqeuest != "":
            if not os.path.exists(src_reqeuest) or not os.path.exists(dst_request):
                my_dbg_vanzo("Error,src_request or dst_request must be a file name or empty",LEVEL_ERROR)
                return
            #this is the file case
            with open(src_reqeuest) as src_file:
                src_lines=src_file.readlines()
            with open(dst_request) as dst_file:
                dst_lines=dst_file.readlines()
        else:
            my_dbg_vanzo("Usage:copy_requests src_project_name dst_project_name [src_po_filename] [dst_po_filename]",LEVEL_IMPORTANT)
            return

        src_lines.sort()
        dst_lines.sort()
        list_diff=list(set(src_lines).difference(set(dst_lines)))
        print "list_diff:",list_diff
        src_copy_list=[]
        dst_copy_list=[]
        src_project_info=self.get_project_info(src_project_name)
        dst_project_info=self.get_project_info(dst_project_name)
        if not dst_project_info or not src_project_info:
            return
        npn_dst_project_name=npn_vanzo(dst_project_name)
        for item in list_diff:
            #here to copy the request
            #overlay_projects/vendor/google/userdata/Android.mk.custom.overlay.all_nand_projects
            #overlay_projects/mediatek/config/vanzo72_wet_lca/ProjectConfig.mk.custom.overlay.mt72_z5_c11_niao_wcdma_lca
            item=item.strip()
            index=-1
            dst_name=""
            if item.find("overlay_projects/") == 0:
                #here is overlay
                index=item.rfind(".overlay.")
                if index < 0:
                    my_dbg_vanzo("Error,not find the overlay symbol:%s"%item,LEVEL_ERROR)
                    continue
                dst_name=item[:index]+".overlay."+npn_dst_project_name
            elif item.find("patch_projects/") == 0:
                index=item.rfind(".patchset.")
                if index < 0:
                    my_dbg_vanzo("Error,not find the overlay symbol:%s"%item,LEVEL_ERROR)
                    continue
                dst_name=item[:index]+".patchset."+npn_dst_project_name

            if item.rfind(".all_")>=0:
                my_dbg_vanzo("Warning!file:%s is a all_ type overlay,please copy yourself!"%item,LEVEL_WARNING)
                continue
            dst_name=dst_name.replace(src_project_info["project"],dst_project_info["project"])
            if src_dir=="":
                src_copy_list.append(os.path.join(self.VANZO_PREFIX,item))
            else:
                src_copy_list.append(os.path.join(src_dir,item))
            if dst_dir=="":
                dst_copy_list.append(os.path.join(self.VANZO_PREFIX,dst_name))
            else:
                dst_copy_list.append(os.path.join(dst_dir,dst_name))
        print "src_copy_list:%s"%src_copy_list
        print "dst_copy_list:%s"%dst_copy_list
        self.copy_file_list(src_copy_list,dst_copy_list,False)
            
    
                
    def get_manifest_remote_address(self,project_name):
        project_info=self.get_project_info(project_name)
        if not project_info:
            return None
        repo_address=project_info["repo"]
        #print "repo_address:",repo_address
        manifest_address="ssh://vanzo/"+repo_address+"/manifest.git"
        #print "manifest_address:",manifest_address
        return manifest_address
    def check_out_repo_manifest(self,project_name):
        path=".repo/manifests"
        if not os.path.exists(path):
            my_sys_vanzo("mkdir -p " + path)
        manifest_address=self.get_manifest_remote_address(project_name)
        cmd="git clone %s %s"%(manifest_address,path)
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("git clone %s error"%(manifest_address),LEVEL_ERROR)
            return False
        return True
    def is_recent_project(self,project_name):
        if self.recent_project_list:
            if project_name in self.recent_project_list:
                return True
            if self.npn_to_long_project(project_name) in self.recent_project_list:
                return True

        dailybuild_list=os.path.expanduser('~')+"/build_projects/scripts/dailybuild_all_projects.txt"
        if not os.path.exists(dailybuild_list):
            my_dbg_vanzo("Warning!Can not find the dailybuild_all_projects!",LEVEL_WARNING)
            return False
        self.recent_project_list=[]
        with open(dailybuild_list) as in_file:
            lines = in_file.readlines()
            for item in lines:
                self.recent_project_list.append(item.lower().strip())
        if project_name in self.recent_project_list:
            return True
        if self.npn_to_long_project(project_name) in self.recent_project_list:
            return True
        return False
    def try_push_to_server(self,git_dir=None,direct_to_server=False,dry_run=False):
    #def try_push_to_server(self,git_dir=None,direct_to_server=False,dry_run=True):
        #last_commit_log = commands.getstatusoutput("git show HEAD^ -s")[1].split("\n")[0].split()[1]
        cwd=os.getcwd()
        if git_dir==None:
            git_dir=cwd
        os.chdir(git_dir)
        cmd="git log -n 10 --pretty=oneline"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        commit_list=stdoutdata.split("\n")
        id_list=[]
        for item in commit_list[1:]:
            item=item.strip()
            if item<1:
                continue
            item_list=item.split()
            if len(item_list)<1:
                continue
            id_list.append(item_list[0])
        #print "id_list:",id_list
        #last_commit_log=" ".join(id_list)
        cmd="git branch -rv"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        branch_status = stdoutdata.split("\n")
        #print "branch_status %s"%(branch_status)
        remote_address = ""
        if direct_to_server:
            #for direct push to server
            gerrit_or_server = "heads"
        else:
            #for push to gerrit
            gerrit_or_server = "for"
        remote_branch = ""
        cmd="git rev-parse --git-dir"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("get git dir error",LEVEL_ERROR)
            os.chdir(cwd)
            return False,"",""
        git_dir=stdoutdata.strip().split("\n")[0]
        start_id=""
        match_list=[]
        for one_id in id_list:
            for line in branch_status:
                if "tphone-v" in line:
                    continue
                one_branch= line.strip()
                if len(one_branch)<1:
                    continue
                branch_and_log = one_branch.split()
                #print "line:",line
                filename=os.path.join(git_dir,"refs/remotes/",branch_and_log[0])
                #print "filename:",filename
                commit_id=""
                if not os.path.exists(filename):
                    commit_id=branch_and_log[1].strip()
                    #continue
                else:
                    with open(filename) as in_file:
                        line=in_file.readlines()
                        commit_id=line[0].strip()
                #print "commit_id:",commit_id
                #if commit_id == one_id:
                if one_id.startswith(commit_id):
                    remote_address= branch_and_log[0].strip().split("/")[0]
                    '''
                    if remote_branch != "": 
                        print "Sorry now not support,more than one branch old:git push %s HEAD:refs/%s/%s,new:branch_and_log:%s" % (remote_address, gerrit_or_server,remote_branch,branch_and_log)
                        return False,"",""
                    '''
                    remote_branch = branch_and_log[0].strip().split("/")[-1]
                    #print "one_match:remote_address %s,remote_branch:%s"%(remote_address,remote_branch)
                    match_list.append([commit_id,remote_address,remote_branch])
                    #here we do not check the duplicate
        
        #print "match_list:",match_list
        lens=len(match_list)
        if lens > 0:
            if lens > 1:
                hint="which remote server and branch do you want to push:\n"
                for i in xrange(0,lens):
                    hint+="%d:remote server %s ,branch %s\n"%(i+1,match_list[i][1],match_list[i][2])
                hint+="[1-%d]1?"%(lens)
                answer=self.get_user_answer(hint,True)
                print "answer:",answer
                if answer=="":
                    index=1
                else:
                    index=int(answer)
                if index<1 or index>lens:
                    my_dbg_vanzo("Error,please input a number between 1 and %d"%(lens),LEVEL_ERROR)
                    os.chdir(cwd)
                    return False,"",""
                match=match_list[index-1]
            else:
                match=match_list[0]
            start_id=match[0]
            remote_address=match[1]
            remote_branch=match[2]
            cmd="git push %s HEAD:refs/%s/%s" % (remote_address, gerrit_or_server,remote_branch)
            if dry_run:
                #print "push cmd:",cmd
                os.chdir(cwd)
                return True,cmd,start_id
            else:
                returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
                os.chdir(cwd)
                if returncode != 0:
                    return False,cmd
                return True,cmd,start_id
                 
        os.chdir(cwd)
        return False,"",""
        '''
        origin/HEAD
        if "remotes/vanzo" in one_branch and branch_and_log[1].strip() in last_commit_log:
            remote_address = "vanzo"
            if remote_branch != "": 
                print "Sorry now not support,more than one branch: git push %s HEAD:refs/%s/%s" % (remote_address, gerrit_or_server,remote_branch)
                return False,""
            remote_branch = branch_and_log[0].strip().split("/")[-1]
        elif "remotes/origin" in one_branch and branch_and_log[1].strip() in last_commit_log:
            remote_address = "origin"
            if remote_branch != "": 
                print "more than one branch: git push %s HEAD:refs/%s/%s" % (remote_address, gerrit_or_server,remote_branch)
                return False,""
            remote_branch = branch_and_log[0].strip().split("/")[-1]
        '''

    def get_git_branch(self,dir_name=None):
        if not dir_name or len(dir_name)<1:
            dir_name=os.getcwd()
        if not os.path.exists(dir_name):
            my_dbg_vanzo("Error,not exist dir:%s"%(dir_name),LEVEL_ERROR)
            return None,None
        cwd=os.getcwd()
        os.chdir(dir_name)
        cmd="git branch"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        branch_list=stdoutdata.split("\n")
        current_branch=""
        #print "branch_list:",branch_list
        for item in branch_list:
            item=item.strip()
            if item.startswith("*"):
                index = item.find("*")
                item=item[index+1:].strip()
                current_branch=item
                break
        os.chdir(cwd)
        if current_branch.find("no branch")>=0:
            return None,branch_list
        #print "current_branch:",current_branch
        return current_branch,branch_list
        
                
        
        
    def commit_to_local(self,git_dir,file_list=None,add_only=False,commit_log=None,auto=False):
        cwd=os.getcwd()
        #print "file_list:",file_list
        if not file_list:
            file_list=["."]
            #commit_dir=os.getcwd()
            #current_branch,branch_list=self.get_git_branch()
        #else:
            '''
            commit_dir=os.path.dirname(file_list[0])
            if not commit_dir or len(commit_dir)<1:
                commit_dir=os.getcwd()
            print "commit_dir:",commit_dir
            '''
        current_branch,branch_list=self.get_git_branch(git_dir)
        #print "current_branch:%s,branch_list:%s"%(current_branch,branch_list)
        if not current_branch or len(current_branch)<1:
            #my_dbg_vanzo("Error you must be on a branch,if you have a .repo,then you can execute repo start x .",LEVEL_ERROR)
            if auto==False:
                    hint="Now on no branch state,whether repo start a temp branch?[Y/N]Y?"
                    answer=self.get_user_answer(hint)
                    if answer.lower() == "n":
                        return False
            branch_name="auto_commit_branch"
            #print "branch_name:%s,branch_list:%s"%(branch_name,branch_list)
            for item in branch_list:
                if item.strip()==branch_name:
                    delete_cmd="git branch -D auto_commit_branch"
                    cmd="cd %s;%s;cd - >/dev/null"%(git_dir,delete_cmd)
                    returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
                    #print "Delete branch auto_commit_branch:%d,%s"%(returncode,stderrdata)
                    break
            cmd="cd %s;repo start %s .;cd - >/dev/null"%(git_dir,branch_name)
            returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
            if returncode != 0:
                my_dbg_vanzo("create branch %s error!"%(branch_name),LEVEL_ERROR)
                return False
                    
        os.chdir(git_dir)
        cmd="git add"
        for item in file_list:
            cmd=cmd+" %s"%(item)
        #print "cmd add is:",cmd
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("git add error:%s"%(stderrdata),LEVEL_ERROR)
            os.chdir(cwd)
            return False

        if add_only==True:
            os.chdir(cwd)
            return True
        cmd="git commit"
        for item in file_list:
            cmd=cmd+" %s"%(item)
        if not commit_log or len(commit_log)<1:
            input_log=raw_input("please input commit log:\n")
        else:
            input_log=commit_log
        input_log+=" by auto commit tool"
        cmd+=" -m \"%s\""%(input_log)
        #print "cmd2:",cmd
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("git commit error:%d,%s,%s"%(returncode,stdoutdata,stderrdata),LEVEL_ERROR)
            os.chdir(cwd)
            sys.exit()
            return False
        os.chdir(cwd)
        return True
        
    def get_cared_files(self,root_dir,dir_name,all_file=False):
        if not dir_name:
            return []
        cwd=os.getcwd()
        os.chdir(root_dir)
        #care_list=[".py",".java",".xml",".mp3",".ogg",".cpp",".c",".mk"]
        cmd="find %s"%(dir_name)
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            #my_dbg_vanzo("Error find %s error"%(dir_name),LEVEL_ERROR)
            os.chdir(cwd)
            return [dir_name]
        all_list=stdoutdata.split("\n")
        result_list=[]
        for item in all_list:
                if os.path.isdir(item):
                    continue
                file_name=os.path.basename(item)
                #print "file_name:",file_name
                if file_name.startswith("."):
                    continue
                if all_file:
                    result_list.append(item)
                    continue
                index=file_name.find(".overlay.")
                if index>=0:
                    if item not in result_list:
                        result_list.append(item)
                        continue
                index=file_name.find(".patchset.")
                if index>=0:
                    if item not in result_list:
                        result_list.append(item)
                        continue
                _,suffix=os.path.splitext(file_name)
                if not suffix or len(suffix)<1:
                    continue
                if not suffix in self.care_list:
                    continue
                if item not in result_list:
                    result_list.append(item)
        os.chdir(cwd)
        return result_list
    def get_all_apks_from_mk(self,file_path):
        regex=re.compile("\s*copy_from\s*:=")
        begin=False
        results=[]
        with open(file_path) as in_file:
            lines=in_file.readlines()
            for item in lines:
                if begin==False:
                    if re.match(regex,item):
                        begin=True
                        continue
                else:
                    work_item=item.strip()
                    index=work_item.find("\\")
                    if index>=0:
                        work_item=work_item[:index].strip()
                    if len(work_item)>0:
                        results.append(work_item)
                    #fixme if the apkname includes the "/"
                    if index < 0:
                        break
        #print "results:",results
        return results
    def get_search_dir(self,dir_name):
        if not os.path.exists(dir_name):
            return None
        cwd=os.getcwd()
        os.chdir(dir_name)
        cmd="git rev-parse --git-dir"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("get git dir error",LEVEL_ERROR)
            os.chdir(cwd)
            return None
        git_dir=stdoutdata.strip().split("\n")[0]
        if git_dir == ".git":
            git_dir = dir_name
        else:
            git_dir=os.path.dirname(git_dir)

        os.chdir(cwd)
        return git_dir

    def get_kernel_dir(self):
        #kernel_dir="kernel-3.4"
        kernel_list=glob.glob("kernel-*")
        if len(kernel_list)!=1:
            my_dbg_vanzo("Error,Can not find kernel dir\n",LEVEL_ERROR)
            return False,"Error work dir"
        kernel_dir=kernel_list[0]
        return True,kernel_dir

    def commit_to_server(self,file_list=None,commit_log=None,auto=False):
        search_list=[]
        cwd=os.getcwd()
        #care_list=[".py",".java",".xml",".mp3",".ogg",".cpp",".c",".mk"]
        #print "file_list:",file_list
        cache_only=False
        if not commit_log:
            commit_log=""
        if not file_list:
            search_list=[cwd]
        else:
            #for file_name in file_list:
            lens=len(file_list)
            skip=False
            for i in xrange(0,lens):
                #if not os.path.exists(file_name):
                    #my_dbg_vanzo("Error,no such file:%s"%(file_name),LEVEL_ERROR)
                    #return False
                file_name=file_list[i]
                if skip:
                    if os.path.exists(file_name):
                        skip=False
                    else:
                        commit_log+=" "+file_name
                        continue
                #print "file_name:",file_name
                if file_name == "-m":
                   #print "find -m"
                    #commit_log="".join(file_list[i+1:])
                    #break
                    #print "commit_log:",commit_log
                    skip=True
                    continue
                if file_name == "-c":
                    cache_only=True
                    continue

                search_mode=False
                if os.path.isdir(file_name):
                    cmd="find %s -name .git"%(file_name)
                    returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
                    if returncode==0 and len(stdoutdata.strip())>0:
                        search_dir=file_name
                        search_mode=True
                    else:
                        search_dir=self.get_search_dir(os.path.dirname(file_name))
                else:
                    #search_dir=os.path.dirname(file_name)
                    search_dir=self.get_search_dir(os.path.dirname(file_name))
                print "search_dir:",search_dir
                if not search_dir or len(search_dir)<1:
                    search_dir=cwd
                if not search_dir in search_list:
                    search_list.append(search_dir)
        #print "search_list:",search_list
        #print "commit_log:",commit_log
        if not search_list:
            search_list=[cwd]
            file_list=None
        for search_dir in search_list:
            if len(search_dir)<1:
                continue
            modified_patchset,modified_files,cached_list,notracked_list=self.get_current_modified_file(search_dir)
            print "modified_files:%s,modified_patchset %s,file_list:%s"%(modified_files,modified_patchset,file_list)
            commit_files=[]
            if modified_files and len(modified_files)>0:
                if not file_list:
                    commit_files.extend(cached_list)
                    #auto recognize the commit list
                    for item in modified_files:
                        #if not os.path.exists(item):
                            #continue
                        if cache_only:
                            break
                        results=self.get_cared_files(search_dir,item)
                        for modified_file in results:
                            if modified_file not in commit_files:
                                commit_files.append(modified_file)
                        '''
                        file_name=os.path.basename(item)
                        if file_name.startswith("."):
                            continue
                        index=file_name.find(".overlay.")
                        if index>=0:
                            if item not in commit_files:
                                commit_files.append(item)
                            continue
                        index=file_name.find(".patchset.")
                        if index>=0:
                            if item not in commit_files:
                                commit_files.append(item)
                            continue
                        _,suffix=os.path.splitext(file_name)
                        #print "suffix:",suffix
                        if not suffix or len(suffix)<1:
                            continue
                        if not suffix in self.care_list:
                            continue
                        if item not in commit_files:
                            commit_files.append(item)
                        '''
                        
                    #commit_files=modified_files
                else:
                    print "has file_list,search_mode:",file_list,search_mode
                    #modified_files means current modified files
                    for item in modified_files:
                        #file_list means user want to commit
                        for commit_item in file_list:
                            #if os.path.isdir(commit_item):
                            if search_mode:
                                #cached file always commit
                                for cached_file in cached_list:
                                    if not cached_file in commit_files:
                                        commit_files.append(cached_file)
                                if cache_only:
                                    continue 
                                if item not in commit_files:
                                    results=self.get_cared_files(search_dir,item)
                                    for modified_file in results:
                                        if modified_file not in commit_files:
                                            commit_files.append(modified_file)
                                    #commit_files.append(item)
                                break
                            else:
                                if cache_only:
                                    for cached_file in cached_list:
                                        if not cached_file in commit_files:
                                            commit_files.append(cached_file)
                                full_name=os.path.join(cwd,commit_item)+"/"
                                print "item:%s,full_name:%s"%(item,full_name)
                                #full_name=os.path.join(cwd,commit_item).split("/")
                                #if full_name.item in full_name:
                                if full_name.find(item)>=0:
                                    if item not in commit_files:
                                        commit_files.append(item)
                                    break
                        
                #print "commit_files:%s,commit_log:%s"%(commit_files,commit_log)
                print "commit_files:%s"%(commit_files)
                if len(commit_files)<1:
                    my_dbg_vanzo("Sorry can not find file to commit!",LEVEL_HINT)
                    return False
                if not file_list:
                    my_dbg_vanzo("Are you sure to commit files:\n",LEVEL_IMPORTANT)
                    for item in commit_files:
                        print item
                    answer=self.get_user_answer()
                    if answer.lower() == "n":
                        return False
                else:
                    my_dbg_vanzo("below files will be commited:",LEVEL_HINT)
                    for item in commit_files:
                        print item
                if commit_files and len(commit_files)>0:
                    res=self.commit_to_local(search_dir,commit_files,True,commit_log,auto)
                    if res != True:
                        my_dbg_vanzo("Sorry,git add error!",LEVEL_ERROR)
                        return False
                    if modified_patchset and len(modified_patchset)>0:
                        res=self.check_patch_conflict(modified_patchset,True)
                        if res != True:
                            my_dbg_vanzo("Sorry,has conflicts I can not submit",LEVEL_ERROR)
                            return False
                    else:
                        full_dir=os.path.abspath(search_dir)
                        root_dir=self.to_root_dir()
                        if root_dir != "":
                            patch_root_dir=os.path.normpath(self.VANZO_PREFIX)
                            #print "patch_root_dir:%s,cwd %s"%(patch_root_dir,os.getcwd())
                            if os.path.exists(patch_root_dir) and full_dir.find(patch_root_dir)<0:
                                check_src_list=[]
                                for src in commit_files:
                                    _,suffix=os.path.splitext(src)
                                    if suffix in self.care_list:
                                        src=os.path.join(search_dir,src)
                                        check_src_list.append(src)
                                check_src_list.insert(0,"-s")
                                print "check_src_list:",check_src_list
                                res=self.check_patch_conflict(check_src_list,True)
                                if res != True:
                                    my_dbg_vanzo("Sorry,has conflicts I can not submit",LEVEL_ERROR)
                                    return False
                    os.chdir(cwd)
                    res=self.commit_to_local(search_dir,commit_files,False,commit_log,auto)
                    if res != True:
                        my_dbg_vanzo("Sorry,commit to local error!",LEVEL_ERROR)
                        return False
                #res,_=self.try_push_to_server()
            #else:
            res,cmd,start_id=self.try_push_to_server(search_dir,False,True)
            if not res:
                #my_dbg_vanzo("%s donot has commit to push,maybe you need sync to remote server"%(search_dir),LEVEL_IMPORTANT)
                my_dbg_vanzo("Sorry get push server address and branch error,maybe no commit or donot sync to server!",LEVEL_ERROR)
                continue
            patch_list,modified_list=self.get_last_patchset(search_dir,start_id)
            #print "patch_list:",patch_list
            if len(modified_list)<1:
                my_dbg_vanzo("Warning!I can not get the last commit log,but I try to commit it for you,please check it yourself!",LEVEL_WARNING)
            elif len(patch_list)>0:
                res=self.check_patch_conflict(patch_list,True)
                if res != True:
                    my_dbg_vanzo("Sorry,last commit has conflicts I can not submit",LEVEL_ERROR)
                    return False
            '''
            res,_,_=self.try_push_to_server(search_dir)
            #print "res:",res
            if res != True:
                my_dbg_vanzo("Sorry,push to server error!",LEVEL_ERROR)
                return False
            '''
            os.chdir(search_dir)
            #print "here to run cmd:",cmd
            returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
            if returncode != 0:
                print "Commit failed!"
                os.chdir(cwd)
                return False
            os.chdir(cwd)
            print "Commit success!"
        return True


if __name__ == '__main__':
    worker=VanzoWorker()
    #worker.get_possible_ancestor(sys.argv[1])
    #worker.list_patchset_overlay(sys.argv[1])
    #worker.list_patchset_overlay_fast(sys.argv[1],"True")
    if len(sys.argv)>1:
        worker.commit_to_server(sys.argv[1:])
    else:
        worker.commit_to_server()
    #worker.list_patchset_overlay_fast(sys.argv[1],"True",False,sys.argv[2])
    #worker.update_po()
    #worker.patch_one_project(sys.argv[1],sys.argv[2])
    #worker.create_project_from(sys.argv[1],sys.argv[2])
    #worker.checkout_or_clone_dir("packages/apps/Mms")
    #worker.check_patch_conflict()
    #worker.check_patch_conflict(sys.argv[1])
    #if len(sys.argv) > 1:
    #    worker.list_diff_dir(sys.argv[1])
    #else:
    #    worker.list_diff_dir()
    #do_add_recommended_apks_vanzo(sys.argv[1])
    #worker.get_exclude_target_list(sys.argv[1])
    #print project_custom_get_fallback_vanzo(sys.argv[1],"vendor/vanzo_custom/fallback_extra.txt")







