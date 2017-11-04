#!/usr/bin/env python2.7
import sys
import os
import xml.dom.minidom
import ConfigParser
import zipfile
import tarfile
import re
import getopt
import shutil
import subprocess
import stat
from distutils import dir_util, file_util

USERDATA_TGZ='system/backup/userdata.tar.gz'

class Package(object):
    def __init__(self, name):
      self.name = name
      self.files = []

    def  add_file(self, src, dst,label=None): 
      self.files.append((src, dst,label))
    
class Packages(object):
  def __init__(self, name):
    self.packages = {}
    self.__parse_xml(name)

  def __parse_xml(self, fname):  

    print "in __parse_xml fname:",fname
    if not os.path.exists(fname):
        print "Warning! in __parse_xml %s not exist!"%(fname)
        return

    data = open(fname).read()
    if len(data) == 0:
        print "Warning! in __parse_xml %s empty!"%(fname)
        return
    root = xml.dom.minidom.parse(fname)

    root = root.childNodes[0]

    for node in root.childNodes:
      if node.nodeName == 'package':
        name = node.getAttribute('name')
        if name == '':
          continue
        
        p = Package(name)
        for i in node.childNodes:
          if i.nodeName == 'file':
            src = i.getAttribute('src')
            dst = i.getAttribute('dst')
            label = i.getAttribute('label')
            p.add_file(src, dst,label)

        self.packages[name] = p
  
  def get_package_file_list(self, name):
    if not self.packages.has_key(name):
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
            print 'packages not found %s\n' % (name)
            return []
        if not self.packages.has_key(real_name):
            print 'packages not found: %s\n' % (real_name)
            return []
        all_list=self.packages[real_name].files
        #print "real_name,all_list,choosed",real_name,all_list,choosed
        choosed_list=[]
        for (src,dst,label)in all_list:
            print 'src,dst,label',src,dst,label
            #if label and (label in choosed) and (label not in minused):
            if label and (label in choosed):
                choosed_list.append((src,dst,label))
        if index_dollar>0 and len(choosed_list)<1:
            print 'You config must be error:',name
            sys.exit(-1)
        if len(choosed_list)<1:
            choosed_list = all_list

        choosed_list=[item for item in choosed_list if not item[2] or (item[2] not in minused)]
        
        print "choosed_list:",choosed_list
        return choosed_list
    
    return self.packages[name].files

  def overlay(self, filepath):
    self.__parse_xml(filepath)

class CustomerCfg(object):
  def __init__(self, name):
    print name
    self.customers = {}
    paser = ConfigParser.ConfigParser()
    paser.optionxform=str
    paser.read(name)

    customer = {}
    for sec in paser.sections():
      customer = dict(paser.items(sec))
      print "customer:",customer
      self.customers[sec]=customer

  def get_custom_config(self, id=None):
    if id != None:
        if self.customers.has_key(id):
          return self.customers[id]
        else:
          return None
    else:
        #only has one value
        if len(self.customers)!=1:
            print "Error,self.customers %d"%(len(self.customers))
            return None
        for key,value in self.customers.items():
            return value

def RunCommand(cmd):
    #print "Running: ", cmd
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (stdoutdata, stderrdata) = p.communicate()
    return (p.returncode, stdoutdata, stderrdata)

