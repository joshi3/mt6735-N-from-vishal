from BasePlugin import BasePlugin
from bridge import *
import os
import os.path
import xml.dom.minidom
import copy
from Responsible import *
#we do not encourage use patch and override,but for sometimes ,we do need it,just like the go statements,so,then...
class Po(object):
    def __init__(self, name):
      self.name = name
      self.files = []

    def  add_file(self, src, label=None): 
      self.files.append((src, label))
class Poes(object):
  def __init__(self, name):
    self.poes= {}
    self.__parse_xml(name)

  def __parse_xml(self, fname):  

    #print "in __parse_xml fname:",fname
    if not os.path.exists(fname):
        #print "Warning! in __parse_xml %s not exist!"%(fname)
        return

    root = xml.dom.minidom.parse(fname)

    root = root.childNodes[0]

    for node in root.childNodes:
      if node.nodeName == 'po':
        name = node.getAttribute('name')
        if name == '':
          continue
        
        p = Po(name)
        for i in node.childNodes:
          if i.nodeName == 'file':
            src = i.getAttribute('src')
            label = i.getAttribute('label')
            p.add_file(src, label)

        self.poes[name] = p
  
  def get_po_file_list(self, name):
    if not self.poes.has_key(name):
        index_dollar=name.find('$')
        index_minus=name.find('-')
        choosed=[] 
        minused=[]
        if index_dollar > 0:
            real_name=name[:index_dollar] 
            if index_minus > 0:
                choosed=name[index_dollar+1:index_minus].split('$')
                minused=name[index_minus+1:].split('-')
            else:
                choosed=name[index_dollar+1:].split('$')
        elif index_minus > 0: 
            real_name=name[:index_minus] 
            minused=name[index_minus+1:]
        else:
            assert False,'poes not found %s\n' % (name)
            return []
        if not self.poes.has_key(real_name):
            assert False,'poes not found: %s\n' % (real_name)
            return []
        all_list=self.poes[real_name].files
        #print "real_name,all_list,choosed",real_name,all_list,choosed
        choosed_list=[]
        for (src,label)in all_list:
            print 'src,label',src,label
            #if label and (label in choosed) and (label not in minused):
            if label and (label in choosed):
                choosed_list.append((src,label))
        if index_dollar>0 and len(choosed_list)<1:
            print 'You config must be error:',name
            sys.exit(-1)
        if len(choosed_list)<1:
            choosed_list = all_list

        choosed_list=[item for item in choosed_list if not item[1] or (item[1] not in minused)]
        
        print "choosed_list:",choosed_list
        return choosed_list
    
    return self.poes[name].files

  def overlay(self, filepath):
    self.__parse_xml(filepath)

