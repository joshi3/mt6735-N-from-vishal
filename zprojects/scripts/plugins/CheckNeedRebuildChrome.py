import glob
import os
import commands
import time
import sys
from bridge import *
from BasePlugin import BasePlugin
class CheckNeedRebuildChrome(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"PRODUCT_PREBUILT_WEBVIEWCHROMIUM":None}
        self.chrome_prebuilt_time = "Thu Nov 12 12:00:00 2015"
        self.chrome_prebuilt_time2 = time.strptime(self.chrome_prebuilt_time)
    def process(self,config_map):
        if "VANZO_INNER_PROJECT_NAME" not in config_map:
            return -1,"VANZO_INNER_PROJECT_NAME must be exist"

        check_dir = "external/chromium_org/android_webview"
        list_output = commands.getstatusoutput("cd {0};git log .".format(check_dir))[1].split("\n")
        for  one_line in list_output:
            if "Not a git repository" in one_line:
                break
            if one_line.startswith("Date:"):
                src_update_time = one_line.replace("Date:", "")[:-6].strip()
                src_update_time2 = time.strptime(src_update_time)

                if (src_update_time2 > self.chrome_prebuilt_time2):
                    my_dbg_vanzo("Error! Need to rebuild chrome, source update time: {0}, chrome prebuild time: {1}\n".format(src_update_time, self.chrome_prebuilt_time))
                    sys.exit(-1)
                break
    
        return 0,None
