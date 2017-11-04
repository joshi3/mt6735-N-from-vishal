#!/usr/bin/env python
import commands
import sys
import os
import shutil
from android_worker import AndroidWorker
#from bridge import npn_vanzo, get_project_info_vanzo,my_sys_vanzo,my_dbg_vanzo
from bridge import *

class MTKWorker(AndroidWorker):
    def __init__(self,project_name="",force=True):
        AndroidWorker.__init__(self,project_name,force)

    def set_env(self,project_name):
        set_project(project_name)
    def compile(self,project_name=""):
        self.set_env(project_name)
        dir="mediatek/custom/%s"%(current_project)
        if os.path.exists(dir):
            cmd="nohup ./makeMtk -t %s n &" %(current_project)
            my_sys_vanzo(cmd)
        else:
            my_dbg_vanzo("Error,no such project %s"%(current_project),LEVEL_ERROR)
            return


