from BasePlugin import BasePlugin
from bridge import *
import os
import os.path
import xml.dom.minidom
import copy

class SoftwareConfigCheck(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_SOFTWARE_CONFIG_CHECK_SUPPORT":self.process_sw_config_check}
        self.config_root="zprojects"
        self.board_project_name=None
        self.output_path="software_config.log"
        self.debug=False
        self.newline='\r\n'
        #here for key:{prop:func}
        self.check_devices={
            'CUSTOM_KERNEL_LCM':{'LCM':None},
            'CUSTOM_KERNEL_ACCELEROMETER':{'Accelerometer':None},
            'CUSTOM_KERNEL_LENS':{'Lens':None},
            'CUSTOM_KERNEL_TOUCHPANEL':{'Touchpanel':None},
            'CUSTOM_KERNEL_VIBRATOR':{'Vibrator':None},
            'CUSTOM_KERNEL_GYROSCOPE':{'Gyroscope':None},

            'CUSTOM_KERNEL_FLASHLIGHT':{'Flashlight':None},

            'CUSTOM_KERNEL_MAIN_IMGSENSOR':{'Rear Camera':None},
            'CUSTOM_KERNEL_MAIN_BACKUP_IMGSENSOR':{'Rear Camera(backup)':None},
            'CUSTOM_KERNEL_SUB_IMGSENSOR':{'Front Camera':None},
            'CUSTOM_KERNEL_SUB_BACKUP_IMGSENSOR':{'Front Camera(backup)':None},

            'CUSTOM_KERNEL_MAIN_LENS':{'Front Lens':None},
            'CUSTOM_KERNEL_MAIN_BACKUP_LENS':{'Front Lens(backup)':None},
            'CUSTOM_KERNEL_SUB_LENS':{'Rear Lens':None},
            'CUSTOM_KERNEL_SUB_BACKUP_LENS':{'Rear Lens(backup)':None},

            'CUSTOM_KERNEL_MAGNETOMETER':{'Magnetometer':None},
            'CUSTOM_KERNEL_IRDA':{'Irda':None},
            'CUSTOM_KERNEL_HALL':{'Hall':None},
            'CUSTOM_KERNEL_ALSPS':{'P-Sensor':None},
            'VANZO_CUSTOM_MEMORY_BY_NAME_VALUE':{'Memory':self.get_memory_list},
            'VANZO_INNER_CUSTOM_MODEM':{'Modem model':None},
            "MTK_GPS_SUPPORT":{'GPS':None},
            "MTK_NFC_SUPPORT":{'NFC':None},
            'CUSTOM_KERNEL_DTV':{'DTV':None},
            'CONFIG_MTK_FINGERPRINT':{'Finger Print':None},
            'CONFIG_USB_MTK_OTG':{'OTG':None},
            'CUSTOM_KERNEL_LEDS':{'Leds':None},
        }

        self.max_length=260

    def process(self,config_map):
        for item,handler in self.match_item.items():
            if item not in config_map:
                continue
            #value=config_map[item].strip()
            res,error_info=handler(item,config_map)
            if res < 0:
                print "process %s error"%(item)
                return -1,error_info
            else:
                if error_info:
                    self.out_lines.extend(error_info)
        return 1,[]

    def get_memory_list(self,key,prop_name,config_map):
        memory_file=os.path.join(self.config_root,config_map['MTK_PLATFORM'].lower(),'memory','custom_MemoryDevice.h.'+config_map[key])
        if self.debug == True:
            print 'memory_file:',memory_file
        cmd='cat  %s |grep CS_PART_NUMBER | awk \'{print $3}\''%(memory_file)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("Error to get memory info",LEVEL_ERROR)
            return None

        config='  '.join(stdoutdata.split('\n'))
        if self.debug == True:
            print config
        config=config[:self.max_length]
        return prop_name+': '+config+ self.newline + '_'*92 + self.newline

    def process_sw_config_check(self,prop_name,config_map):
        project_name=None
        if "VANZO_INNER_PROJECT_NAME" in config_map:
            project_name=config_map["VANZO_INNER_PROJECT_NAME"]
        else:
            return -1,"VANZO_INNER_PROJECT_NAME must in config_map"

        config_name=None
        if "VANZO_INNER_CURRENT_CONFIG_NAME" in config_map:
            config_name=config_map["VANZO_INNER_CURRENT_CONFIG_NAME"]
        else:
            return -1,"VANZO_INNER_CURRENT_CONFIG_NAME must in config_map"
        value=config_map[prop_name]
        if self.debug == True:
            print 'value:',value
        if value.lower()!='yes':
            return 0,None

        current_value= ' '*36 + 'Software Config Info' + self.newline + '_'*92 + self.newline
        for key,sub_map in sorted(self.check_devices.items(), key=lambda d:d[1], reverse=False):
            if key not in config_map:
                #my_dbg_vanzo('%s not exist'%(key),LEVEL_WARNING)
                continue
            for prop,handler in sub_map.items():
                if not handler:
                    if len(config_map[key].strip())>0:
                        config_value='  '.join(config_map[key].split())
                        #for prop max lenth
                        #config_value=config_map[key].split()
                        config_value=config_value[:self.max_length]
                        current_value=current_value+' '+prop+': '+config_value + self.newline + '_'*92 + self.newline
                    else:
                        current_value=current_value+' '+prop+': '+'N/A' + self.newline + '_'*92 + self.newline
                else:
                    current_value=current_value+' '+handler(key,prop,config_map)
        if self.debug == True:
            print 'current_value :',current_value
        #self.board_project_name=project_name.split('-',1)[0]
        #output_path="out/target/product/%s/softwareConfig.log"%(self.board_project_name)
        #outpput_path="software_config.log"
        if self.debug == True:
            print 'output_path: ' + self.output_path

        current_value=current_value+' '
        os.system("echo '%s' > %s" % (current_value, self.output_path))
        return 0,None

