import math
from BasePlugin import BasePlugin
class CustomLcdDesity(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"CUSTOM_KERNEL_LCM":None}

    def process(self,config_map):
        if "VANZO_INNER_PM_PROJECT_NAME" not in config_map:
            return -1,"VANZO_INNER_PM_PROJECT_NAME must be exist"
        lcm_physicalsize_token = config_map["CUSTOM_KERNEL_LCM"].strip().split()[0].split("_")[1]
        #default to 45
        lcm_size=45
        for index, c in enumerate(lcm_physicalsize_token):
            if c.isdigit():
                lcm_size = int(lcm_physicalsize_token[index:].strip())
                break
        while lcm_size < 300:
            lcm_size = lcm_size * 10
        lcm_height = int(config_map["LCM_HEIGHT"])
        lcm_width = int(config_map["LCM_WIDTH"])

        print "CustomLcdDesity, lcm size: %d" % lcm_size
        print "CustomLcdDesity, lcm_height:%d" % lcm_height
        print "CustomLcdDesity, lcm_width:%d" % lcm_width

        standard_aapt = "mdpi"
        pixels = lcm_height * lcm_width
        if pixels <= 240 * 432:
            standard_aapt = "ldpi"
        if pixels >= 480 * 800:
            standard_aapt = "hdpi"
        if pixels >= 640 * 960:
            standard_aapt = "xhdpi"
        if pixels >= 1080 * 1920:
            standard_aapt = "xxhdpi"
        if pixels >= 1440 * 2560:
            standard_aapt = "xxxhdpi"

        list_lcd_density = (120, 160, 240, 320, 480, 640)
        list_standard_aapt = ("ldpi", "mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi")
        standard_lcd_desity= list_lcd_density [list_standard_aapt.index(standard_aapt)]
        print "CustomLcdDesity, standard_lcd_desity:%d" % standard_lcd_desity
        print "CustomLcdDesity, standard_aapt:%s" % standard_aapt

        #if ro.sf.lcd_density was defined in env-xxxx.ini, don't set its value here
        if "ro.sf.lcd_density" not in config_map["VANZO_INNER_CUSTOM_OVERRIDE_PROP"]:
            config_map["VANZO_INNER_CUSTOM_OVERRIDE_PROP"] += " ro.sf.lcd_density=%d" % standard_lcd_desity
        else:
            print "ro.sf.lcd_density was defined already!"

        if "xxxhdpi" == standard_aapt:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG=xxxhdpi xxhdpi xhdpi hdpi"
        elif "xxhdpi" == standard_aapt:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG=xxhdpi xhdpi hdpi"
        elif "xhdpi" == standard_aapt:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG=xhdpi hdpi"
        else:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG={0}".format(standard_aapt)

        return 1, [config_string,]

    """
    def process(self,config_map):
        if "VANZO_INNER_PM_PROJECT_NAME" not in config_map:
            return -1,"VANZO_INNER_PM_PROJECT_NAME must be exist"
        lcm_physicalsize_token = config_map["CUSTOM_KERNEL_LCM"].strip().split()[0].split("_")[1]
        for index, c in enumerate(lcm_physicalsize_token):
            if c.isdigit():
                lcm_size = int(lcm_physicalsize_token[index:].strip())
                break
        while lcm_size < 300:
            lcm_size = lcm_size * 10
        lcm_height = int(config_map["LCM_HEIGHT"])
        lcm_width = int(config_map["LCM_WIDTH"])

        print "CustomLcdDesity, lcm size: %d" % lcm_size
        print "CustomLcdDesity, lcm_height:%d" % lcm_height
        print "CustomLcdDesity, lcm_width:%d" % lcm_width

        real_lcd_desity =  int(100 * math.sqrt(lcm_height * lcm_height + lcm_width * lcm_width) / lcm_size)

        list_lcd_desity = (120, 160, 240, 320, 480, 640)
        min_delta = 999
        standard_lcd_desity = 0
        for tmp_lcd_desity in list_lcd_desity:
            if abs(real_lcd_desity - tmp_lcd_desity) < min_delta:
                min_delta = abs(real_lcd_desity - tmp_lcd_desity)
                standard_lcd_desity = tmp_lcd_desity
        config_map["VANZO_INNER_CUSTOM_OVERRIDE_PROP"] += " ro.sf.lcd_density=%d" % standard_lcd_desity

        list_standard_aapt = ("ldpi", "mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi")
        standard_aapt = list_standard_aapt[list_lcd_desity.index(standard_lcd_desity)]

        print "CustomLcdDesity, standard_lcd_desity:%d" % standard_lcd_desity
        print "CustomLcdDesity, standard_aapt:%s" % standard_aapt

        if "xxxhdpi" == standard_aapt:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG=xxxhdpi xxhdpi xhdpi hdpi"
        elif "xxhdpi" == standard_aapt:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG=xxhdpi xhdpi hdpi"
        elif "xhdpi" == standard_aapt:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG=xhdpi hdpi"
        else:
            config_string = "VANZO_PRODUCT_AAPT_CONFIG={0}".format(standard_aapt)

        return 1, [config_string,]
    """
