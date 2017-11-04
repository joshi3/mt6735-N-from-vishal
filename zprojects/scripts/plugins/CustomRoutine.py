from BasePlugin import BasePlugin
import os
import os.path
class CustomRoutine(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_INNER_CUSTOM_BUILD_VERSION":{"ro.custom.build.version":self.process_prop},"VANZO_INNER_CUSTOM_BT_NAME":{"bluetooth.HostName":self.process_custom_conf},"VANZO_INNER_CUSTOM_WIFI_SSID":{"wlan.SSID":self.process_custom_conf},"VANZO_INNER_CUSTOM_DM_MANUFACTURER":{"dm.Manufacturer":self.process_custom_conf},"VANZO_INNER_CUSTOM_DM_SOFTWARE_VERSION":{"dm.SoftwareVersion":self.process_custom_conf},"VANZO_INNER_CUSTOM_WIFI_DIRECT_NAME":None,"VANZO_INNER_CUSTOM_ISO_NAME":None,"VANZO_INNER_CUSTOM_PRODUCT_STRING":None,"VANZO_INNER_CUSTOM_USB_STORAGE_NAME":None,"VANZO_INNER_CUSTOM_SDCARD_VOLUME_NAME":None,"VANZO_INNER_CUSTOM_CAMERA_MANUFACTURER":None,"VANZO_INNER_CUSTOM_CAMERA_MODEL":None,"VANZO_INNER_CUSTOM_DEFAULT_RINGTONE":{"ro.config.ringtone":self.process_prop},"VANZO_INNER_CUSTOM_DEFAULT_RINGTONE_SIM2":{"ro.config.ringtone_sim2":self.process_prop},"VANZO_INNER_CUSTOM_DEFAULT_NOTIFICATION_SOUND":{"ro.config.notification_sound":self.process_prop},"VANZO_INNER_CUSTOM_DEFAULT_DATEFORMAT":{"ro.com.android.dateformat":self.process_prop},"VANZO_INNER_CUSTOM_DEFAULT_ALARM_ALERT":{"ro.config.alarm_alert":self.process_prop}}
        self.added_prop_key="VANZO_INNER_CUSTOM_ADDED_PROP"
        self.override_prop_key="VANZO_INNER_CUSTOM_OVERRIDE_PROP"
        self.out_lines=[]
    def process(self,config_map):
        for item,out_key in self.match_item.items():
            #print "item,out_key",item,out_key
            if item not in config_map:
                continue
            value=config_map[item].strip()
            #print "item,value:",item,value
            if len(value)<1:
                continue
            if not out_key:
                print "Sorry %s now not supported custom"%(item) 
                continue
            #print "out_key:",out_key
            if isinstance(out_key,str):
                #for Android default prop that is in the buildinfo.sh,so we just output the macros to the env and mk
                self.out_lines.append("%s=%s"%(out_key,value))
            elif isinstance(out_key,dict):
                #print "out_key:",out_key
                method=out_key.values()[0]
                res,error_info=method(out_key.keys()[0],item,config_map)
                if res < 0:
                    print "process %s error"%(item)
                    return -1,error_info
                else:
                    if error_info and len(error_info)>0:
                        self.out_lines.extend(error_info)
                    
            else:
                method=out_key
                res,error_info=method(item,config_map)
                if res < 0:
                    print "process %s error"%(item)
                    return -1,error_info
                else:
                    if error_info:
                        self.out_lines.extend(error_info)
        #print "out_lines:",self.out_lines
        return 1,self.out_lines
    def process_prop(self,prop_name,item,config_map):
        value=""
        if prop_name.find("vanzo")>=0:
            if self.added_prop_key in config_map:
                value=config_map[self.added_prop_key]
            value=value+" "+prop_name+"="+config_map[item].strip()
            if len(value.strip())>0:
                config_map[self.added_prop_key]=value
        else:
            if self.override_prop_key in config_map:
                value=config_map[self.override_prop_key]
            value=value+" "+prop_name+"="+config_map[item].strip()
            if len(value.strip())>0:
                config_map[self.override_prop_key]=value
        return 1,None

    def process_custom_conf(self,prop_name,item,config_map):
        #here should process the custom.conf,must return a list
        work_dir="zprojects/obj/"
        cmd="mkdir -p %s"%(work_dir) 
        os.system(cmd)
        filename=os.path.join(work_dir,"custom.conf")
        if not os.path.exists(filename):
            board_conf="device/vanzo/%s/custom.conf"%(config_map["VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE"])
            if os.path.exists(board_conf):
                custom_conf_path=board_conf
            else:
                custom_conf_path="device/mediatek/common/custom.conf"
            print 'custom_conf_path:',custom_conf_path
            cmd="cp %s %s"%(custom_conf_path,work_dir)
            os.system(cmd)
        #modify_lines(self,file_name,content,match_line,only_one=True):
        all_contents= open(filename).read( )
        content=prop_name+"="+config_map[item].strip()
        if all_contents.find(prop_name) >= 0:
            cmd="sed -i 's/%s.*/%s/g' %s"%(prop_name,content,filename)
            os.system(cmd)
        else:
            cmd="echo %s >>%s"%(content,filename)
            os.system(cmd)
            
        copy_key="VANZO_INNER_CUSTOM_COPY"
        copy_files=""
        if copy_key in config_map:
            copy_files=config_map[copy_key]
        line="%s:system/vendor/etc/custom.conf"%(filename)
        if copy_files.find(line)<0:
            copy_files=copy_files+" "+line
        #print "copy_files:",copy_files
        config_map[copy_key]=copy_files
        return 1,None
