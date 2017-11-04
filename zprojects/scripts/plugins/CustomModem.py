import glob
import os
import commands
from bridge import *
from BasePlugin import BasePlugin

class CustomModem(BasePlugin):

    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_INNER_CUSTOM_MODEM":None}
        self.patched_label="modems_patched_label_remove_me_if_need_repatch"

    def record_patch(self):
        cmd="touch %s"%(self.patched_label)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            return -1,"create file error"

    def patched(self):
        if os.path.exists(self.patched_label):
            return True
        return False

    def process(self, config_map):
        if "VANZO_INNER_CUSTOM_MODEM" not in config_map:
            return -1,"VANZO_INNER_CUSTOM_MODEM must be exist"
        modem_patch_name = config_map["VANZO_INNER_CUSTOM_MODEM"]

        #Use modem patch link, nothing to be done here
        if modem_patch_name=="none":
            my_dbg_vanzo("warning! modem patch link is very inefficient and fallibility, you should use VANZO_INNER_CUSTOM_MODEM instead!!!")
            return 0,None

        platform_name = config_map["MTK_PLATFORM"].lower()
        patch_path = "../zprojects/{0}/modem_patch/{1}".format(platform_name, modem_patch_name)
        modem_dirs = "modems/"

        cwd=os.getcwd()
        os.chdir(modem_dirs)

        #if patch already applied, nothing need to do
        if self.patched():
            my_dbg_vanzo("warning!%s already patched!", LEVEL_WARNING)
            #commands.getstatusoutput("git checkout .; git clean -fd")
            os.chdir(cwd)
            return 0,None

        #Check the validity of modem patch
        if not os.path.exists(patch_path):
            assert False, "modem patch not existed, patch name:{0}, invalid modem config, VANZO_INNER_CUSTOM_MODEM={1}".format(patch_path, modem_patch_name)

        cmd="patch -p1 --dry-run < %s"%(patch_path)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("Patch error -------> pwd:%s,cmd:%s\n"%(os.getcwd(),cmd),LEVEL_ERROR)
            os.chdir(cwd)
            sys.exit(-1)

        cmd="patch -p1 < %s"%(patch_path)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)

        self.record_patch()
        os.chdir(cwd)

        return 1,None

