#!/usr/bin/env python
#encoding=utf-8
#first author:wangfei
import os
import glob
import re
import sys
import shutil
import tempfile
import ConfigParser
from vanzo_worker import VanzoWorker
from bridge import *
from project import Project

class ProjectManager():
    def __init__(self,codes_root=None,is_custom_tool=False):
        self.is_custom_tool=is_custom_tool
        self.begin_dir=os.getcwd()
        self.worker=VanzoWorker()
        self.po_name="patch_overrides"
        if codes_root != None and os.path.isdir(codes_root):
            self.codes_root=codes_root
        else:
            self.codes_root=self.begin_dir
        self.COMPANY="vanzo"
        self.config_root="zprojects"
        self.compile_modem=-1
        self.eng = 0
        self.compile_script=os.path.join(self.config_root,"scripts","mk.sh")
        self.current_project=None
        self.external_project_name="VANZO_INNER_PM_PROJECT_NAME"
        if os.path.exists("vendor/mediatek/proprietary/bootable/bootloader/preloader/"):
            self.bigger_than_50=True
        else:
            self.bigger_than_50=False
            
        #here maybe changed for future codes base
        self.cmds_map={
        "new_project_from":self.new_project_from,
        "del_project":self.del_project,
        "compile":self.compile_project,
        "get_config_name":self.get_config_name,
        "get_modem_src":self.get_modem_src,
        "get_all_config_name":self.get_all_config_name,
        "get_all_macros_info":self.get_all_macros_info,
        "list_po":self.list_po,
        "get_project_macro":self.get_project_macro,

        }
    def parse_config(self,config_name):
        config_map={}
        paser = ConfigParser.ConfigParser()
        paser.optionxform=str
        paser.read(config_name)
        sections = paser.sections() 
        for sec in sections:
            config_map[sec] = dict(paser.items(sec))
        return config_map
    def get_all_config_map(self):
        with tempfile.NamedTemporaryFile() as tmp_out_path:
            for item in glob.glob("%s/*/env*.ini"%(self.config_root)):
                with open(item) as i:
                    tmp_out_path.write(i.read())
                    tmp_out_path.write('\n')
            tmp_out_path.flush()
            return self.parse_config(tmp_out_path.name)
        
    def get_kernel_dir(self):
        #kernel_dir="kernel-3.4"
        kernel_list=glob.glob("kernel-*")
        if len(kernel_list)!=1:
            my_dbg_vanzo("Error,Can not find kernel dir\n",LEVEL_ERROR)
            return False,"Error work dir"
        kernel_dir=kernel_list[0]
        return True,kernel_dir

    def create_board_project(self,new_name,base_name):
        '''
        preloader lk kernel android
        '''
        print "new_name:base_name\n",new_name,base_name
        res,kernel_dir=self.get_kernel_dir()
        if res==False:
            return res,kernel_dir
        search_list=["arch/arm","drivers/misc/mediatek/mach/"]
        returncode = 1
        stdoutdata = None
        stderrdata = None
        for item in search_list:
            cmd="find  %s/%s -maxdepth 2 -name %s"%(kernel_dir,item,base_name)
            #print cmd
            returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
            #print returncode,stdoutdata,stderrdata
            if returncode == 0 and len(stdoutdata) > 1:
                break
        error_info="Can not Guess the platform"
        if returncode != 0:
            return False,error_info
        base_project_path=stdoutdata.strip()
        if len(stdoutdata)<1:
            return False,error_info
        dir_name=os.path.dirname(base_project_path)
        mach_name=os.path.basename(dir_name)
        if mach_name.startswith("mach-"):
            platform=mach_name[5:]
        else:
            platform=mach_name
        print "platform:",platform
        modified_dir=[]
        pwd=os.getcwd()
        #for preloader
        if self.bigger_than_50:
            bootable_prefix="vendor/mediatek/proprietary"
        else:
            bootable_prefix=""

        os.chdir(os.path.join(bootable_prefix,"bootable/bootloader/preloader/custom"))
        os.system("rm -rf %s"%(new_name))
        os.system("cp -rf %s %s"%(base_name,new_name)) 
        os.system("mv %s/%s.mk %s/%s.mk"%(new_name,base_name,new_name,new_name))
        os.system("sed --follow-symlinks -i 's/%s/%s/g' %s/%s.mk"%(base_name,new_name,new_name,new_name))
        modified_dir.append(os.path.join(bootable_prefix,"bootable/bootloader/preloader/custom"))
        os.chdir(pwd)
        #for lk
        os.chdir(os.path.join(bootable_prefix,"bootable/bootloader/lk"))
        os.system("cp project/%s.mk project/%s.mk"%(base_name,new_name))
        os.system("rm -rf target/%s"%(new_name))
        os.system("cp  -a target/%s target/%s"%(base_name,new_name))
        os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' project/%s.mk"%(base_name,new_name,new_name))
        os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' target/%s/include/target/cust_usb.h"%(base_name,new_name,new_name))
        modified_dir.append(os.path.join(bootable_prefix,"bootable/bootloader/lk"))
        os.chdir(pwd)
        #for kernel old mode
        os.chdir("%s/arch/"%(kernel_dir))
        if os.path.exists("arm/mach-%s"%(platform)):
            os.system("rm -rf arm/mach-%s/%s"%(platform,new_name))
            os.system("cp  -a arm/mach-%s/%s arm/mach-%s/%s"%(platform,base_name,platform,new_name))
        if os.path.exists("arm/configs/%s_defconfig"%(base_name)):
            os.system("cp arm/configs/%s_defconfig arm/configs/%s_defconfig"%(base_name,new_name))
            os.system("cp arm/configs/%s_debug_defconfig arm/configs/%s_debug_defconfig"%(base_name,new_name))
            if os.path.exists("arm/boot/dts/%s.dts"%(base_name)):
                os.system("cp arm/boot/dts/%s.dts arm/boot/dts/%s.dts"%(base_name,new_name))
            os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' arm/configs/%s_defconfig"%(base_name,new_name,new_name))
            os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' arm/configs/%s_debug_defconfig"%(base_name,new_name,new_name))
        elif os.path.exists("arm64/configs/%s_defconfig"%(base_name)):
            os.system("cp arm64/configs/%s_defconfig arm64/configs/%s_defconfig"%(base_name,new_name))
            os.system("cp arm64/configs/%s_debug_defconfig arm64/configs/%s_debug_defconfig"%(base_name,new_name))
            #kernel-3.10/arch/arm64/boot/dts
            if os.path.exists("arm64/boot/dts/%s.dts"%(base_name)):
                os.system("cp arm64/boot/dts/%s.dts arm64/boot/dts/%s.dts"%(base_name,new_name))
            os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' arm64/configs/%s_defconfig"%(base_name,new_name,new_name))
            os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' arm64/configs/%s_debug_defconfig"%(base_name,new_name,new_name))
        else:
            print "Error,can not find the config dir"
            sys.exit(-1)
        
        modified_dir.append("%s/arch/"%(kernel_dir))
        os.chdir(pwd)
        #for kernel after 6732
        #kernel-3.10/drivers/misc/mediatek/mach/mt6752/vanzo6752_lwt_l/
        os.chdir("%s/drivers/misc/mediatek/"%(kernel_dir))
        if os.path.exists("mach/%s/%s"%(platform,base_name)):
            os.system("rm -rf mach/%s/%s"%(platform,new_name))
            os.system("cp  -a mach/%s/%s mach/%s/%s"%(platform,base_name,platform,new_name))
        os.chdir(pwd)
        #for android 
        os.system("rm -rf device/%s/%s"%(self.COMPANY,new_name))
        os.system("cp  -a device/%s/%s device/%s/%s"%(self.COMPANY,base_name,self.COMPANY,new_name))
        os.system("mv device/%s/%s/full_%s.mk device/%s/%s/full_%s.mk"%(self.COMPANY,new_name,base_name,self.COMPANY,new_name,new_name))
        modified_dir.append("device/%s/"%(self.COMPANY))
        os.system("rm -rf vendor/mediatek/proprietary/custom/%s"%(new_name))
        os.system("cp  -a vendor/mediatek/proprietary/custom/%s vendor/mediatek/proprietary/custom/%s"%(base_name,new_name))
        #os.system("sed  -i 's/'''%s'''/'''%s'''/g' device/%s/%s/AndroidBoard.mk"%(base_name,new_name,self.COMPANY,new_name))
        os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' device/%s/%s/AndroidProducts.mk"%(base_name,new_name,self.COMPANY,new_name))
        os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' device/%s/%s/BoardConfig.mk"%(base_name,new_name,self.COMPANY,new_name))
        os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' device/%s/%s/device.mk"%(base_name,new_name,self.COMPANY,new_name))
        os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' device/%s/%s/full_%s.mk"%(base_name,new_name,self.COMPANY,new_name,new_name))
        os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' device/%s/%s/vendorsetup.sh"%(base_name,new_name,self.COMPANY,new_name))
        if not os.path.islink("device/%s/%s/ProjectConfig.mk"%(self.COMPANY,new_name)):
                os.chdir("device/%s/%s/"%(self.COMPANY,new_name))
                os.system("ln -sf ../%s/ProjectConfig.mk ProjectConfig.mk"%(base_name))
                os.chdir(pwd)
        if os.path.exists("vendor/mediatek/proprietary/custom/%s/Android.mk"%(new_name)):
            os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' vendor/mediatek/proprietary/custom/%s/Android.mk"%(base_name,new_name,new_name))
        if os.path.exists("vendor/mediatek/proprietary/trustzone/project/%s.mk"%(base_name)):
            os.system("cp  -a vendor/mediatek/proprietary/trustzone/project/%s.mk vendor/mediatek/proprietary/trustzone/project/%s.mk"%(base_name,new_name))
            os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' vendor/mediatek/proprietary/trustzone/project/%s.mk"%(base_name,new_name,new_name))
        elif os.path.exists("vendor/mediatek/proprietary/trustzone/custom/build/project/%s.mk"%(base_name)):
            os.system("cp  -a vendor/mediatek/proprietary/trustzone/custom/build/project/%s.mk vendor/mediatek/proprietary/trustzone/custom/build/project/%s.mk"%(base_name,new_name))
            os.system("sed --follow-symlinks -i 's/'''%s'''/'''%s'''/g' vendor/mediatek/proprietary/trustzone/custom/build/project/%s.mk"%(base_name,new_name,new_name))
        else:
            print "Warning!!!can not find trustzone!"
        #copy board related flashlight
        #kernel-3.18/drivers/misc/mediatek/flashlight/src/mt6735
        flashlight_path = "%s/drivers/misc/mediatek/flashlight/src/%s"%(kernel_dir, platform)
        if os.path.exists("%s/%s"%(flashlight_path, base_name)):
            os.chdir(flashlight_path)
            os.system("cp -a %s  %s"%(base_name, new_name))
            os.chdir(pwd)
        #here should link preloader dct
        os.chdir(os.path.join(bootable_prefix,"bootable/bootloader/preloader/custom/%s/"%(new_name)))
        dst_file="../../../../../%s/arch/arm/mach-%s/%s/dct"%(kernel_dir,platform,new_name)
        if not os.path.exists(dst_file):
            dst_file="../../../../../%s/drivers/misc/mediatek/mach/%s/%s/dct"%(kernel_dir,platform,new_name)
        if not os.path.exists(dst_file):
            dst_file="../../../../../../../../%s/drivers/misc/mediatek/mach/%s/%s/dct"%(kernel_dir,platform,new_name)

        os.system("rm -rf dct")
        os.system("ln -sf %s dct"%(dst_file))
        os.chdir(pwd)
        #here should link lk dct
        os.chdir(os.path.join(bootable_prefix,"bootable/bootloader/lk/target/%s/"%(new_name)))
        os.system("rm -rf dct")
        os.system("ln -sf %s dct"%(dst_file))
        os.chdir(pwd)
        #here should link vendor dct
        os.chdir("vendor/mediatek/proprietary/custom/%s/kernel"%(new_name))
        dst_file="../../../../../../%s/arch/arm/mach-%s/%s/dct"%(kernel_dir,platform,new_name)
        if not os.path.exists(dst_file):
            dst_file="../../../../../../%s/drivers/misc/mediatek/mach/%s/%s/dct"%(kernel_dir,platform,new_name)
        if not os.path.exists(dst_file):
            dst_file="../../../../../../../../%s/drivers/misc/mediatek/mach/%s/%s/dct"%(kernel_dir,platform,new_name)
        os.system("rm -rf dct")
        os.system("ln -sf %s dct"%(dst_file))
        os.chdir(pwd)
        modified_dir.append("vendor/mediatek/proprietary/custom/")
    #for whether shared dynamic lib
        #for 5.0 can not copy or link the lib
        #os.system("rm -rf  vendor/%s/libs/%s"%(self.COMPANY,new_name))
        #os.system("cp -a vendor/%s/libs/%s vendor/%s/libs/%s"%(self.COMPANY,base_name,self.COMPANY,new_name))
        #modified_dir.append("vendor/%s/libs/"%(self.COMPANY))
        config_path=os.path.join(pwd,self.config_root,base_name)
        if os.path.exists(config_path):
            res,error_info=self.create_custom_project(new_name,base_name)
        else:
            res,error_info=self.create_custom_project(new_name)
        custom_cfg=os.path.join(self.config_root,"scripts","new_proj.cfg")
        #print  "custom_cfg:%s, res:%s"%(custom_cfg, res)
        if res:
            if os.path.exists(custom_cfg):
                env_file=os.path.join(self.config_root,new_name,"env_%s.ini"%(new_name))
                os.system("cat %s >> %s"%(custom_cfg,env_file))

        return res,error_info

    def create_custom_project(self,new_custom,base_custom=None):
        '''
        here base_custom can be none only in inner case,new a board project
        '''
        if not base_custom:
            #this is a board project just create some empty file
            #env file,binary dir includes logo and other binary ,packages.xml,overlay
            binary=os.path.join(self.config_root,new_custom,"binary")
            mkdir_p_vanzo(binary)
            env_file=os.path.join(self.config_root,new_custom,"env_%s.ini"%(new_custom))
            os.system("touch %s"%(env_file))
            packages=os.path.join(self.config_root,new_custom,"packages.xml")
            os.system("touch %s"%(packages))
            return True,None
        else:
            base_dir=os.path.join(self.config_root,base_custom) 
            new_dir=os.path.join(self.config_root,new_custom)
            cmd="cp -a %s %s"%(base_dir,new_dir)
            os.system(cmd)
            for current_src_root,dirs,files in os.walk(new_dir,False,None,True):
                for item in files:
                    cmd="sed  --follow-symlinks -i 's/%s/%s/g' %s"%(base_custom.lower(),new_custom.lower(),os.path.join(current_src_root,item))
                    os.system(cmd)
                    cmd="sed  --follow-symlinks -i 's/%s/%s/g' %s"%(base_custom.upper(),new_custom.upper(),os.path.join(current_src_root,item))
                    os.system(cmd)
            cmd="mv %s/env_%s.ini %s/env_%s.ini"%(new_dir,base_custom,new_dir,new_custom)
            print "cmd:",cmd
            os.system(cmd)
            
            return True,None

    def get_config_project_path(self,config_name):
        segments=config_name.split("-")
        lens=len(segments)
        '''
        if lens < 2:
            return False,"Error %s can only be a project not a config"
        '''
        cfg_path=None
        for i in xrange(lens,1,-1):
            cfg="-".join(segments[0:i])
            #print "cfg:",cfg
            cfg_path=os.path.join(self.config_root,cfg,"env_%s.ini"%(cfg))
            if os.path.exists(cfg_path):
                return cfg_path

        return None

    def append_config(self,config_path,config_list):
        with open(config_path,"a") as out_handle:
            for item in config_list:
                out_handle.write(item)

    def get_config_contents(self,config_path,config_name):
        start_regex=re.compile("^\s*\[\s*%s\s*\]\s*$"%(config_name)) 
        end_regex=re.compile("^\s*\[\s*\S+\s*\]\s*$") 
        
        write_list=[]
        start=False
        with open(config_path) as in_handle:
            for item in in_handle:
                if start:
                    write_list.append(item)
                elif re.match(start_regex,item):
                    start=True
                    write_list.append(item)
                elif re.match(end_regex,item):
                    if start:
                        break
        return write_list
        
    def create_custom_config(self,new_config,base_config=None):
        '''
        here base_config can be none only in inner case,new a empty config 
        '''
        new_config=new_config.strip()
        if not base_config:
            #first to get the project name
            segments=new_config.split("-")
            lens=len(segments)
            if lens < 2:
                return False,"Error %s can only be a project not a config"
            cfg_path=self.get_config_project_path(new_config)
            if not cfg_path:
                return False,"Error must create parent project first"
            with open(cfg_path,"a") as in_handle:
                line="[%s]"%(new_config)
                in_handle.write(line)
            return True,None
        else:
            base_config=base_config.strip()
            base_config_path=self.get_config_project_path(base_config)
            if not base_config_path:
                return False,"can not find %s or %s is not a config"%(base_config,base_config)
            config_contents=self.get_config_contents(base_config_path,base_config)

            out_list=[]
            for item in config_contents:
                    item=item.replace(base_config.lower(),new_config.lower())
                    item=item.replace(base_config.upper(),new_config.upper())
                    
                    out_list.append(item)

            new_config_path=self.get_config_project_path(new_config)
            if not new_config_path:
                return False,"can not find %s path"%(new_config)

            self.append_config(new_config_path,out_list)

        return True,None


    def new_project_from(self,parameter_list):
        #Usage new_project_from -b aaa bbb,means from bbb to create aaa
        if not parameter_list or len(parameter_list)<2:
            my_dbg_vanzo("Input parameter error",LEVEL_ERROR)
            return False,"Input error:%s"%(parameter_list)
        is_board=False
        is_config=False
        base_project_name=parameter_list[-1]
        new_project_name=parameter_list[-2]
        if len(parameter_list)>2:
            parameter=parameter_list[-3]
            if parameter == "-b":
                is_board=True
            elif parameter ==  "-c":
                is_config=True
        #is_board:True means this is a new borad project,else means this is a custom project base on some board
        my_dbg_vanzo("is_board %s,is_config %s\n"%(is_board,is_config),LEVEL_DBG)
        if is_board:
            res,error_info=self.create_board_project(new_project_name,base_project_name)
        elif is_config:
            res,error_info=self.create_custom_config(new_project_name,base_project_name)
        else:
            res,error_info=self.create_custom_project(new_project_name,base_project_name)
            
        print error_info
        return res,error_info

    def del_project(self,parameter_list):
        if len(parameter_list)<1:
            return False,"Error parameter"
        project_name=parameter_list[0]
        hint="Are you sure to remove project %s[y/n:n]"%(project_name)
        answer=raw_input(hint)
        answer=answer.lower()
        while answer!="y" and answer!="n" and answer!="":
            my_dbg_vanzo("can only input Y or N!",LEVEL_HINT)
            answer=raw_input(hint)
            answer=answer.lower()
        if answer == "":
            answer="n"
        if answer == "n":
            return True,None
        project_path=os.path.join(self.config_root,project_name)
        cmd="rm -rf %s"%(project_path)
        print "here to remove %s\n"%(project_path)
        os.system(cmd)
        return True,None


    def process_compile_parameter(self,para_list):
        #left to future
        #my_dbg_vanzo("Error,now do not realize\n",LEVEL_ERROR)
        if "-m" in para_list:
            self.compile_modem = 1
        elif "-d" in para_list:
            self.eng = 1
        elif "-ud" in para_list:
            self.eng = 2
        elif "-nm" in para_list:
            self.compile_modem = 0
    def before_compile(self,compile_modem):
        if compile_modem > 0:
            compile_modem = True
        else:
            compile_modem = False
        return self.current_project.before_compile(compile_modem)

    def after_compile(self):
        #here should do some clean job
        #Project.clean
        self.current_project.after_compile()
        #remove obj
        obj_path=os.path.join(self.config_root,"obj")
        if os.path.exists(obj_path):
            shutil.rmtree(os.path.join(self.config_root,"obj"))
        
            
    def get_inner_name(self,external_name):
        all_map=self.get_all_config_map()
        for config_name,config_map in all_map.items():
            if self.external_project_name in config_map:
                if config_map[self.external_project_name].lower()==external_name:
                    return config_name
    def get_all_config_name(self,parameter_list):
        cmd="cat zprojects/*/*.ini|grep -o '\[.*\]'"
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        #print "res:",returncode,stdoutdata,stderrdata
        if returncode == 0:
            return stdoutdata,None
        else:
            return False,"Error to get config name"


    def get_patch_and_overrides(self,current_project):
        from plugins import PatchOverride
        po_plugin=PatchOverride(True)
        po_plugin.process_patch_override(None,current_project.product_map)
        
    def get_project_macro(self,parameter_list):
        config_name,error_info=self.get_config_name(parameter_list,True)
        if config_name == False:
            print '%s error'%(parameter_list[0])
            return config_name,error_info
        current_project=Project(config_name,False)
        keyes=parameter_list[1:]
        for item in keyes:
            if item in current_project.product_map:
                print '%s=%s'%(item,current_project.product_map[item])
            else:
                my_dbg_vanzo('No such key in project',LEVEL_ERROR) 
        return None,None
    def list_po(self,parameter_list):
        for item in parameter_list:
            item=item.strip()
            config_name,error_info=self.get_config_name([item],True)
            if config_name == False:
                print '%s error'%(config_name)
                return item,error_info
            item=config_name
            if item.find('-') < 0:
                continue
            try:
                current_project=Project(item,False)
            except Exception,e:
                print 'Project %s error'%(item)
                continue
            print '%s po:\n'%(item)
            self.get_patch_and_overrides(current_project)
            print '\n'

        return None,None
        
    def get_all_macros_info(self,parameter_list):
        configs,error_info = self.get_all_config_name(parameter_list)
        if error_info:
            return False,error_info
        configs=configs.strip().replace('[','').replace(']','').split('\n')
        #print configs
        whole_huge_map={}
        current_project=None
        for item in configs:
            #here to filter the virtual project or board project
            if item.find('-') < 0:
                continue
            try:
                current_project=Project(item,False)
            except Exception,e:
                continue
            current_map=current_project.get_config_macro_history()
            whole_huge_map.update(current_map)
            
        print whole_huge_map
        return whole_huge_map,None
    def get_modem_src(self,parameter_list):
        res,error_info=self.get_config_name(parameter_list)
        if res == False:
            return res,error_info
        config_name=res
        self.current_project=Project(config_name,False)
        config_map=self.current_project.product_map
        if 'CUSTOM_MODEM' not in config_map:
            my_dbg_vanzo("Error project %s do not have modem config"%config_name,LEVEL_ERROR)
            return False,"No modme Config"
        modem_dir=config_map['CUSTOM_MODEM']
        print '###modem_src:',modem_dir
        return modem_dir,None
                
    def get_config_name(self,parameter_list,quiet=False):
        if len(parameter_list)<1:
            my_dbg_vanzo("Error,must supply a long project name\n",LEVEL_ERROR)
            return False,"must supply a project config name"
        config_name=parameter_list[0].lower().strip()
        if  config_name.startswith("mt"):
            inner_config_name=self.get_inner_name(config_name)
            if not inner_config_name:
                my_dbg_vanzo("Error,no such project:%s"%(config_name),LEVEL_ERROR)
                return False,"no such project %s"%(config_name)
            config_name = inner_config_name
        #self.current_project=Project(config_name,False)
        #print config_name,self.current_project.current_platform
        if not quiet:
            print config_name
        return config_name,None

    def compile_project(self,parameter_list):
        if len(parameter_list)<1:
            my_dbg_vanzo("Error,must supply a project config name\n",LEVEL_ERROR)
            return False,"must supply a project config name"
        
        lens=len(parameter_list)
        print "parameter_list:",parameter_list,lens
        config_name=parameter_list[0].lower()
        i=1
        for i in xrange(1,lens):
            print "i:",i
            if parameter_list[i].startswith("-"):
                self.process_compile_parameter(parameter_list[i:])
            else:
                compile_cmd=" ".join(parameter_list[i:])
                break
        else:
            if self.compile_modem < 0:
                self.compile_modem=1
            compile_cmd="make -j32"
        print "compile_modem,compile_cmd:",self.compile_modem,compile_cmd
        if  config_name.startswith("mt"):
            inner_config_name=self.get_inner_name(config_name)
            if not inner_config_name:
                my_dbg_vanzo("Error,no such project:%s"%(config_name),LEVEL_ERROR)
                return False,"no such project %s"%(config_name)
            config_name = inner_config_name

        self.current_project=Project(config_name)
        '''
        if lens==index+1:
            compile_cmd="make -j32"
        else:
            compile_cmd=" ".join(parameter_list[index+1:])
        '''
        self.before_compile(self.compile_modem)
        cmd="%s %s %s %s"%(self.compile_script,self.current_project.project_name,self.eng,compile_cmd)
        print "cmd:",cmd
        #returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        #print "res:",returncode,stdoutdata,stderrdata
        res=os.system(cmd)
        print "compile result:",res

        self.after_compile()
        if res != 0:
            return False,"Compile error!"

        return True,None
        

    def dispatch(self,cmd,parameter_list):
        os.chdir(self.codes_root)
        res = False
        error_info="Sorry do not support such cmd:%s"%(cmd)
        for key,value in self.cmds_map.items():
            if key == cmd:
                res,error_info=value(parameter_list)
                break 

        os.chdir(self.begin_dir)
        if res == False:
            sys.exit(-1)
        else:
            sys.exit(0)

        return res,error_info


if __name__ == '__main__':
    manager=ProjectManager()
    manager.dispatch(sys.argv[1],sys.argv[2:])
    #manager.new_project_from(sys.argv[1:])
    #manager.compile_project(sys.argv[1:])
    sys.exit()