def mkdir_p_vanzo(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if error.errno != errno.EEXIST or not os.path.isdir(path):
            raise
def copy_one_file(src_file,dst_file):
    if not os.path.exists(src_file):
        return -1
    dir_name=""
    if os.path.isdir(dst_file):
        dir_name=dst_file
    else:
        dir_name=os.path.dirname(dst_file)
    if not os.path.exists(dir_name):
        mkdir_p_vanzo(dir_name)
    cmd="cp -a %s %s"%(src_file,dst_file)
    returncode, stdoutdata, stderrdata=RunCommand(cmd)
    #print "resutls:",returncode,stderrdata,stderrdata
    return returncode
def copy_and_merge(src_root,dst_root,arch,force=False):
    #print "enter copy_and_merge cwd:%s,src_root:%s,dst_root %s"%(os.getcwd(),src_root,dst_root)
    filelist=[]
    for current_src_root,dirs,files in os.walk(src_root,False,None,True):
        index=current_src_root.find(src_root)
        relative_index=index+len(src_root)
        relative_path=current_src_root[relative_index:]
        #print "current_src_root %s,src_root %s,index %d,relative_index %d,relative_path %s,dst_root %s"%(current_src_root,src_root,index,relative_index,relative_path,dst_root)
        '''
        if len(relative_path) < 1:
            continue
        elif relative_path[0]=="/":
            relative_path=relative_path[1:]
        '''
        if len(relative_path)>0 and relative_path[0]=="/":
            relative_path=relative_path[1:]
        current_dst_root=os.path.join(dst_root,relative_path)
        for one_dir in dirs:
            dst_path=os.path.join(current_dst_root,one_dir)
            if not os.path.exists(dst_path):
                mkdir_p_vanzo(dst_path)
        #print "files:",files
        for one_file in files:
            src_path=os.path.join(current_src_root,one_file)
            dst_path=os.path.join(current_dst_root,one_file)
            #print "src_path:%s,dst_path %s"%(src_path,dst_path)
            copied_list=copy_apk(src_path,dst_path,arch)
            if force == True:
                if not copied_list or len(copied_list)<1:
                    if copy_one_file(src_path,dst_path)== 0:
                        filelist.append(dst_path) 
            elif os.path.exists(dst_path):
                file_stat_x=os.stat(src_path)
                file_stat_y=os.stat(dst_path)
                src_m=file_stat_x[stat.ST_MTIME]
                dst_m=file_stat_y[stat.ST_MTIME]
                src_size=os.path.getsize(src_path)
                dst_size=os.path.getsize(dst_path)
                if src_m == dst_m and src_size == dst_size:
                    continue
                if not copied_list or len(copied_list)<1:
                    if copy_one_file(src_path,dst_path)==0:
                        filelist.append(dst_path)
            else:
                if not copied_list or len(copied_list)<1:
                    if copy_one_file(src_path,dst_path)==0:
                        filelist.append(dst_path) 
            filelist.extend(copied_list)
    return filelist

def copy_apk(src_file,dst_file,arch):
  if not src_file or not dst_file:
    print "Error file not exist:",src_file,dst_file
    return []
  filelist = []
  s=src_file
  d=dst_file
  if s.endswith('.apk') and os.path.exists(s):
    if d.find('data/app') >= 0 or d.find('pre-install') >= 0:
      print "%s:to data do not need extract"%(d)
      if copy_one_file(src_file,dst_file) == 0:
        filelist.append(dst_file)
      return filelist
    try:
      zip = zipfile.ZipFile(s)
      znamelist = zip.namelist()
      apk_dest=d[:-4]
      if os.path.isdir(apk_dest):
          shutil.rmtree(apk_dest)
      for name in znamelist:
        if name.endswith('.so') and name.find("armeabi") != -1:
          if arch != 'armeabi':
            lib_localArch = re.compile('lib/armeabi/').sub('lib/'+arch+'/', name)
            try :
              znamelist.index(lib_localArch)
              name = lib_localArch
            except ValueError:
              #print 'can not find %s, use the default.' % lib_localArch
              pass

          print 'copy lib:<%s>\n' % name
          ori_arch=os.path.basename(os.path.dirname(name))
          if ori_arch.find('arm64') > 0:
            dst_arch = 'arm64'
          else:
            dst_arch = 'arm'
          data = zip.read(name)
          '''
          #dest = re.compile('system/app/.*$').sub('system/lib/', d)
          dest = re.compile('system/.*$').sub('system/lib/', d)
          #dest = re.compile('/data/').sub('/system/', dest)
          dest = os.path.join(dest, '%s' % (os.path.basename(name)))
          '''
          dest = os.path.join(apk_dest, '%s' % (name))
          dest=dest.replace(ori_arch,dst_arch)
          dirname = os.path.dirname(dest)
          #print "dest and dirname:",dest,dirname,apk_dest
          if not os.path.exists(dirname):
            #os.makedirs(dirname)
            mkdir_p_vanzo(dirname)
          (lambda f, d: (f.write(d), f.close()))(open(dest, 'wb'), data)  
          filelist.append(dest)
      zip.close()
      dst_apk_name=os.path.join(apk_dest,os.path.basename(d))
      if copy_one_file(src_file,dst_apk_name) == 0:
        filelist.append(dst_apk_name)
    except Exception,e:
      print "extract so from %s error:%s!" % (s,e)

  return filelist

def get_real_packages_list(packages):
    work_list=[]
    result_list=[]
    origin_list=packages.split()
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

    return result_list

def copy_file(src, dst, project_name, arch='armeabi'):
  filelist = []
  custom_cfg = CustomerCfg(src + '/' + project_name + '/' + project_name + '.cfg')
  package_cfg = Packages(src + '/public-binary/packages.xml')
  local_packages = os.path.join(src,  '%s/packages.xml' % (project_name))
  if os.path.exists(local_packages):
    package_cfg.overlay(local_packages)

  
  custom = custom_cfg.get_custom_config()
  print custom
  if custom == None:
    return []

  packages = custom['VANZO_RESOURCE_PACKAGES']
  packages_list=get_real_packages_list(packages)
  #for p in packages.split():
  for p in packages_list:
    try:
      (name, partion) = p.split(':')   ###packagename:DATA
    except:
      name = p
      partion = ''

    dpre = None
    for (ss, d,label) in package_cfg.get_package_file_list(name):
      s = os.path.join(src + '/' + project_name + '/binary', ss)

      ###force copy to specific partion
      if partion != '':
        if partion[0] == 'D': partion = 'data'
        elif partion[0] == 'S': partion = 'system'
        elif partion[0] == 'P': partion = 'system/pre-install'

        if partion in ('data', 'system'):
          d = os.path.join(partion, re.compile('(system|data)/(.*)').sub(r'\2', d))
        elif partion == 'system/pre-install':
          d = os.path.join('data', re.compile('(system|data)/(.*)').sub(r'\2', d))
          dpre = os.path.join(partion, os.path.basename(d))

    
      d = os.path.join(dst, d)
      if dpre:
        dpre = os.path.join(dst, dpre)

      if not os.path.exists(s):
        #print '*** file %s is not exists in project folder, try public-binary folder ***\n' % (s)
        s = os.path.join(src + '/public-binary', ss)
        if not os.path.exists(s):
          print '*** file %s is not exists in public-binary folder ***\n' % (s)
          continue

      if dpre:
        dirname = os.path.dirname(dpre)
        if not os.path.exists(dirname):
          os.makedirs(dirname)

      dirname = os.path.dirname(d)
      if not os.path.exists(dirname):
        os.makedirs(dirname)

      copied_list=copy_apk(s,d,arch)
      if os.path.isdir(s):
        '''
        if os.path.exists(d):
          shutil.rmtree(d)
        shutil.copytree(s, d)
        '''
        filelist.extend(copy_and_merge(s,d,arch))
        print 'copy dir %s to %s' % (s, d)
      else:
        if not copied_list or len(copied_list)<1:
            shutil.copyfile(s, d)
            filelist.append(d)
            if dpre:
              shutil.copyfile(s, dpre)
              filelist.append(dpre)
      #if not os.path.isdir(s):
      #  print 'copy file %s to %s' % (s, d)
      filelist.extend(copied_list)

  return filelist

def create_userdata_tgz(filelist, tgz):
  dirname = os.path.dirname(tgz)
  if not os.path.exists(dirname):
    os.makedirs(dirname)

  tar = tarfile.open(tgz, 'w:gz')

  for file in filelist:
    if not os.path.exists(file):
      continue

    relpath = re.compile('(.*?)/(system|data)/(.*)').sub(r'\2/\3', file)
    if relpath.startswith('data'):
      tar.add(file, relpath)

  tar.close()

print "len:%d,pwd:%s"%(len(sys.argv),os.getcwd())
#if len(sys.argv) != 4:
  #print 'usage %s src dst' % (sys.argv[0])

src = os.path.abspath(sys.argv[1])
dst = sys.argv[2]
project_name = sys.argv[3]
prj_armeabi = sys.argv[4]

print "src:%s,dst:%s,project_name:%s,prj_armeabi:%s"%(src,dst,project_name,prj_armeabi)
filelist = copy_file(src, dst, project_name, prj_armeabi)

#tar_tgz = os.path.join(dst, USERDATA_TGZ)
#create_userdata_tgz(filelist, tar_tgz)
