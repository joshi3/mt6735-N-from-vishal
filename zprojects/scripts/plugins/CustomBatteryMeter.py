import glob
import os
import commands
from BasePlugin import BasePlugin
class CustomBatteryMeter(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_CUSTOM_BATTERYCAP_BY_NAME_VALUE":None}
    def process(self,config_map):
        if "VANZO_INNER_PROJECT_NAME" not in config_map:
            return -1,"VANZO_INNER_PROJECT_NAME must be exist"
        battery_cap = int(config_map["VANZO_CUSTOM_BATTERYCAP_BY_NAME_VALUE"])
        if config_map["HIGH_BATTERY_VOLTAGE_SUPPORT"] == "yes":
            is_batthv = True
        else:
            is_batthv = False

        platform_name = config_map["MTK_PLATFORM"].lower()
        board_name =  config_map["VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE"]

# Vanzo:yuntaohe on: Mon, 11 Jan 2016 10:09:18 +0800
#        if platform_name == "mt6735" :
#            project_name = config_map["VANZO_INNER_PM_PROJECT_NAME"].lower().split('_')
#            if "mt6735m" in project_name :
#                src_dir = "./zprojects/{0}/battery_mt6735m".format(platform_name)
#            else:
#                src_dir = "./zprojects/{0}/battery".format(platform_name)
#        else:
# End of Vanzo:yuntaohe
        src_dir = "./zprojects/{0}/battery".format(platform_name)

# Vanzo:yuntaohe on: Mon, 11 Jan 2016 10:10:24 +0800
#        dst_dirs = glob.glob("kernel-*/arch/arm/mach-{0}/{1}/power/".format(platform_name, board_name))
#        dst_name = "cust_battery_meter"
#        if len(dst_dirs) > 0:
#            dst_dir = dst_dirs[0]
#        else:
#            dst_dirs = glob.glob("kernel-*/drivers/misc/mediatek/mach/{0}/{1}/power/".format(platform_name, board_name))
#            #assert len(dst_dirs) > 0
#            if len(dst_dirs) > 0:
#                dst_dir = dst_dirs[0]
#            else:
# End of Vanzo:yuntaohe
        dst_dirs = glob.glob("kernel-*/drivers/misc/mediatek/include/mt-plat/{0}/include/mach/".format(platform_name))
        assert len(dst_dirs) > 0
        dst_dir = dst_dirs[0]
        dst_name = "mt_battery_meter"


# Vanzo:yuntaohe on: Mon, 11 Jan 2016 10:11:39 +0800
#        if "cust_battery_meter" in commands.getstatusoutput("cd {0};git status | grep cust_battery_meter".format(dst_dir))[1]:
#            return 0, None
# End of Vanzo:yuntaohe

        if "mt_battery_meter" in commands.getstatusoutput("cd {0};git status | grep mt_battery_meter".format(dst_dir))[1]:
            return 0, None

        for file_name in ( "{0}.h".format(dst_name), "{0}_table.h".format(dst_name)):
            if is_batthv:
                list_battery_overlay = glob.glob("{0}/{1}.*mah.hv".format(src_dir, file_name))
            else:
                list_battery_overlay = glob.glob("{0}/{1}.*mah".format(src_dir, file_name))
            list_battery_overlay.sort()
            min_delta = 10000
            min_file = None
            for src_file in list_battery_overlay:
                print src_file
                current_battery_cap = int(src_file.split(".")[3].replace("mah", ""))
                current_delta = abs(current_battery_cap - battery_cap)
                if current_delta < min_delta:
                    min_delta = current_delta
                    min_file = src_file

            if min_delta == 10000:
                assert False, "Battery meter table not found for {0}.".format(battery_cap)

            """
            if min_delta >= 200:
                assert False, "Battery meter table too coarse! Need fixup."
            """

            print "modify battery capacity using file {0}".format(min_file)
            os.system("cp -f {0} {1}/{2}".format(min_file, dst_dir, file_name))

        return 1,None
