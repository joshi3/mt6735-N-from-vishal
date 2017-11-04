from BasePlugin import BasePlugin
import os
import sys
class CustomLogo(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_INNER_USE_CUSTOM_LOGO":None}
        self.COMITTER_ENV_KEY = "COMITTER_NAME"
    def need_add_watermark(self,config_map):
        if os.environ.has_key(self.COMITTER_ENV_KEY):
            comitter_name = os.environ[self.COMITTER_ENV_KEY]
        else:
            comitter_name = "scm"
        print "comitter_name:%s" % comitter_name

        if "VANZO_NO_WATERMARK" in config_map and config_map["VANZO_NO_WATERMARK"]=="yes":
            return False
        if "deamon" in comitter_name and not "deamondemo" in comitter_name and not "deamonls" in comitter_name:
            return False
        if "digit_signer" in comitter_name:
            return False
        return True

    def process(self,config_map):
        tool_name="zprojects/scripts/logo.sh"
        if "VANZO_INNER_PROJECT_NAME" not in config_map:
            return -1,"VANZO_INNER_PROJECT_NAME must be exist"
        if "BOOT_LOGO" not in config_map:
            return -1,"BOOT_LOGO must be exist"

        for item in self.match_item.keys():
            value=config_map[item].lower()
            #print "value:",value
            if value != "yes" and value != "y":
                return 0,None

        #print "config_map[VANZO_INNER_CURRENT_CONFIG_NAME]:",config_map["VANZO_INNER_CURRENT_CONFIG_NAME"]
        if "VANZO_LOGO_PATH" in config_map and len(config_map["VANZO_LOGO_PATH"].strip())>0:
            logo_path=config_map["VANZO_LOGO_PATH"].strip()
        else:
            logo_path=os.path.join("zprojects",config_map["VANZO_INNER_PROJECT_NAME"],"binary/logo",config_map["VANZO_INNER_CURRENT_CONFIG_NAME"])
            if not os.path.exists(os.path.join(logo_path,config_map["BOOT_LOGO"])):
                index=logo_path.rfind('-')
                while index > 0:
                    logo_path=logo_path[:index]
                    if os.path.exists(os.path.join(logo_path,config_map["BOOT_LOGO"])):
                        break
                    index=logo_path.rfind('-')
                if index <= 0:
                    logo_path=config_map["VANZO_INNER_CURRENT_CONFIG_NAME"]
            #print 'logo_path:',os.path.join(logo_path,config_map["BOOT_LOGO"])
            logo_path=os.path.basename(logo_path)

        print 'logo_path basename:',logo_path

        if self.need_add_watermark(config_map):
            watermark="yes"
        else:
            watermark="no"
        # Vanzo:yucheng on: Fri, 03 Jun 2016 16:34:37 +0800
        # Modify for logo.bin customization
        pump_express_support = "no"
        wireless_charge_support = "no"
        if "MTK_PUMP_EXPRESS_SUPPOR" in config_map and config_map["MTK_PUMP_EXPRESS_SUPPOR"].lower() == "yes":
            pump_express_support = "yes"
        elif "MTK_PUMP_EXPRESS_PLUS_SUPPORT" in config_map and config_map["MTK_PUMP_EXPRESS_PLUS_SUPPORT"].lower() == "yes":
            pump_express_support = "yes"

        if "MTK_WIRELESS_CHARGER_SUPPORT" in config_map and config_map["MTK_WIRELESS_CHARGER_SUPPORT"].lower() == "yes":
            wireless_charge_support = "yes"
        # End of Vanzo: yucheng
        cmd="%s %s %s %s %s %s %s"%(tool_name,config_map["BOOT_LOGO"],config_map["VANZO_INNER_PROJECT_NAME"],logo_path,watermark,pump_express_support,wireless_charge_support)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        #print "cmd:",cmd
        #print returncode,stdoutdata,stderrdata
        if returncode == 0:
            return 1,None
        else:
            return -1,"%s error"%(cmd)
