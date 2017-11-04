#!/usr/bin/env python
#encoding=utf-8
#author:wangfei
import commands
import sys
import os
import stat
import shutil
import subprocess
import tempfile
import sys
import types
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element as Element
from xml.etree.ElementTree import dump as XmlDump
#from bridge import npn_vanzo, get_project_info_vanzo,my_sys_vanzo,my_dbg_vanzo
from bridge import *

class AndroidWorker():
    def __init__(self,project_name="",force=True):
        self.current_project=project_name
        #means custom tool
        self.force=force
        self.ignore_list=[]
        item=os.path.join(os.getcwd(),"out")
        self.ignore_list.append(item)
        item=os.path.join(os.getcwd(),"prebuilts")
        self.ignore_list.append(item)
        item=os.path.join(os.getcwd(),"docs")
        self.ignore_list.append(item)
        item=os.path.join(os.getcwd(),"sdk")
        self.ignore_list.append(item)
    def unique(self,L):
        #return [x for x in L if x not in locals()['_[1]']]
        res=[]
        [res.append(x) for x in L if x not in res]
        return res
    def cmp_time(self,x,y):
        #for newest patch last apply
        if not x:
            return -1
        if not y:
            return 1
        x_file=x[1]
        y_file=y[1]
        cwd=os.getcwd()
        os.chdir(self.VANZO_PREFIX) 
        cmd="git log --pretty=format:'%aN %at' "
        cmd_x=cmd+" "+x_file
        result_x = commands.getstatusoutput(cmd_x)[1].split()
        cmd_y=cmd+" "+y_file
        result_y = commands.getstatusoutput(cmd_y)[1].split()
        file_stat_x=os.stat(x_file)
        file_stat_y=os.stat(y_file)
        if not result_x or len(result_x)<2:
            result_x=[]
            result_x.append(file_stat_x[stat.ST_MTIME])
            result_x.append(file_stat_x[stat.ST_MTIME])
        else:
            cmd="git status -s "
            cmd_x=cmd+" "+x_file
            modified = commands.getstatusoutput(cmd_x)[1]
            if modified:
                result_x=[]
                result_x.append(file_stat_x[stat.ST_MTIME])
                result_x.append(file_stat_x[stat.ST_MTIME])
            
        if not result_y or len(result_y)<2:
            result_y=[]
            result_y.append(file_stat_y[stat.ST_MTIME])
            result_y.append(file_stat_y[stat.ST_MTIME])
        else:
            cmd="git status -s "
            cmd_y=cmd+" "+y_file
            modified = commands.getstatusoutput(cmd_y)[1]
            if modified:
                result_y=[]
                result_y.append(file_stat_y[stat.ST_MTIME])
                result_y.append(file_stat_y[stat.ST_MTIME])
        #print "cmd_x %s,cmd_y %s"%(cmd_x,cmd_y)
        res = int(result_x[1]) - int(result_y[1])
        os.chdir(cwd)
        return res
    def cmp_digit(self,x,y):
        x_index=x.rfind("$")
        y_index=y.rfind("$")
        if x_index < 0 or y_index < 0:
            return cmp(x,y)
        else:
            x_clean=x[0:x_index]
            y_clean=y[0:y_index]
            res=cmp(x_clean,y_clean)
            if res != 0:
                return res
            else:
                x_digit=x[x_index+1:]
                y_digit=y[y_index+1:]
                res=int(x_digit) - int(y_digit) 
                if res > 0:
                    return 1
                elif res < 0:
                    return -1
                else:
                    return 0

    def set_project(self,project_name):
        self.current_project=project_name
    def get_project(self):
        return self.current_project 
    def get_cpu_cores(self):
        with open("/proc/cpuinfo") as in_file:
            total_cores=0
            lines = in_file.readlines()
            for item in lines:
                index=item.strip().find("cpu cores")
                if index>=0:
                    seg=item[index:].strip()
                    number_index=seg.find(":") 
                    if number_index >=0:
                        number=seg[number_index+1:].strip()
                        total_cores+=(int)(number)
                
        return  total_cores
    def clean_hard(self,dirname):
        if not os.path.exists(dirname):
            return False
        cwd=os.getcwd()
        os.chdir(dirname)
        cmd="git clean -fdxq&&git reset --hard"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        os.chdir(cwd)
        if returncode == 0:
            return True
        return False
    def hard_reset_all(self):
        cmd="repo forall -c 'git clean -fdxq&&git reset --hard'"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        #print returncode,stdoutdata,stderrdata
        if returncode == 0:
            return True
        return False

    def clean_one_project(self,quiet,dirname,filename):
        for item in self.ignore_list:
            if os.path.abspath(dirname) == item:
                #print "ignore %s"%(item)
                del filename[:]
                return
        git_symbol=os.path.join(dirname,".git")
        if not os.path.exists(git_symbol):
            return 
        cwd=os.getcwd()
        if quiet == False:
            my_dbg_vanzo("Project:%s"%(dirname),LEVEL_IMPORTANT)
        os.chdir(dirname)
        #print "in clean_one_project cwd:%s,dirname %s"%(cwd,dirname)
        cmd="git clean -fdxq;git checkout -f ."
        my_sys_vanzo(cmd)
        #print "after cmd"
        #results = commands.getstatusoutput(cmd)[1]
        #if quiet == False:
        #    my_dbg_vanzo(results,LEVEL_HINT)
        os.chdir(cwd)
        #fixme for vanzo special process,and for the efficiency,should I move to vanzo_worker?
        #print "filename:",filename
        if not "packages" in filename:
            del filename[:]
            return
        else:
            if dirname == "mediatek":
                del filename[:]
                filename.append("packages")
                return
        
    def clean_dir(self,dir_name=None,quiet=False):
        if dir_name == None:
            dir_name=os.getcwd()
        else:
            dir_name=dir_name.strip()
            if len(dir_name) < 1:
                dir_name=os.getcwd()
        #print "in clean_dir dir_name is %s"%(dir_name)
        os.path.walk(dir_name,self.clean_one_project,quiet)
    def clean(self):
        #cmd="repo forall -c 'git clean -fdx;git checkout .'"
        #my_sys_vanzo(cmd)
        self.clean_dir(None,True)
    def sync_to(self,local_only=False,quiet=False):
        cores=self.get_cpu_cores()
        cmd="repo sync -j%d -f -d"%(cores)
        if local_only:
            cmd+=" -l"
        if quiet:
            cmd+=" -q"
        #my_sys_vanzo(cmd)
        #print "sync_to cmd:%s"%(cmd)
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        #print "sync to:"
        #print returncode,stdoutdata,stderrdata
        if returncode != 0:
            return False
        return True

    def switch_to(self,manifest_name,local_only=False,quiet=False):
        dst_name=manifest_name.lower().strip()
        if dst_name[-4:] == ".xml":
            dst_name=dst_name[:-4]
        #dst_project_info = get_project_info_vanzo(dst_name)
        result=self.npn_to_long_project(dst_name)
        if  result != None:
            dst_name = result
            
        dst_manifest="manifests/%s.xml"%(dst_name)
        #print "dst_manifest %s"%(dst_manifest)
        if not os.path.exists(".repo/"+dst_manifest):
            my_dbg_vanzo("Error,.repo/manifests/%s.xml not exist"%(manifest_name),LEVEL_ERROR)
            return False
        default_manifest=".repo/manifest.xml"
        cmd="ln -sf %s %s"%(dst_manifest,default_manifest)
        my_sys_vanzo(cmd)
        self.clean_dir(None,quiet)
        return self.sync_to(local_only,quiet)

        
    def copy_one_file(self,src_file,dst_file):
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
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        #print "resutls:",returncode,stderrdata,stderrdata
        return returncode
    def copy_and_merge(self,src_root,dst_root,force=False):
        #print "enter copy_and_merge cwd:%s,src_root:%s,dst_root %s"%(os.getcwd(),src_root,dst_root)
        for current_src_root,dirs,files in os.walk(src_root,False,None,True):
            index=current_src_root.find(src_root)
            relative_index=index+len(src_root)
            relative_path=current_src_root[relative_index:]
            #print "current_src_root %s,src_root %s,index %d,relative_index %d,relative_path %s,dst_root %s"%(current_src_root,src_root,index,relative_index,relative_path,dst_root)
            if len(relative_path) < 1:
                continue
            elif relative_path[0]=="/":
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
               # print "src_path:%s,dst_path %s"%(src_path,dst_path)
                if force == True:
                    self.copy_one_file(src_path,dst_path)
                elif os.path.exists(dst_path):
                    file_stat_x=os.stat(src_path)
                    file_stat_y=os.stat(dst_path)
                    src_m=file_stat_x[stat.ST_MTIME]
                    dst_m=file_stat_y[stat.ST_MTIME]
                    src_size=os.path.getsize(src_path)
                    dst_size=os.path.getsize(dst_path)
                    if src_m == dst_m and src_size == dst_size:
                        continue
                    self.copy_one_file(src_path,dst_path)
                else:
                    self.copy_one_file(src_path,dst_path)
        
    def copy_file_list(self,src_list,dst_list,force):
            if len(src_list) != len(dst_list):
                my_dbg_vanzo("Warning!the length of src_list is not equal to dst_list!",LEVEL_WARNING)
            count=len(src_list)
            for i in xrange(0,count):
                if force == False:
                    if os.path.exists(dst_list[i]):
                        my_dbg_vanzo("Warning!the file %s already exist,so ignore"%(dst_list[i]),LEVEL_WARNING)
                        continue;
                #my_dbg_vanzo("here to copy %s to %s"%(src_list[i],dst_list[i]),LEVEL_DBG)
                src=src_list[i].strip()
                dst=dst_list[i].strip()
                #cmd="cp -a %s %s"%(src_list[i],dst_list[i])
                dirname=os.path.dirname(dst)
                mkdir_p_vanzo(dirname)
                cmd="cp -a %s %s"%(src,dst)
                self.RunCommand(cmd)
                returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
                #print returncode,stdoutdata,stderrdata

    def create_manifest(self,project_name):
        dst_project_info = get_project_info_vanzo(project_name)
        #print "project_name:%s,dst_project_info %s"%(project_name,dst_project_info)
        #trunk_manifest=".repo/manifests/"+dst_project_info["vtrunk"]
        trunk_manifest=dst_project_info["vtrunk"]+".xml"
        dst_manifest=".repo/manifests/%s.xml"%(project_name)
        if os.path.exists(dst_manifest):
            my_dbg_vanzo("Warning!file %s already exist"%(dst_manifest),LEVEL_WARNING)
            return
        cmd="ln -sf %s %s"%(trunk_manifest,dst_manifest)
        my_sys_vanzo(cmd)
        self.modified_project.append(".repo/manifests")
    def is_exist_file(self,file_name):
        if os.path.exists(file_name):
            return True
        else:
            return False
        
    def get_git_project_codes(self,local_dir,remote_path,branch_name):
        if not os.path.exists(local_dir):
            mkdir_p_vanzo(local_dir)
        cwd=os.getcwd()
        #os.chdir(local_dir)
        cmd="git clone -b %s %s %s"%(branch_name,remote_path,local_dir)
        #results = commands.getstatusoutput(cmd)[1].split()
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        #print cmd,returncode,stderrdata,stderrdata
        if returncode != 0:
                my_dbg_vanzo("git clone %s error"%(remote_path),LEVEL_ERROR)
                return False
        #for item in results:
            #if item.find("fatal")>=0:
                #my_dbg_vanzo("git clone %s error"%(remote_path),LEVEL_ERROR)
                #os.chdir(cwd)
                #return False
        #os.chdir(cwd)
        return True
    def is_different_git_project(self,dir_name,src_project,dst_project):
        #print "enter is_different_git_project src_project %s,dst_project %s"%(src_project,dst_project)
        try:
            src_fetch_path,src_remote_path,src_remote_branch,src_default_base=self.get_git_project_info(dir_name,src_project,False)
            dst_fetch_path,dst_remote_path,dst_remote_branch,dst_default_base=self.get_git_project_info(dir_name,dst_project,False)
            if src_fetch_path != dst_fetch_path:
                return True
            if src_remote_path != dst_remote_path:
                return True
            if src_remote_branch != dst_remote_branch:
                return True
            if src_default_base != dst_default_base:
                return True
            return False
        except Exception,e:
            print "Exception:",e
            return True
    def checkout_project_branch(self,local_dir,remote_branch):
        if not os.path.exists(local_dir):
            my_dbg_vanzo("Error %s not exist"%(local_dir),LEVEL_ERROR)
            return False
        cwd=os.getcwd()
        self.clean_one_project(True,local_dir,[])
        os.chdir(local_dir)
        #print "the current dir is :",os.getcwd()
        cmd="git checkout -f %s"%(remote_branch)
        #print "cmd is %s"%(cmd)
        #results = commands.getstatusoutput(cmd)[1]
        #results=subprocess.call(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        #print returncode,stderrdata,stderrdata
        if returncode != 0:
            my_dbg_vanzo("git checkout %s to %s error"%(local_dir,remote_branch),LEVEL_ERROR)
            os.chdir(cwd)
            return False
        os.chdir(cwd)
        return True

    def has_remote_branch(self,dir_name,branch_name):
        cwd=os.getcwd()
        os.chdir(dir_name)
        cmd="git branch -r"
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        if returncode !=0:
            os.chdir(cwd)
            return False
        results=stdoutdata.split("\n")
        #print "results:",results
        branch_name=branch_name.strip()
        for item in results:
            item=item.strip() 
            if item==branch_name:
                os.chdir(cwd)
                return True
        os.chdir(cwd)
        return False
    def checkout_or_clone_dir(self,dir_name,project_name=None,quiet=True):
        #print "project_name is %s"%(project_name)
        try:
            if dir_name[-1] == "/":
                dir_name=dir_name[:-1]
            fetch_path,remote_path,remote_branch,default_base=self.get_git_project_info(dir_name,project_name,False)
            #print "dir_name %s,fetch_path %s,remote_path %s,remote_branch %s,default_base %s"%(dir_name,fetch_path,remote_path,remote_branch,default_base)
            if (remote_branch == None) or (default_base == None):
                return False
            if not os.path.exists(dir_name):
                return self.get_git_project_codes(dir_name,fetch_path+"/"+remote_path,remote_branch)
            else:
                #return self.checkout_project_branch(dir_name,default_base+"/"+remote_branch)
                out_branch=default_base+"/"+remote_branch
                if not self.has_remote_branch(dir_name,out_branch):
                    out_branch="origin/%s"%(remote_branch)
                    if not self.has_remote_branch(dir_name,out_branch):
                        out_branch=remote_branch
                #print "out_branch:",out_branch
                return self.checkout_project_branch(dir_name,out_branch)
        except Exception,e:
            print "Exception:",e
            return False
        

    def get_git_project_info(self,dir_name,project_name=None,quiet=True):
        #print "dir_name %s,cwd %s"%(dir_name,os.getcwd())
        if project_name == None:
            project_name=self.get_current_prj()
        long_project_name=self.npn_to_long_project(project_name)
        #print "long_project_name:",long_project_name
        dst_manifest=".repo/manifests/%s.xml"%(long_project_name)
        if not os.path.exists(dst_manifest):
            if self.force==False:
                if quiet == False:
                    my_dbg_vanzo("Error no manifest %s"%dst_manifest,LEVEL_ERROR)
                return None,None,None,None
            else:
                self.check_out_repo_manifest(project_name)
        dir_name=dir_name.strip()
        handle=ET.parse(dst_manifest)

        fetch_path=""
        remote_path=""
        remote_branch=""
        default_base=""
        remote_info=handle.findall("/remote")
        for item in remote_info:
            fetch_path=item.attrib["fetch"]

        default_settings=handle.findall("/default")
        for item in default_settings:
            #print item.attrib
            default_branch=item.attrib["revision"]
            default_base=item.attrib["remote"]
        project_settings=handle.findall("/project")
        for project in project_settings:
            project_local_path=project.attrib["path"]
            project_remote_path=project.attrib["name"]
            #print "project_local_path %s,dir_name %s"%(project_local_path,dir_name)
            if project_local_path.strip() == dir_name:
                remote_path=project_remote_path
                key="revision" 
                if key in project.attrib:
                    remote_branch=project.attrib[key]
                else:
                    remote_branch=default_branch
            
        #print "fetch_path %s,remote_path %s,remote_branch %s,default_base %s"%(fetch_path,remote_path,remote_branch,default_base)
        return fetch_path,remote_path,remote_branch,default_base


    def set_env(self,project_name):
        if project_name != "":
            set_project(project_name)
    def compile(self,project_name=""):
        self.set_env(project_name)
        cmd="nohup make -j%d &"%(get_cpu_cores())
        my_sys_vanzo(cmd)
    def RunCommand(self,cmd):
        #print "Running: ", cmd
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (stdoutdata, stderrdata) = p.communicate()
        return (p.returncode, stdoutdata, stderrdata)
    def find_file(self,search_file,search_dir=None):
        if search_dir==None:
            search_dir=os.getcwd()
        if not os.path.exists(search_dir):
            return None
        #print "search_file:%s,search_dir:%s"%(search_file,search_dir)
        for root, dirs, files in os.walk(search_dir):
            for item in dirs:
                if item == search_file:
                    return os.path.join(root,item)
            for item in files:
                if item == search_file:
                    return os.path.join(root,item)
        return None
    def insert_lines_before(self,file_name,content,match_line,only_one=True):
        inserted=False
        with open(file_name) as in_file:
            all_lines=in_file.readlines()
            regex=re.compile(match_line)
            write_lines=[]
            count=len(all_lines)
            for i in xrange(0,count):
                if re.match(regex,all_lines[i]):
                    inserted=True
                    write_lines.append(content)
                    write_lines.append("\n")
                    write_lines.append(all_lines[i])
                    if only_one:
                        write_lines.extend(all_lines[i+1:])
                        break
                else:
                    write_lines.append(all_lines[i])
        if inserted==False:
            return False
        _,out_name = tempfile.mkstemp("tmp","tmp",os.getcwd())
        with open(out_name,"w+") as out_handle:
            out_handle.writelines(write_lines)
        os.rename(out_name,file_name) 
        return True
        
    def insert_lines_after(self,file_name,content,match_line,only_one=True):
        #print "match_line is %s"%(match_line)
        with open(file_name) as in_file:
            all_lines=in_file.readlines()
            regex=re.compile(match_line)
            write_lines=[]
            count=len(all_lines)
            for i in xrange(0,count):
                if re.match(regex,all_lines[i]):
                    inserted=True
                    write_lines.append(all_lines[i])
                    write_lines.append(content)
                    write_lines.append("\n")
                    if only_one:
                        write_lines.extend(all_lines[i+1:])
                        break
                else:
                    write_lines.append(all_lines[i])
        if inserted==False:
            return False
        _,out_name = tempfile.mkstemp("tmp","tmp",os.getcwd())
        with open(out_name,"w+") as out_handle:
            out_handle.writelines(write_lines)
        os.rename(out_name,file_name) 
        return True
    def modify_lines(self,file_name,content,match_line,only_one=True):
        #print "file_name:%s,match_line is %s"%(file_name,match_line)
        inserted=False
        with open(file_name) as in_file:
            all_lines=in_file.readlines()
            regex=re.compile(match_line)
            write_lines=[]
            count=len(all_lines)
            for i in xrange(0,count):
                if re.match(regex,all_lines[i]):
                    inserted=True
                    write_lines.append(content)
                    write_lines.append("\n")
                    if only_one:
                        write_lines.extend(all_lines[i+1:])
                        break
                else:
                    write_lines.append(all_lines[i])
        if inserted==False:
            return False
        _,out_name = tempfile.mkstemp("tmp","tmp",os.getcwd())
        with open(out_name,"w+") as out_handle:
            out_handle.writelines(write_lines)
        os.rename(out_name,file_name) 
        return True
    def send_email(to_addrs="wangfei@vanzotec.com", subj="no subject", msg="",attach="",bcc_addrs="",username="",passwd=""):
        total_addrs = []
        for i in to_addrs:
            total_addrs.append(i)
        for i in bcc_addrs:
            total_addrs.append(i)

        print 'All receipients are: %s' % total_addrs

        # Convert lists to strings for msg.
        #s_toaddrs = ",".join(total_addrs)
        #s_bccaddrs = ";".join(bcc_addrs)
        #sys.exit()

        #msgRoot = MIMEMultipart('related')
        msgRoot = MIMEMultipart()
        try:
            att = MIMEText(open(useroptions["attach"], 'rb').read(), 'base64', 'utf-8')  
            att["Content-Type"] = 'application/octet-stream'  
            att["Content-Disposition"] = "attachment; filename=%s"%(useroptions["attach"])
            msgRoot.attach(att)  
        except:
            pass


        try:
            print 'Sending email...'
            SMTPPORT = 25
            SMTPSERVER = 'smtp.exmail.qq.com'
            server = smtplib.SMTP(SMTPSERVER, SMTPPORT)
                
            #server.set_debuglevel(1)
            #server.ehlo()
            #server.starttls()
            print 'Login...'
            smtpuser = 'wangfei@vanzotec.com'
            smtppass = 'Vanzo1'
            FROMADDR = 'wangfei@vanzotec.com'
            if True:
                if username and passwd and username!="" and passwd!="":
                    smtpuser=username
                    smtppass=passwd
                    FROMADDR=smtpuser
                print "smtpuser,smtppass",smtpuser,smtppass
                server.login(smtpuser, smtppass)

            print 'SMTP Server login successed'

            print "FROMADDR %s,total_addrs %s,msg %s"%(FROMADDR,total_addrs,msgRoot.as_string())
            #Contents = MIMEText('<b>This is a img!</b>','html')
            #Contents = MIMEText(msg,'html')
            Contents = MIMEText(msg)
            #Contents = MIMEText(msg)
            msgRoot.attach(Contents)

            msgRoot['Subject'] = subj
            #msgRoot['CC'] = s_bccaddrs
            print "FROMADDR:%s,cont %s"%(FROMADDR,msgRoot.as_string())
            #server.sendmail(FROMADDR, s_toaddrs, msgRoot.as_string())
            print "total_addrs:",total_addrs
            server.sendmail(FROMADDR, total_addrs, msgRoot.as_string())
            #server.sendmail(FROMADDR, s_toaddrs, msgRoot.as_string())
            server.close()
            print 'Email sent!'
        except Exception,e:
            print "ERROR SENDING EMAIL! SMTP ERROR.",e
            sys.exit()
  
    def read_xml(self,in_path):  
        tree = ET.parse(in_path)  
        return tree  
      
    def write_xml(self,tree, out_path):  
        tmp_path=".%s.tmp.working"%(os.path.basename(out_path))
        tree.write(tmp_path, "utf-8")
        #for python 2.6 not write the header,so we must write 
        header="<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
        with open(tmp_path,"rw+") as out_file:
            lines=out_file.readlines()
            lines.insert(0,header)
            #print lines
            out_file.seek(0,0)
            for item in lines:
                out_file.write(item)
        #for this foolish class xmltree,it doesnot format the output,we must do it self
        cmd="xmllint  --format %s >%s"%(tmp_path,out_path)
        returncode, stdoutdata, stderrdata=self.RunCommand(cmd)
        os.remove(tmp_path)
        
        
      
    def if_match(self,node, kv_map,text=None):  
        '''''判断某个节点是否包含所有传入参数属性 
           node: 节点 
           kv_map: 属性及属性值组成的map'''  
        #if map is empty always match
        if (not kv_map or len(kv_map) < 1) and text==None:
            return True
        if kv_map != None:
            for key in kv_map:  
                if node.get(key) != kv_map.get(key):  
                    return False
        #print "node.text:%s,text %s"%(node.text,text)
        if text != None:
            if node.text != text:
                return False
        return True  
      
    def find_nodes(self,tree, path):  
        '''''查找某个路径匹配的所有节点 
           tree: xml树 
           path: 节点路径'''  
        return tree.findall(path)  
      
    def get_node_by_keyvalue_text(self,nodelist, kv_map,text=None):
        '''''根据属性及属性值定位符合的节点，返回节点 
           nodelist: 节点列表 
           kv_map: 匹配属性及属性值map'''
        result_nodes = []
        for node in nodelist:  
            #print "node.tag %s,node.text:%s"%(node.tag,node.text)
            if self.if_match(node, kv_map,text):
                result_nodes.append(node)
        return result_nodes  
      
    def change_node_properties(self,nodelist, kv_map, is_delete=False):  
        '''''修改/增加 /删除 节点的属性及属性值 
           nodelist: 节点列表 
           kv_map:属性及属性值map'''  
        for node in nodelist:  
            for key in kv_map:
                if is_delete:
                    if key in node.attrib:
                        del node.attrib[key]
                else:  
                    node.set(key, kv_map.get(key))
                  
    def change_node_text(self,nodelist, text, is_add=False, is_delete=False):
        '''''改变/增加/删除一个节点的文本 
           nodelist:节点列表 
           text : 更新后的文本'''  
        for node in nodelist:  
            if is_add:  
                node.text += text
            elif is_delete:
                node.text = ""
            else:
                node.text = text
                  
    def create_node(self,tag, property_map, content):
        '''''新造一个节点 
           tag:节点标签 
           property_map:属性及属性值map 
           content: 节点闭合标签里的文本内容 
           return 新节点'''  
        element=None
        if not property_map or len(property_map) < 1:
            element = Element(tag)
        else:
            element = Element(tag, property_map)
        element.text = content
        return element
    def insert_child_node(self,nodelist, element,index):
        '''''给一个节点添加子节点 
           nodelist: 节点列表 
           element: 子节点'''  
        for node in nodelist:  
            node.insert(index,element)
    def insert_child_nodes(self,nodelist, elements,index):
        '''''给一个节点添加子节点 
           nodelist: 节点列表 
           element: 子节点'''  
        for node in nodelist: 
            for element in elements:
                node.insert(index,element)
              
    def add_child_node(self,nodelist, element):
        '''''给一个节点添加子节点 
           nodelist: 节点列表 
           element: 子节点'''  
        for node in nodelist:  
            node.append(element)

    def add_child_nodes(self,nodelist, elements):
        '''''给一个节点添加子节点 
           nodelist: 节点列表 
           element: 子节点'''  
        for node in nodelist:  
            for element in elements:
                node.append(element)
              
    def del_node_by_tagkeyvalue(self,nodelist, tag, kv_map):  
        '''''同过属性及属性值定位一个节点，并删除之 
           nodelist: 父节点列表 
           tag:子节点标签 
           kv_map: 属性及属性值列表'''  
        for parent_node in nodelist:  
            children = parent_node.getchildren()  
            for child in children:  
                if child.tag == tag and self.if_match(child, kv_map):  
                        parent_node.remove(child)  
    def dump_nodes(self,nodes_list):
        for node in nodes_list:
            XmlDump(node)
    def str_to_class(self,field):
        try:
            identifier = getattr(sys.modules[__name__], field)
        except AttributeError:
            #raise NameError("%s doesn't exist." % field)
            return None
        if isinstance(identifier, (types.ClassType, types.TypeType)):
            return identifier
        return None
    def set_force(self,force):
        self.force=force
    def get_pair_from_line(self,line):
        work_line=line.strip()
        index=work_line.find("=")
        if index <= 0:
            return []
        key=work_line[:index].strip()
        value=work_line[index+1:].strip()
        return [key,value]
    def get_config_content(self,config_file):
        if not config_file or not os.path.exists(config_file):
            my_dbg_vanzo("Error:Can not find file %s"%(config_file),LEVEL_ERROR) 
            return []
        config_content=[]
        with open(config_file) as in_file:
            config_content=in_file.readlines() 
        return config_content
    def get_config_map(self,config_file):
        if isinstance(config_file,list):
            lines=config_file
        else:
            lines=self.get_config_content(config_file)
        config_map={}
        for item in lines:
			index=item.find("#")
			if index>=0:
				item=item[:index]
			one_pair=self.get_pair_from_line(item)
			if len(one_pair)!=2:
				continue;
			config_map[one_pair[0]]=one_pair[1]
        return config_map
    def get_user_answer(self,hint=None,raw=False):
        if not hint:
            hint="[Y/N]Y?"
        answer=raw_input(hint)
        if raw:
            return answer
        while answer.lower()!="y" and answer.lower()!="n" and answer.lower()!="":
            my_dbg_vanzo("can only input Y or N!",LEVEL_HINT)
            answer=raw_input(hint)
        if answer.lower() == "":
            answer="Y"
        return answer
    def windows_path_to_linux(self,path):
        if not path:
            return None
        linux_path=path.replace("\\","/")
        return linux_path 
    def linux_path_to_windows(self,path):
        if not path:
            return None
        windows_path=path.replace("/","\\")
        return windows_path
    def dump_node(self,dump_data):
        #print "type:",type(dump_data)
        if isinstance(dump_data,dict):
            for key,value in dump_data.items():
                if isinstance(value,dict):
                    print "%s:"%(key)
                    self.dump_node(value)
                    #for sub_key,sub_value in value.items():
                        #print "%s:%s"%(sub_key,sub_value)
                elif isinstance(value,list) or isinstance(value,tuple):
                    #for item in value:
                        #print item
                    print "%s:"%key
                    self.dump_node(value)
                else:
                    print "%s:%s"%(key,value)
        elif isinstance(dump_data,list) or isinstance(dump_data,tuple):
            for item in dump_data:
                if not isinstance(dump_data,str):
                    self.dump_node(item)
                else:
                    print item
        else:
            print dump_data

if __name__ == '__main__':
    worker=AndroidWorker()
    worker.clean_dir(sys.argv[1])
    sys.exit()

