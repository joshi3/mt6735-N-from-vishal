from BasePlugin import BasePlugin
from bridge import *
import os
import os.path
import xml.dom.minidom
import copy
class CompatibleInfo(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_COMPATIBLE_INFO":self.process_compatible_info}
        self.config_root="zprojects"
        #here for key:{prop:func}
        self.check_devices={'CUSTOM_KERNEL_LCM':{'ro.compatible.lcm':None},'CUSTOM_KERNEL_ACCELEROMETER':{'ro.compatible.accelerometer':None},
                            'CUSTOM_KERNEL_LENS':{'ro.compatible.lens':None},'CUSTOM_KERNEL_TOUCHPANEL':{'ro.compatible.touchpanel':None},
                            'CUSTOM_KERNEL_VIBRATOR':{'ro.compatible.vibrator':None},'CUSTOM_KERNEL_GYROSCOPE':{'ro.compatible.gyroscope':None},
                            'CUSTOM_KERNEL_MAIN_IMGSENSOR':{'ro.compatible.mainimgsensor':None},'CUSTOM_KERNEL_SUB_IMGSENSOR':{'ro.compatible.subimgsensor':None},
                            'CUSTOM_KERNEL_MAGNETOMETER':{'ro.compatible.magnetometer':None},
                            'CUSTOM_KERNEL_FLASHLIGHT':{'ro.compatible.flashlight':None},'CUSTOM_KERNEL_LEDS':{'ro.compatible.leds':None},
                            'CUSTOM_KERNEL_IRDA':{'ro.compatible.irda':None},'CUSTOM_KERNEL_HALL':{'ro.compatible.hall':None},
                            'CUSTOM_KERNEL_ALSPS':{'ro.compatible.alsps':None},'VANZO_FEATURE_CUSTOM_FINGER_PRINT_BY_VALUE':{'ro.compatible.fingerprint':None},
                            'VANZO_CUSTOM_MEMORY_BY_NAME_VALUE':{'ro.compatible.memory':self.get_memory_list},
                            }
        self.max_length=90

    def process(self,config_map):
        for item,out_key in self.match_item.items():
            #print "item,out_key",item,out_key
            if item not in config_map:
                continue
            #value=config_map[item].strip()
            method=out_key
            res,error_info=method(item,config_map)
            if res < 0:
                print "process %s error"%(item)
                return -1,error_info
            else:
                if error_info:
                    self.out_lines.extend(error_info)
        return 1,[]

    def get_memory_list(self,key,prop_name,config_map):
        memory_file=os.path.join(self.config_root,config_map['MTK_PLATFORM'].lower(),'memory','custom_MemoryDevice.h.'+config_map[key])
        print 'memory_file:',memory_file
        cmd='cat  %s |grep CS_PART_NUMBER | awk \'{print $3}\''%(memory_file)
        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("Error to get memory info",LEVEL_ERROR)
            return None
        
        config='@'.join(stdoutdata.split('\n'))
        print config
        config=config[:self.max_length] 
        return prop_name+'='+config

            

    def process_compatible_info(self,prop_name,config_map):
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
        print 'value:',value
        if value.lower()!='yes' and value.lower() != 'y':
            return 0,None

        current_value=''   
        for key,sub_map in self.check_devices.items():
            if key not in config_map:
                #my_dbg_vanzo('%s not exist'%(key),LEVEL_WARNING)
                continue
            for prop,method in sub_map.items():
                if not method:
                    if len(config_map[key].strip())>0:
                        config_value='@'.join(config_map[key].split())
                        #for prop max lenth
                        config_value=config_value[:self.max_length] 
                        current_value=current_value+' '+prop+'='+config_value
                    else:
                        current_value=current_value+' '+prop+'='+'@'
                else:
                    current_value=current_value+' '+method(key,prop,config_map)
        print 'current_value :',current_value
        new_prop_settings=current_value
        if 'VANZO_INNER_CUSTOM_OVERRIDE_PROP' in config_map:                          
            new_prop_settings=new_prop_settings+' '+config_map['VANZO_INNER_CUSTOM_OVERRIDE_PROP'] 
        config_map['VANZO_INNER_CUSTOM_OVERRIDE_PROP']=new_prop_settings

        return 0,None

