#!/usr/bin/env python

import os
from sh import git
import sys
from pyutils import fs
from os.path import exists, join,expanduser
import glob

class Responsible():

    def get_current_path(self):
        return os.getcwd()

    def find_author(self, patch):
        with fs.chdir('zprojects'):
            git('clean', '-fd')
            git('fetch', '--all')
            if os.path.exists("msg.log"):
                my_sys("rm -f msg.log")
        
            cmds0 = "git log -1"
            cmds1 = ">> msg.log "
            cmds = cmds0 + " " + patch + " " + cmds1
            os.system(cmds)
    
            log_file = open(expanduser("{}/msg.log".format(os.getcwd())))
            print "======================================================================="
            while True:
                lines = log_file.readline()
                if lines:
                    print lines.strip()
                else:
                    break
            log_file.close()

    def main_do(self,patch):
        self.get_current_path()
        self.find_author(patch)
        if glob.glob("zprojects/msg.log"):
            os.system("rm -f zprojects/msg.log")
        else:
            pass