class PatchOverride(BasePlugin):
    def __init__(self,only_show=False):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_INNER_USE_PATCH_OVERRIDE":self.process_patch_override}
        self.out_lines=[]
        self.config_root="zprojects"
        self.po_name="patch_overrides"
        self.patch_bak_suffix="patch.ori"
        self.patched_label="patched_label_remove_me_if_need_repatch"
        self.overlayed_label="{}/overlayed_label_remove_me_if_need_reoverlay".format(self.config_root)
        self.only_show=only_show
        self.current_patches={}
        self.current_overrides={}
        self.patch_dir_name="patches"
        self.overrides_dir_name="overrides"

    def process(self,config_map):
        for item,out_key in self.match_item.items():
            #print "item,out_key",item,out_key
            if item not in config_map:
                continue
            value=config_map[item].strip()
            if len(value)<1 or value.lower()!="yes":
                continue
            if not out_key:
                print "Sorry %s now not supported custom"%(item)
                continue
            method=out_key
            res,error_info=method(item,config_map)
            if res < 0:
                print "process %s error"%(item)
                return -1,error_info
            else:
                if error_info:
                    self.out_lines.extend(error_info)
        return 1,self.out_lines

    def get_real_po_list(self,poes):
        work_list=[]
        result_list=[]
        origin_list=poes.split()
        origin_list.reverse()
        for item in origin_list:
            clean_item=item
            index_colon=clean_item.find(':')
            if index_colon>0:
                clean_item=clean_item[:index_colon]
            index_minus=clean_item.find('-')
            if index_minus>0:
                clean_item=clean_item[:index_minus]
            index_dollar=clean_item.find('$')
            if index_dollar>0:
                clean_item=clean_item[:index_dollar]
            if clean_item not in work_list:
                work_list.append(clean_item)
                result_list.insert(0,item)

        #print 'result_list:',result_list
        return result_list

    def get_po_list_from_dir(self,dir_name):
        #print 'in get_po_list_from_dir the dir_name:',dir_name
        cmd="find %s -type f -name '*.patch' "%(dir_name)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            return -1,"find %s error"%(dir_name)
        patches=stdoutdata.strip().split("\n")
        cmd="find %s -type l -name '*.patch' "%(dir_name)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            return -1,"find %s error"%(dir_name)
        patches.extend(stdoutdata.strip().split("\n"))

        cmd="find %s -name '*.override.*' "%(dir_name)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            overrides=""
        else:
            overrides=stdoutdata.strip().split("\n")
        #print 'patches:',patches
        #print 'overrides:',overrides
        real_patches=[]
        real_overrides=[]
        for item in patches:
            if len(item.strip())>=1:
               real_patches.append(item) 
        for item in overrides:
            if len(item.strip())>=1:
                real_overrides.append(item)
        return real_patches,real_overrides

    def preprocess_patches(self,patches_list,patches_map={}):
        #print 'in preprocess_patches patches_list,patches_map:',patches_list,patches_map
        for item in patches_list:
            if len(item.strip())<1:
                continue
            if not os.path.exists(item):
                my_dbg_vanzo("Warning %s not exist\n"%(item),LEVEL_WARNING)
                continue
            index=item.find(self.patch_dir_name)
            if index<0:
                my_dbg_vanzo("Error why not find %s from %s\n"%(self.patch_dir_name,item),LEVEL_ERROR)
                return False
            src_dir=os.path.dirname(os.path.abspath(item[index+len(self.patch_dir_name)+1:]))
            item=os.path.abspath(item)
            if src_dir in patches_map:
                patch_list=patches_map[src_dir]
                for each_patch in patch_list[:]:
                    if os.path.basename(each_patch) == os.path.basename(item):
                        patch_list.remove(each_patch)
                patch_list.append(item)
                patches_map[src_dir]=patch_list
            else:
                patches_map[src_dir]=[item]

        #print 'patches_map:',patches_map
        return True

    def preprocess_overrides(self,overrides_list,overrides_map={}):
        #print 'before:overrides_list:',overrides_list
        #print 'before:overrides_map:',overrides_map
        for item in overrides_list:
            if len(item.strip())<1:
                continue
            if not os.path.exists(item):
                my_dbg_vanzo("Warning %s not exist\n"%(item),LEVEL_WARNING)
                continue
            index=item.rfind(self.overrides_dir_name)
            if index<0:
                my_dbg_vanzo("Error why not find %s from %s\n"%(self.overrides_dir_name,item),LEVEL_ERROR)
                return -1,"override %s error"%(item)
            src_path=os.path.abspath(item[index+len(self.overrides_dir_name)+1:])
            index=src_path.rfind(".override")
            if index<0:
                my_dbg_vanzo("Error %s format error,must ended with .override\n"%(src_path),LEVEL_ERROR)
                return -1,"override %s error"%(item)
            src_path=src_path[0:index]
            item=os.path.abspath(item)
            if src_path in overrides_map:
                my_dbg_vanzo("Warning!%s has more than one override\n"%(src_path),LEVEL_ERROR)
            overrides_map[src_path]=item
        #print 'after overrides_map:',overrides_map
        return True

    def get_po_config_files(self,config_map,patches_map={},overrides_map={}):
      patches_list = []
      overrides_list=[]
      po_cfg = Poes(self.config_root + '/public-binary/po.xml')
      project_name = config_map['VANZO_INNER_PROJECT_NAME']
      local_poes= os.path.join(self.config_root,  '%s/po.xml' % (project_name))
      if os.path.exists(local_poes):
        po_cfg.overlay(local_poes)

      if 'VANZO_PO_CONFIG' not in config_map or len(config_map['VANZO_PO_CONFIG'].strip())<1:
        return True

      poes = config_map['VANZO_PO_CONFIG']
      po_list=self.get_real_po_list(poes)
      #print 'po_list:',po_list
      for p in po_list:
        name = p
        if len(name)<1:
            continue
        for (ss, label) in po_cfg.get_po_file_list(name):
          s = os.path.join(self.config_root + '/' + project_name + '/po', ss)

          ###force copy to specific partion

          if not os.path.exists(s):
            #print '*** file %s is not exists in project folder, try public-binary folder ***\n' % (s)
            s = os.path.join(self.config_root + '/public-binary/po', ss)
            if not os.path.exists(s):
              print '*** file %s is not exists in public-binary folder ***\n' % (s)
              continue
          if s.find('.override.')>=0:
            overrides_list.append(s)
          elif s.find('.patch')>=0:
            patches_list.append(s)
          elif os.path.isdir(s):
            p,o=self.get_po_list_from_dir(s); 
            patches_list.extend(p)
            overrides_list.extend(o)
          else:
            my_dbg_vanzo("Sorry I can not guess the type(patch/override):%s"%(s),LEVEL_ERROR);
            return False

        #print 'patches_list:',patches_list
        #print 'overrides_list:',overrides_list
      if len(patches_list)>0:
        res=self.preprocess_patches(patches_list,patches_map);
        if res != True:
            return res
        
      if len(overrides_list)>0:
        res=self.preprocess_overrides(overrides_list,overrides_map); 
        if res != True:
            return res


      return True


    def process_patch_override(self,prop_name,config_map):
        project_name=None
        if "VANZO_INNER_PROJECT_NAME" in config_map:
            project_name=config_map["VANZO_INNER_PROJECT_NAME"]
        else:
            return -1,"VANZO_INNER_PROJECT_NAME must in config_map"

        config_name=None
        if "VANZO_INNER_CURRENT_CONFIG_NAME" in config_map:
            config_name=config_map["VANZO_INNER_CURRENT_CONFIG_NAME"]
        else:
            return -1,"VANZO_INNER_CURRENT_CONFIG_NAME must in config_map"
        '''
        config_po=os.path.join(self.config_root,project_name,config_name,self.po_name)
        project_po=os.path.join(self.config_root,project_name,self.po_name)
        if os.path.exists(config_po):
            return self.do_patch_override(config_po,config_map)
        elif os.path.exists(project_po):
            return self.do_patch_override(project_po,config_map)
        else:
            return 0,None
        '''
        if 'inherit' not in config_map:
            return -1,'why inherit key not in config_map'
        inherit_list=config_map['inherit'].split()
        inherit_list.reverse()
        #print 'inherit_list:',inherit_list
        for item in inherit_list:
            if item.find('-')<0:
                break
            config_po=os.path.join(self.config_root,project_name,item,self.po_name)
            if os.path.exists(config_po):
                return self.do_patch_override(config_po,config_map)
        project_po=os.path.join(self.config_root,project_name,self.po_name)
        if os.path.exists(project_po):
            return self.do_patch_override(project_po,config_map)
        else:
            return self.begin_patch_and_overrides(config_map)
        return 0,None

    def record_modify_files(self,stdoutdata):
        temp_list=stdoutdata.split("\n")
        for each_line in temp_list:
            index=each_line.find("patching file")
            if index<0:
                continue
            modifing_file=each_line[index+len("patching file"):].strip()
            if not os.path.exists(modifing_file):
                continue
            basename=os.path.basename(modifing_file)
            dst_file=os.path.join(os.path.dirname(modifing_file),"."+basename+self.patch_bak_suffix)
            cmd="cp -a %s %s"%(modifing_file,dst_file)
            res =  os.system(cmd)
            if res != 0:
                return -1,"bak file error"
        return 0,None

    def record_patch(self):
        cmd="touch %s"%(self.patched_label)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("create patch label:%s error\n"%(os.getcwd()),LEVEL_ERROR)
            return -1,"create file error"

        return 0,None

    def patched(self):
        if os.path.exists(self.patched_label):
            return True
        return False

    def record_overlay(self):
        cmd="touch %s"%(self.overlayed_label)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("create overlay label:%s error\n"%(os.getcwd()),LEVEL_ERROR)
            return -1,"create file error"

        return 0,None

    def overlayed(self):
        if os.path.exists(self.overlayed_label):
            return True
        return False

    def diff_patch_map(self,before_map,after_map):
        for key,value in before_map.items():
            if key not in after_map:
                print '%s lost'%(key)
                continue
            value_after=after_map[key] 
            for item in value:
                if item not in value_after:
                    print 'patch %s lost'%(item)
                    continue
                value_after.remove(item) 
            print 'added patches key:%s value:%s'%(key,value_after)
            after_map.pop(key)
        print 'added patches:'
        for key,value in after_map.items():
            print key,value

    def diff_overrides_map(self,before_map,after_map):
        for key,value in before_map.items():
            if key not in after_map:
                print '%s lost'%(key)
                continue
            value_after=after_map[key]
            if value_after != value:
                print 'modified override key:%s from %s to value:%s'%(key,value,value_after)
            after_map.pop(key)
        print 'added overrides:'
        for key,value in after_map.items():
            print key,value
            
        
    def begin_patch_and_overrides(self,config_map,patches_map={},overrides_map={}):
        #my_dbg_vanzo("here to patch_files:%d\n"%(len(patches_map)),LEVEL_DBG);
        #test_map=copy.deepcopy(patches_map)
        #test_map=copy.deepcopy(overrides_map)
        self.get_po_config_files(config_map,patches_map,overrides_map)
        #self.diff_patch_map(test_map,patches_map)
        #self.diff_overrides_map(test_map,overrides_map)
        #sys.exit()
        self.current_patches=patches_map
        if self.only_show:
            if len(patches_map)>0:
                my_dbg_vanzo('patches:',LEVEL_HINT)
            for key,value in patches_map.items():
                print '%s:'%(key)
                for patch in value:
                    my_dbg_vanzo('\t%s'%(patch),LEVEL_HINT)
        elif len(patches_map)>0:
            res,error_info=self.patch_files(patches_map)
            if res < 0:
                return res,error_info
        #my_dbg_vanzo("here to override_files:%d\n"%(len(overrides_map)),LEVEL_DBG);
        self.current_overrides=overrides_map
        if self.only_show:
            if len(overrides_map)>0:
                my_dbg_vanzo('\noverrides:',LEVEL_IMPORTANT)
            for key,value in overrides_map.items():
                print '%s:'%(key)
                my_dbg_vanzo('\t%s'%(value),LEVEL_IMPORTANT)
        elif len(overrides_map)>0:
            return self.override_files(overrides_map)

        return True,None
    def do_patch_override(self,po_path,config_map):
        #here we do no think it has a lot of patches,so we do it simply
        #my_dbg_vanzo("here do_patch_override\n",LEVEL_DBG);
        #print "po_path:",po_path
        patch_name="patches"
        patch_path=os.path.join(po_path,patch_name)
        patches_map={}
        if os.path.exists(patch_path):
            cmd="find %s -type f -name '*.patch' "%(patch_path)
            returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
            if returncode != 0:
                return -1,"find %s error"%(patch_path)
            patches=stdoutdata.strip().split("\n")
            cmd="find %s -type l -name '*.patch' "%(patch_path)
            returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
            if returncode != 0:
                return -1,"find %s error"%(patch_path)
            patches.extend(stdoutdata.strip().split("\n"))
            if not self.only_show:
                print "patches:\n",patches
            for item in patches:
                if len(item.strip())<1:
                    continue
                if not os.path.exists(item):
                    my_dbg_vanzo("Warning %s not exist\n"%(item),LEVEL_WARNING)
                    continue
                index=item.find(patch_path)
                if index<0:
                    my_dbg_vanzo("Error why not find %s from %s\n"%(patch_path,item),LEVEL_ERROR)
                    return -1,"patch %s error"%(item)
                src_dir=os.path.dirname(os.path.abspath(item[len(patch_path)+1:]))
                item=os.path.abspath(item)
                if src_dir in patches_map:
                    if not self.only_show:
                        my_dbg_vanzo("Warning!%s has more than one patch\n"%(src_dir),LEVEL_WARNING)
                    patch_list=patches_map[src_dir]
                    patch_list.append(item)
                    patches_map[src_dir]=patch_list
                else:
                    patches_map[src_dir]=[item]

        override_name="overrides"
        override_path=os.path.join(po_path,override_name)
        overrides_map={}
        if os.path.exists(override_path):
            cmd="find %s -name '*.override.*' "%(override_path)
            returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
            if returncode != 0:
                #my_dbg_vanzo("find %s error,cmd:%s"%(override_path,cmd),LEVEL_ERROR)
                #return False,"find %s error"%(override_path)
                overrides=""
            else:
                overrides=stdoutdata.strip().split("\n")
            #print "overrides:",overrides
            for item in overrides:
                if len(item.strip())<1:
                    continue
                if not os.path.exists(item):
                    my_dbg_vanzo("Warning %s not exist\n"%(item),LEVEL_WARNING)
                    continue
                index=item.find(override_path)
                if index<0:
                    my_dbg_vanzo("Error why not find %s from %s\n"%(override_path,item),LEVEL_ERROR)
                    return -1,"override %s error"%(item)
                src_path=os.path.abspath(item[len(override_path)+1:])
                index=src_path.rfind(".override")
                if index<0:
                    my_dbg_vanzo("Error %s format error,must ended with .override\n"%(src_path),LEVEL_ERROR)
                    return -1,"override %s error"%(item)
                src_path=src_path[0:index]
                item=os.path.abspath(item)
                if src_path in overrides_map:
                    my_dbg_vanzo("Error!%s has more than one override\n"%(src_path),LEVEL_ERROR)
                    return -1,"override %s and %s error\n"%(item,patches_map[src_path])
                else:
                    overrides_map[src_path]=item

        '''
        #my_dbg_vanzo("here to patch_files:%d\n"%(len(patches_map)),LEVEL_DBG);
        self.current_patches=patches_map
        if self.only_show:
            if len(patches_map)>0:
                my_dbg_vanzo('patches:',LEVEL_HINT)
            for key,value in patches_map.items():
                print '%s:'%(key)
                for patch in value:
                    my_dbg_vanzo('\t%s'%(patch),LEVEL_HINT)
        elif len(patches_map)>0:
            res,error_info=self.patch_files(patches_map)
            if res < 0:
                return res,error_info
        #my_dbg_vanzo("here to override_files:%d\n"%(len(overrides_map)),LEVEL_DBG);
        self.current_overrides=overrides_map
        if self.only_show:
            if len(overrides_map)>0:
                my_dbg_vanzo('\noverrides:',LEVEL_IMPORTANT)
            for key,value in overrides_map.items():
                print '%s:'%(key)
                my_dbg_vanzo('\t%s'%(value),LEVEL_IMPORTANT)
        elif len(overrides_map)>0:
            return self.override_files(overrides_map)
        '''

        return self.begin_patch_and_overrides(config_map,patches_map,overrides_map)

    def patch_files(self,patches_map):
        cwd=os.getcwd()
        for dir_name,patch_list in patches_map.items():
            os.chdir(dir_name)
            if self.patched():
                my_dbg_vanzo("warning!%s already patched,so ignore!"%(dir_name),LEVEL_WARNING)
                os.chdir(cwd)
                continue
            for patch in patch_list:
                cmd="patch -p1 --dry-run < %s"%(patch)
                returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
                if returncode != 0:
                    my_dbg_vanzo("Patch %s error,pwd:%s,cmd:%s\n"%(patch,os.getcwd(),cmd),LEVEL_ERROR)
                    os.chdir(cwd)
                    reponsible = Responsible()
                    author = reponsible.main_do(patch)
                    #return -1,"Patch %s error"%(patch)
                    sys.exit(-1)
                cmd="patch -p1 < %s"%(patch)
                returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
                cmd="find |grep xml.orig |xargs rm -rf"
                returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
                #print returncode,stdoutdata,stderrdata
            self.record_patch()
            os.chdir(cwd)

        return 0,None

    def override_files(self,overrides_map):
        if self.overlayed():
            my_dbg_vanzo("warning!already overlayed,so ignore!",LEVEL_WARNING)
            return True,None
        for src_name,override_name in overrides_map.items():
            if os.path.isfile(override_name):
                os.system("rm -f " + src_name)
                os.system("mkdir -p " + os.path.dirname(src_name))
                os.system("cp -f " + override_name + " " + src_name)
            elif os.path.isdir(override_name):
                os.system("mkdir -p " + src_name)
                os.system("cp -afL " + override_name + "/* " + src_name)
        self.record_overlay()
        return True,None
