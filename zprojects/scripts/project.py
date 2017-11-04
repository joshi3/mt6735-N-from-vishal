#!/usr/bin/env python
#encoding=utf-8
#first author:wangfei
import os,os.path
import sys
import glob
import re
import ConfigParser
import shutil
import traceback

from vanzo_worker import VanzoWorker
from bridge import *
from build_modem import get_modem
from bool_calculator import BoolCalculator

class Project():
    def __init__(self,config_name,output=True,is_custom_tool=False):
        self.is_custom_tool=is_custom_tool
        self.COMPANY="vanzo"
        self.products={}
        self.config_name=config_name
        self.begin_dir=os.getcwd()
        self.config_root="zprojects"
        self.modem_root="modems"
        self.worker=VanzoWorker()
        #record all macros defined in env
        self.macro_map={}
        self.product_map={}
        #for parents list
        self.inherit_list=[]
        #sub map include all VANZO_INNER_ macro
        self.inner_macro_map={}
        #sub map include all by name macro for android and kernel and so on
        self.by_name_macro_list=[]
        #sub map include all by value macro for android and kernel  and so on
        self.by_value_macro_list=[]
        #sub map include all by name and value macro
        self.name_value_macro_map={}
        #featureoption
        self.feature_option_map={}
        #resource map:
        self.resource_map={}
        #po map:
        self.po_map={}
        #kernel config map
        self.kernel_config_map={}
        #all env ,need export to compile environment
        self.env_file=None
        #macros mk use in mkfile and c,c++
        self.macro_file=None
        #feature option file
        self.feature_option_file=None
        #for kernelconfig file
        self.kernel_config_file=None
        #featureoption tool
        self.feature_tool="zprojects/scripts/javaoptgen.pl"
        #for special SUFFIX
        self.special_suffix={
        "_ADDED":None,
        "_OVERRIDED":None,
        "_FINAL":None,
        "_INTERFACE":self.check_interface,
        } 
        #for all plugins
        self.plugins_list=self.get_all_plugins()
        self.output=output
        self.old_by_name_list=[
                "HIGH_BATTERY_VOLTAGE_SUPPORT",
                "MTK_PUMP_EXPRESS_PLUS_SUPPORT",
                "GANGYUN_CAMERA_BEAUTY",
                "GANGYUN_BOKEH_SUPPORT",
                "MTK_LCM_PHYSICAL_ROTATION_HW",
        ]
        self.old_by_value_list=[
                "VANZO_ACC_TOP_OR_BOT",
                "CUSTOM_KERNEL_HALL",
        ]
        self.old_by_name_value_list=[
                "VANZO_SUB_CAM_ROTATION", 
                "VANZO_MAIN_CAM_ROTATION",
        ]
        #for kernel used
        self.old_special_value_list=[
        ]
        #for kernel used
        self.old_special_name_value_list=[
                "LCM_HEIGHT", 
                "LCM_WIDTH",
        ]
        self.old_featureoption_list=[
        "MTK_FM_SUPPORT_STUB", "MTK_FM_TX_SUPPORT_STUB" , "MTK_RADIO_SUPPORT_STUB" , "MTK_AGPS_APP_STUB", "MTK_GPS_SUPPORT_STUB" , "HAVE_MATV_FEATURE_STUB", "MTK_BT_SUPPORT_STUB" , "MTK_WLAN_SUPPORT_STUB" , "MTK_TTY_SUPPORT_STUB" , "MTK_NFC_SUPPORT_STUB" , "HIGH_BATTERY_VOLTAGE_SUPPORT",
        #from 82kk javaoption.pm
        "GEMINI", "MTK_AUDIO_PROFILES", "MTK_AUDENH_SUPPORT", "MTK_BT_PROFILE_AVRCP13", "MTK_GEMINI_ENHANCEMENT", "MTK_SNS_SUPPORT", "MTK_MEMORY_COMPRESSION_SUPPORT", "MTK_LCA_SUPPORT", "MTK_WAPI_SUPPORT", "MTK_QVGA_LANDSCAPE_SUPPORT", "MTK_BT_SUPPORT", "MTK_CAMERA_APP_3DHW_SUPPORT", "MTK_WAPPUSH_SUPPORT", "HAVE_APPC_FEATURE", "MTK_AGPS_APP", "MTK_YGPS_APP", "MTK_OOBE_APP", "MTK_SCREEN_OFF_WIFI_OFF", "MTK_FM_TX_SUPPORT", "MTK_VT3G324M_SUPPORT", "MTK_VOICE_UI_SUPPORT", "MTK_VOICE_UNLOCK_SUPPORT", "MTK_MT519X_FM_SUPPORT", "MTK_DM_APP", "MTK_MATV_ANALOG_SUPPORT", "MTK_WLAN_SUPPORT", "MTK_IPO_SUPPORT", "MTK_IPOH_SUPPORT", "MTK_GPS_SUPPORT", "MTK_OMACP_SUPPORT", "MTK_BT_30_HS_SUPPORT", "HAVE_MATV_FEATURE", "MTK_BT_21_SUPPORT", "MTK_BT_30_SUPPORT", "MTK_BT_40_SUPPORT", "MTK_BT_FM_OVER_BT_VIA_CONTROLLER", "MTK_BT_PROFILE_OPP", "MTK_BT_PROFILE_SIMAP", "MTK_BT_PROFILE_PRXM", "MTK_BT_PROFILE_PRXR", "MTK_BT_PROFILE_HIDH", "MTK_BT_PROFILE_FTP", "MTK_BT_PROFILE_PBAP", "MTK_BT_PROFILE_MANAGER", "MTK_BT_PROFILE_BPP", "MTK_BT_PROFILE_BIP", "MTK_BT_PROFILE_DUN", "MTK_BT_PROFILE_PAN", "MTK_BT_PROFILE_HFP", "MTK_BT_PROFILE_A2DP", "MTK_BT_PROFILE_AVRCP", "MTK_BT_PROFILE_AVRCP14", "MTK_BT_PROFILE_TIMEC", "MTK_BT_PROFILE_TIMES", "MTK_BT_PROFILE_MAPS", "MTK_BT_PROFILE_MAPC", "MTK_BT_PROFILE_SPP", "MTK_DEDICATEDAPN_SUPPORT", "MTK_SEARCH_DB_SUPPORT", "MTK_DIALER_SEARCH_SUPPORT", "MTK_DHCPV6C_WIFI", "MTK_FM_SHORT_ANTENNA_SUPPORT", "MTK_MDLOGGER_SUPPORT", "MTK_TTY_SUPPORT", "MTK_WB_SPEECH_SUPPORT", "MTK_WPA2PSK_SUPPORT", "MTK_DUAL_MIC_SUPPORT", "HAVE_AWBENCODE_FEATURE", "HAVE_AACENCODE_FEATURE", "MTK_WIFI_HOTSPOT_SUPPORT", "MTK_CTA_SUPPORT", "MTK_FM_SUPPORT", "MTK_DM_ENTRY_DISPLAY", "MTK_THEMEMANAGER_APP", "MTK_PHONE_VT_MM_RINGTONE", "MTK_PHONE_VT_VOICE_ANSWER", "MTK_PHONE_VOICE_RECORDING", "MTK_POWER_SAVING_SWITCH_UI_SUPPORT", "MTK_FD_SUPPORT", "MTK_DRM_APP", "MTK_VLW_APP", "MTK_SMS_FILTER_SUPPORT", "MTK_GEMINI_3G_SWITCH", "MTK_IPV6_SUPPORT", "MTK_MULTI_STORAGE_SUPPORT", "MTK_MTKLOGGER_SUPPORT", "MTK_EMULATOR_SUPPORT", "MTK_SHARE_MODEM_SUPPORT", "MTK_SHARE_MODEM_CURRENT", "MTK_EAP_SIM_AKA", "MTK_THEMEMAMANGER_APP", "MTK_LOG2SERVER_APP", "MTK_FM_RECORDING_SUPPORT", "MTK_AVI_PLAYBACK_SUPPORT", "MTK_AUDIO_APE_SUPPORT", "MTK_FLV_PLAYBACK_SUPPORT", "MTK_WML_SUPPORT", "MTK_TB_APP_LANDSCAPE_SUPPORT", "HAVE_VORBISENC_FEATURE", "MTK_FD_FORCE_REL_SUPPORT", "MTK_BRAZIL_CUSTOMIZATION", "MTK_BRAZIL_CUSTOMIZATION_CLARO", "MTK_BRAZIL_CUSTOMIZATION_VIVO", "MTK_WMV_PLAYBACK_SUPPORT", "MTK_HDMI_SUPPORT", "HAVE_AEE_FEATURE", "MTK_FOTA_ENTRY", "MTK_SCOMO_ENTRY", "MTK_OGM_PLAYBACK_SUPPORT", "MTK_MTKPS_PLAYBACK_SUPPORT", "MTK_SEND_RR_SUPPORT", "MTK_RAT_WCDMA_PREFERRED", "MTK_SMSREG_APP", "MTK_FM_RX_SUPPORT", "MTK_DEFAULT_DATA_OFF", "MTK_TB_APP_CALL_FORCE_SPEAKER_ON", "MTK_EMMC_SUPPORT", "MTK_SIM_RECOVERY", "MTK_CAMCORDER_PROFILE_MID_MP4", "MTK_DISPLAY_HIGH_RESOLUTION", "MTK_AUDIO_HD_REC_SUPPORT", "MTK_LAUNCHER_UNREAD_SUPPORT", "MTK_FM_50KHZ_SUPPORT", "MTK_S3D_SUPPORT", "MTK_BSP_PACKAGE", "MTK_TETHERINGIPV6_SUPPORT", "MTK_PHONE_NUMBER_GEODESCRIPTION", "MTK_AUDIOPROFILE_SELECT_MMS_RINGTONE_SUPPORT", "MTK_LOG2SERVER_INTERNAL", "MTK_DT_SUPPORT", "EVDO_DT_SUPPORT", "EVDO_DT_VIA_SUPPORT", "MTK_SHARED_SDCARD", "MTK_2SDCARD_SWAP", "ENCRY_PARTITION_SUPPORT", "MTK_IMEI_LOCK", "MTK_ENS_SUPPORT", "MTK_RAT_BALANCING", "MTK_ACMT_DEBUG", "MTK_TB_HW_DEBUG", "MTK_VSS_SUPPORT", "MTK_FSCK_MSDOS_MTK", "WIFI_WPS_PIN_FROM_AP", "WIFI_WEP_KEY_ID_SET", "MTK_ENABLE_VIDEO_EDITOR", "OP01_CTS_COMPATIBLE", "MTK_ENABLE_MD1", "MTK_ENABLE_MD2", "MTK_NETWORK_TYPE_ALWAYS_ON", "MTK_EMMC_DISCARD", "HAVE_CMMB_FEATURE", "MTK_NFC_SUPPORT", "MTK_NFC_MT6605", "MTK_NFC_MSR3110 ", "MTK_NFC_ADDON_SUPPORT", "MTK_NFC_APP_SUPPORT", "MTK_BENCHMARK_BOOST_TP", "MTK_FLIGHT_MODE_POWER_OFF_MD", "MTK_DATAUSAGE_SUPPORT", "NATIVE_AUDIO_PREPROCESS_ENABLE", "MTK_AAL_SUPPORT", "MTK_TETHERING_EEM_SUPPORT", "MTK_WFD_SUPPORT", "MTK_BEAM_PLUS_SUPPORT", "MTK_MT8193_HDMI_SUPPORT", "MTK_GEMINI_3SIM_SUPPORT", "MTK_GEMINI_4SIM_SUPPORT", "MTK_WEB_NOTIFICATION_SUPPORT", "HAVE_ADPCMENCODE_FEATURE", "MTK_SYSTEM_UPDATE_SUPPORT", "MTK_USES_VR_DYNAMIC_QUALITY_MECHANISM", "MTK_SD_SUPPORT", "MTK_SIM_HOT_SWAP", "MTK_VIDEO_THUMBNAIL_PLAY_SUPPORT", "MTK_RADIOOFF_POWER_OFF_MD", "MTK_BIP_SCWS", "MTK_CTPPPOE_SUPPORT", "MTK_IPV6_TETHER_PD_MODE ", "MTK_CACHE_MERGE_SUPPORT", "MTK_FAT_ON_NAND", "MTK_LAUNCH_TIME_OPTIMIZE", "MTK_LCA_RAM_OPTIMIZE", "MTK_LCA_ROM_OPTIMIZE", "MTK_TELEPHONY_MODE", "MTK_MDM_LAWMO", "MTK_MDM_FUMO", "MTK_MDM_SCOMO", "MTK_MAV_PLAYBACK_SUPPORT", "MTK_MULTISIM_RINGTONE_SUPPORT", "MTK_MT8193_HDCP_SUPPORT", "MTK_CDS_EM_SUPPORT", "MTK_STREAMING_VIDEO_SUPPORT", "MTK_NO_NEED_USB_LED", "PURE_AP_USE_EXTERNAL_MODEM", "MTK_SHOW_MSENSOR_TOAST_SUPPORT", "MTK_WFD_HDCP_TX_SUPPORT", "MTK_NFC_OMAAC_SUPPORT", "MTK_NFC_OMAAC_CMCC", "MTK_WORLD_PHONE", "MTK_NO_TRAN_ANIM", "MTK_PERFSERVICE_SUPPORT", "MTK_HW_KEY_REMAPPING", "MTK_AUDIO_CHANGE_SUPPORT", "MTK_LOW_BAND_TRAN_ANIM", "MTK_HDMI_HDCP_SUPPORT", "MTK_INTERNAL_HDMI_SUPPORT", "MTK_INTERNAL_MHL_SUPPORT", "MTK_OWNER_SDCARD_ONLY_SUPPORT", "MTK_ONLY_OWNER_SIM_SUPPORT", "MTK_SIM_HOT_SWAP_COMMON_SLOT", "MTK_AUTOIP_SUPPORT", "MTK_SEC_WFD_VIDEO_PATH_SUPPORT", "MTK_CTA_SET", "MTK_NFC_SE_NUM", "MTK_CTSC_MTBF_INTERNAL_SUPPORT", "MTK_3GDONGLE_SUPPORT", "MTK_DEVREG_APP", "EVDO_IR_SUPPORT", "MTK_MULTI_PARTITION_MOUNT_ONLY_SUPPORT", "MTK_WIFI_CALLING_RIL_SUPPORT", "MTK_TVOUT_SUPPORT", "MTK_TABLET_PLUGIN_BUILD", "MTK_DRM_KEY_MNG_SUPPORT", "MTK_OVERLAY_ENGINE_SUPPORT", "MTK_DOLBY_DAP_SUPPORT", "MTK_TRANSPARENT_BAR_SUPPORT", "MTK_MOBILE_MANAGEMENT", "MTK_CLEARMOTION_SUPPORT", "MTK_LTE_DC_SUPPORT", "MTK_LTE_SUPPORT", "MTK_ENABLE_MD5", "MTK_CHIPTEST_INT", "MTK_USER_ROOT_SWITCH", "MTK_FEMTO_CELL_SUPPORT", "MTK_SAFEMEDIA_SUPPORT", "MTK_UMTS_TDD128_MODE", "MTK_BESLOUDNESS_SUPPORT", "MTK_3DWORLD_APP", "MTK_SINGLE_IMEI", "MTK_SINGLE_3DSHOT_SUPPORT", "MTK_SDIOAUTOK_SUPPORT", "MTK_WIFIWPSP2P_NFC_SUPPORT", "MTK_RILD_READ_IMSI", "SIM_REFRESH_RESET_BY_MODEM", "MTK_SUBTITLE_SUPPORT", "MTK_DFO_RESOLUTION_SUPPORT", "MTK_SMARTBOOK_SUPPORT", "MTK_PERSIST_PARTITION_SUPPORT", "MTK_DX_HDCP_SUPPORT", "MTK_CAMERA_OT_SUPPORT", "MTK_LIVE_PHOTO_SUPPORT", "MTK_MOTION_TRACK_SUPPORT", "MTK_PLAYREADY_SUPPORT", "MTK_SEC_VIDEO_PATH_SUPPORT", "MTK_VIDEOORB_APP", "MTK_HOTKNOT_SUPPORT", "MTK_PRIVACY_PROTECTION_LOCK", "MTK_TELEPHONY_BOOTUP_MODE_SLOT1", "MTK_TELEPHONY_BOOTUP_MODE_SLOT2", "MTK_BG_POWER_SAVING_SUPPORT", "MTK_CSD_DIALER_SUPPORT", "MTK_VIDEO_HEVC_SUPPORT", "MTK_BG_POWER_SAVING_UI_SUPPORT", "MTK_SLOW_MOTION_VIDEO_SUPPORT", "MTK_TOUCH_BOOST", "MTK_DM_AGENT_SUPPORT", "MTK_VOICE_CONTACT_SEARCH_SUPPORT", "MTK_VIDEO_4KH264_SUPPORT", "MTK_PASSPOINT_R1_SUPPORT", "MTK_CAM_GESTURE_SUPPORT", "MTK_HUIYOU_LOVEFISHING_APP", "MTK_HUIYOU_GAMEHALL_APP", "MTK_HUIYOU_WABAOJINGYING_APP", "MTK_HUIYOU_SYJT_APP", "MTK_MULTI_WINDOW_SUPPORT", "MTK_IMS_SUPPORT", "MTK_VOLTE_SUPPORT", "BUILD_CTS", "VANZO_PSENSOR_GESTURE_SUPPORT", "VANZO_NEWSENSOR_GESTURE_SUPPORT", "VANZO_TASK_MANAGER_SUPPORT", "VANZO_MAIN_CAMERA_RATIO_4_3", "VANZO_SUB_CAMERA_RATIO_4_3", "VANZO_TOUCHPANEL_GESTURES_SUPPORT", "VANZO_CAMERA_HIGH_BRIGHTNESS", "VANZO_CAMERA_VIDEO_MPEG_4", "VANZO_GPRS_OPEN_DIALOG_SUPPORT", "VANZO_SMART_COVER_SUPPORT", "VANZO_SMALL_WINDOW_SUPPORT", "VANZO_SINGLE_IMEI", "VANZO_FORCE_WRITE_IMEI", "VANZO_OTOUCHPAD_SUPPORT", "VANZO_CAMERA_SHUTTER_SOUND_SWITCH", "VANZO_VTRUNK_SUPERUSER_SUPPORT", "VANZO_CAMERA_TIME_STAMP_SWITCH", "VANZO_CAMERA_GESTURE_SUPPORT", "MTK_TEE_SUPPORT", "MICROTRUST_TEE_SUPPORT", "TRUSTKERNEL_TEE_SUPPORT", "TRUSTTONIC_TEE_SUPPORT",
        ]
        #must clear the work dir
        self.work_dir="zprojects/obj/"
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)

        sys.path.append(os.path.abspath("zprojects/scripts/plugins"))
        #for preprocess cmds map
        self.preprocess_cmds_map={
        "VANZO_PREPROCESS_MEMBER_CLASS":self.get_member_class_config,
        }
        #for custom variable process func
        self.custom_path_func={
        "VANZO_INNER_CUSTOM_MEMORY_HEADER_PATH":self.get_custom_memory_header_path,
        "VANZO_INNER_CUSTOM_PARTITION_TABLE_PATH":self.get_custom_partition_table_path,
        }

        #z35-zp,means z35 and z35-zp config
        segments=config_name.split("-")
        lens=len(segments)
        self.project_name=None
        self.config_path_basename=None
        cfg=None
        last_map={}
        cfg_list=[]
        cfg_path=None
        #maybe future will use the other file,so we use a list
        common_list=["zprojects/common/env_common.ini"]
        #added for support platform config
        common_map={}
        common_parents_list=[]
        for item in common_list:
            if not os.path.exists(item):
                continue
            cfg_map=self.parse_config(item)
            common_parents_list.extend(cfg_map.keys())
            self.macro_map.update(cfg_map)
            if "common" in self.macro_map: 
                #last_map.update(self.macro_map["common"])
                self.merge_config(self.macro_map["common"],common_map)

        for i in xrange(0,lens):
            cfg="-".join(segments[0:i+1])
            #print "cfg:",cfg
            self.inherit_list.append(cfg)
            if cfg in self.macro_map:
                #last_map.update(self.macro_map[cfg])
                self.merge_config(self.macro_map[cfg],last_map)
                
                continue
            cfg_path=os.path.join(self.config_root,cfg,"env_%s.ini"%(cfg))
            #print "cfg_path:",cfg_path
            if not os.path.exists(cfg_path):
                #my_dbg_vanzo("file %s not exist\n"%(cfg_path),LEVEL_WARNING)
                continue
            cfg_map=self.parse_config(cfg_path)
            self.macro_map.update(cfg_map)
            #last_map.update(self.macro_map[cfg])
            self.merge_config(self.macro_map[cfg],last_map)

        #print "self.macro_map:",self.macro_map
        if config_name not in self.macro_map:
            my_dbg_vanzo("Error:project config %s not exist!\n"%(config_name),LEVEL_ERROR)
            raise "%s not exist"%(config_name)

        self.product_map=last_map
        self.product_map["VANZO_INNER_CURRENT_CONFIG_NAME"]=self.config_name
        if "VANZO_INNER_PROJECT_NAME" not in self.product_map:
            self.product_map["VANZO_INNER_PROJECT_NAME"]=os.path.basename(os.path.dirname(cfg_path))

        self.project_name=self.product_map["VANZO_INNER_PROJECT_NAME"].replace("\"","")
        #do not touch this,for some script depends this
        if output:
            my_dbg_vanzo("current project_name:%s"%(self.project_name),self.project_name)
        #to parse the ProjectConfig.mk then the project related config
        self.board_project_name=self.project_name.split('-',1)[0]
        #my_dbg_vanzo("the board_project_name:%s\n"%(self.board_project_name))
        self.product_map["VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE"]=self.board_project_name
        #added for define marco,such as:VANZO_BOARD_A20
        key="VANZO_BOARD_%s"%(self.board_project_name.upper())
        self.product_map[key]="yes"
        #for the define of the ProjectConfig.mk and the define of kernel is not the same,I do not why mtk use this settings
        self.project_config_path="device/%s/%s/ProjectConfig.mk"%(self.COMPANY,self.board_project_name)
        project_config_map=self.parse_project_config(self.project_config_path)
        #get current platform
        if "MTK_PLATFORM" in project_config_map:
            self.current_platform=project_config_map["MTK_PLATFORM"].upper()
        elif "CONFIG_MTK_PLATFORM" in project_config_map:
            self.current_platform=project_config_map["CONFIG_MTK_PLATFORM"].upper()
        else:
            raise "MTK_PLATFORM not exist"
        #here to get the platform config
        platform_config=os.path.join(self.config_root,self.current_platform.lower(),"env.ini")
        if os.path.exists(platform_config):
            cfg_map=self.parse_config(platform_config)
            self.macro_map.update(cfg_map)
            self.merge_config(cfg_map[self.current_platform.lower()],common_map)
            self.inherit_list.insert(0,self.current_platform.lower())

         
        #print "common_map:",common_map
        self.merge_config(self.product_map,common_map)
        self.product_map = common_map


        common_parents_list.extend(self.inherit_list)
        self.inherit_list=common_parents_list
        #print self.inherit_list

        #print "self.product_map:",self.product_map
        #last to add the projectconfig map
        project_config_map.update(self.product_map)
        self.product_map=project_config_map
        self.macro_map['ProjectConfig']=project_config_map
        self.inherit_list.insert(0,'ProjectConfig')
        self.product_map['inherit']=' '.join(self.inherit_list)

        self.config_dir=os.path.join(self.config_root,self.project_name,self.config_name)
        self.project_dir=os.path.join(self.config_root,self.project_name)
        self.board_dir=os.path.join(self.config_root,self.board_project_name)
        self.platform_dir=os.path.join(self.config_root,self.current_platform.lower())
        self.common_dir=os.path.join(self.config_root,"common")
        self.feature_overlay_dir=os.path.join(self.config_root,"common/feature_overlay")
            
        #here is the main proces
        res,error_info=self.parse_map(self.product_map)
        if res == False:
            raise "parse_map error"
        self.config_path_basename=cfg

        self.get_config_macro_history()
        #header_name="src/preloader/custom_MemoryDevice.h"

    def get_config_map(self,config_name):
        if config_name in self.macro_map:
            return self.macro_map[config_name]

        return None
    def get_config_macro_history(self): 
        history_map={}
        macros_all_info_map={}
        history_map[self.config_name]=macros_all_info_map
        #print self.inherit_list
        for key,value in self.product_map.items():
            key_values_list=[]
            for item in self.inherit_list:
                if item in self.macro_map:
                    inherit_map=self.macro_map[item]
                    if key in inherit_map:
                        if not isinstance(inherit_map[key],dict):
                            key_values_list.append(inherit_map[key]+':'+item)
            #if value not in key_values_list:
               #print "Error why %s:%s not in any config"%(key,value)
                #print self.macro_map['common']
                #raise "get_config_macro_history error"
                #key_values_list.append(value)
            macros_all_info_map[key]=key_values_list
        #print history_map
        return history_map
             
        
    def parse_project_config(self,project_config_path):
        if not project_config_path:
            return False,"%s not exist"%(project_config_path)
        project_config_map={}
        with open(project_config_path) as in_file:
            regex=re.compile("^(\S+)\s*=\s*(\S+.*)")
            lines=in_file.readlines()
            for item in lines:
                item=item.strip()
                index=item.find('#')
                if index>=0:
                    item=item[0:index]
                item=item.strip() 
                match=re.match(regex,item)
                if not match:
                    continue
                project_config_map[match.group(1)]=match.group(2)

        #print "project_config_map:",project_config_map
        return project_config_map
                

    def parse_config(self,config_name):
        config_map={}
        paser = ConfigParser.ConfigParser()
        paser.optionxform=str
        paser.read(config_name)
        sections = paser.sections() 
        for sec in sections:
            config_map[sec] = dict(paser.items(sec))
        return config_map
    def merge_config(self,sub_map,config_map,reverse=False):
        res,error_info = self.preprocess_config(sub_map)
        if res == False:
            raise "Error to preprocess_config"
        for key,value in sub_map.items():
            if key+"_FINAL" in config_map:
                my_dbg_vanzo("Warning!%s in the config_map,but someone override it\n"%(key+"_FINAL"),LEVEL_WARNING)
                continue
            if key.endswith("_FINAL"):
                real_key=key[:-6]
                if real_key in sub_map:
                    my_dbg_vanzo("Error,why %s and %s coexist in the config\n"%(key,real_key),LEVEL_ERROR)
                    sys.exit(-1)
                if real_key in config_map:
                    my_dbg_vanzo("Warning!find %s,so remove %s from config_map\n"%(key,real_key),LEVEL_WARNING)
                    config_map.pop(real_key)
                config_map[key]=value
            elif key.endswith("_ADDED"):
                if key[:-6] in sub_map:
                    my_dbg_vanzo("Error,in %s %s and %s exist in the same time,this must be a error!\n"%(self.config_name,key[:-6],key),LEVEL_ERROR)
                    sys.exit(-1)
                real_key=key[:-6]
                if key not in config_map:
                    if real_key in config_map:
                        #here left the member class before,so we can override it,such as package config
                        config_map[key]=config_map[real_key]+" "+value
                        config_map.pop(real_key)
                    else:
                        config_map[key]=value
                else:
                    if real_key in config_map:
                        my_dbg_vanzo("Error,why %s and %s coexist in config_map"%(real_key,key),LEVEL_ERROR)
                        sys.exit(-1)
                    else:
                        if not reverse:
                            config_map[key]=config_map[key]+" "+value
                        else:
                            config_map[key]=value+" "+config_map[key]

            elif key.endswith("_OVERRIDED"):
                real_key=key[:-10]
                config_map[real_key]=value
            else:
                #if key not in config_map:
                config_map[key]=value

    def get_member_class_config(self,key,config_map):
        classes=config_map[key].split()
        #print "classes,cwd:",classes,os.getcwd()
        classes.reverse()
        for item in classes:
            config_name="zprojects/virtual/"+item+"/env.ini"
            if not os.path.exists(config_name):
                my_dbg_vanzo("Error %s not exist\n"%(config_name),LEVEL_ERROR);
                return False,"%s not exist\n"%(config_name)
            sub_map=self.parse_config(config_name)[item]
            #here filter the already configed key
            for key,value in sub_map.items():
                special=False
                if key not in config_map:
                    continue
                for key_suffix in self.special_suffix.keys():
                    if key.endswith(key_suffix):
                        special=True
                        break
                if special:
                    continue
                sub_map.pop(key)
                    
            self.merge_config(sub_map,config_map,True);
        return True,None
        
    def preprocess_config(self,config_map):
        #for all preprocess macro config the before prio first,and the preprocess macro can modify the config_map
        for key,value in self.preprocess_cmds_map.items():
            if key in config_map:
                res,error_info = value(key,config_map)
                config_map.pop(key)
                if res == False:
                    return res,error_info
        return True,None

    def get_all_plugins(self):
        plugin_dir=os.path.join(self.config_root,"scripts/plugins/")
        if not os.path.exists(plugin_dir):
            return []
        file_list=glob.glob(plugin_dir+"*.py") 
        #print "file_list:",file_list
        type_list=[]
        for item in file_list:
            #print "item:",item
            base_name=os.path.basename(item)
            type_str,_=os.path.splitext(base_name)
            if type_str == "__init__":
                continue
            #print "type_str:",type_str
            type_list.append(type_str.strip())


        #print "plugin list:",type_list
            
        return type_list

    def get_copy_settings(self,config_map):
        copy_key="VANZO_INNER_CUSTOM_COPY"
        copy_settings="PRODUCT_COPY_FILES += "
        copy_list=[]
        if copy_key in config_map:
            value=config_map[copy_key].strip()
            copy_settings=copy_settings+value+"\n"
            copy_list.append(copy_settings)

        #print "copy_list:",copy_list
        return copy_list


    def get_prop_settings(self,config_map):
        prop_override_key="VANZO_INNER_CUSTOM_OVERRIDE_PROP"
        prop_added_key="VANZO_INNER_CUSTOM_ADDED_PROP"
        prop_override_settings="PRODUCT_PROPERTY_OVERRIDES+="
        prop_added_settings=prop_added_key+"="
        prop_list=[]
        if prop_override_key in config_map:
            value=config_map[prop_override_key].strip()
            if len(value)>0:
                prop_settings=prop_override_settings+value+"\n"
                prop_list.append(prop_settings)
        if prop_added_key in config_map:
            value=config_map[prop_added_key].strip()
            if len(value)>0:
                prop_settings=prop_added_settings+value+"\n"
                prop_list.append(prop_settings)

        return prop_list



    def get_overlay_settings(self,config_map):
        #here add the overlay support
        #first is the config overlay,then extra overlay,then project overlay,then board overlay,then common/ui overlay
        overlay_name="overlay"
        ui_style="common_ui"
        if "VANZO_INNER_UI_STYLE" in config_map and len(config_map["VANZO_INNER_UI_STYLE"].strip())>0:
            ui_style=config_map["VANZO_INNER_UI_STYLE"]
        #overlay_settings="PRODUCT_PACKAGE_OVERLAYS +="
        overlay_settings=""

        config_overlay_ui=os.path.join(self.config_dir,overlay_name,ui_style)
        config_overlay=os.path.join(self.config_dir,overlay_name)
        inherit_overlay_list=[]
        #print self.inherit_list
        for item in self.inherit_list:
            if item.find('-')<0:
                continue
            if not self.config_name.startswith(item) or item == self.config_name:
                continue
            parent_overlay=os.path.join(self.project_dir,item,overlay_name)
            parent_overlay_ui=os.path.join(self.project_dir,item,overlay_name,ui_style)
            inherit_overlay_list.append(parent_overlay)
            inherit_overlay_list.append(parent_overlay_ui)

        inherit_overlay_list.reverse()
        '''
        if "VANZO_INNER_EXTRA_OVERLAY" in config_map:
            extra_overlay=config_map["VANZO_INNER_EXTRA_OVERLAY"]
        else:
            extra_overlay=""
        '''

        feature_overlay=""
        if "VANZO_USE_CUSTOM_WALLPAPERS" in config_map and config_map["VANZO_USE_CUSTOM_WALLPAPERS"]=="yes":
            if "VANZO_INNER_FEATURE_OVERLAY" in config_map:
                feature_overlay=config_map["VANZO_INNER_FEATURE_OVERLAY"]
            if "BOOT_LOGO" not in config_map:
                my_dbg_vanzo("Error BOOT_LOGO must in config_map\n",LEVEL_ERROR)
                sys.exit(-1)
            reso=config_map["BOOT_LOGO"].split('_',1)[-1]
            feature_overlay+=" "+"default_wallpapers/%s"%(reso)

        
        project_overlay_ui=os.path.join(self.project_dir,overlay_name,ui_style)
        project_overlay=os.path.join(self.project_dir,overlay_name)

        board_overlay=os.path.join(self.board_dir,overlay_name)
        platform_overlay_ui=os.path.join(self.platform_dir,overlay_name,ui_style)
        platform_overlay=os.path.join(self.platform_dir,overlay_name)
        common_overlay_ui=os.path.join(self.common_dir,overlay_name,ui_style)
        common_overlay=os.path.join(self.common_dir,overlay_name)

        #overlay_list=[config_overlay,extra_overlay,project_overlay,board_overlay,platform_overlay,common_overlay]
        #for feature_overlay prio to platform_overlay
        overlay_list=[config_overlay_ui,config_overlay]+inherit_overlay_list+[project_overlay_ui,project_overlay]
        if len(feature_overlay.strip())>0:
            features=feature_overlay.split()
            for item in features:
                path=os.path.join(self.feature_overlay_dir,ui_style,item)
                overlay_list.append(path)
                path=os.path.join(self.feature_overlay_dir,item)
                overlay_list.append(path)
        overlay_list.extend([board_overlay,platform_overlay_ui,platform_overlay,common_overlay_ui,common_overlay])
            
        #print "overlay_list:",overlay_list
        for item in overlay_list:
            item=item.strip()
            if len(item)>1 and os.path.exists(item):
                overlay_settings=overlay_settings+" "+item
        overlay_settings=overlay_settings.strip()+"\n"
        return overlay_settings

    def get_custom_memory_header_path(self,key,config_map):
        memory_config_file = "{0}/memory/custom_MemoryDevice.h.{1}".format(self.platform_dir, config_map["VANZO_CUSTOM_MEMORY_BY_NAME_VALUE"])
        assert os.path.exists(memory_config_file), "{0} not exists!".format(memory_config_file)
        write_line="%s=%s"%(key,memory_config_file)
        return write_line 

    def get_custom_partition_table_path(self,key,config_map):
        #./build/build/tools/ptgen/MT6582/partition_table_MT6582.xls
        partition_xls_name="src/lk/partition_table_%s.xls"%(self.current_platform)
        config_file=os.path.join(self.config_dir,partition_xls_name)
        project_file=os.path.join(self.project_dir,partition_xls_name)
        board_file=os.path.join(self.board_dir,partition_xls_name)
        platform_file=os.path.join(self.platform_dir,partition_xls_name)
        file_list=[config_file,project_file,board_file,platform_file]
        write_line=""
        for item in file_list:
            if os.path.exists(item):
                write_line="%s=%s"%(key,item)
                break
        return write_line 
        
    def get_custom_path_variable(self,config_map):
        write_list=[]
        for key,value in self.custom_path_func.items():
            write_line=value(key,config_map)
            write_line=write_line.strip()
            if write_line and len(write_line)>1:
                write_list.append(write_line+"\n")


        return write_list
        
    def check_interface(self,real_key,suffix,config_map):
        if real_key not in config_map:
            if not real_key.startswith('MTK'):
                return False,"Error,%s not exist in config_map"%(real_key)

        return True,None
    def process_presuffix(self,config_map):
        for key,value in config_map.items()[:]:
            key=key.strip()
            for key_suffix,process_func in self.special_suffix.items():
                lens=len(key_suffix)
                if key.endswith(key_suffix):
                    real_key=key[:-lens]
                    if process_func:
                        res,error_info=process_func(real_key,key_suffix,config_map)
                        if res == False:
                            my_dbg_vanzo(error_info,LEVEL_ERROR)
                            sys.exit(-1)
                    else:
                        if real_key not in config_map:
                            config_map[real_key]=value
                        else:
                            my_dbg_vanzo("%s and %s coexist in the ini tree\n"%(real_key,key),LEVEL_WARNING)
                        config_map.pop(key)
                    break
        
    def post_process_featureoption(self,featureoption_map,config_map):
        for item in self.old_featureoption_list:
            if "VANZO_FEATURE_"+item in config_map:
                featureoption_map[item]=config_map["VANZO_FEATURE_"+item]
            elif item in config_map:
                featureoption_map[item]=config_map[item]
            else:
                featureoption_map[item]="no"

    def is_normal_string(self,nocase_value):
        if nocase_value == 'y' or nocase_value == 'yes' or nocase_value == 'n' or nocase_value == 'no' or nocase_value.isdigit() or len(nocase_value)<1:
            return False
        if nocase_value[0]=='-' and nocase_value[1:].strip().isdigit():
           return False
        return True
    #here we do not support recursive env?env?env?,for I think now no one need it
    def process_env_macro(self,value,config_map):
        def get_pair_index(start_index,value):
            index_list=[]
            work_value=value[start_index+1:] 
            for index,item in enumerate(work_value):
                if item == '?':
                    #print "index:",index
                    index_list.append(index)
                elif item == ':':
                    if len(index_list)>0:
                        #print "here pop one index:",index.pop()
                        #index_list.pop()
                        continue
                    else:
                        #print "here return %d+%d+1"%(index,start_index)
                        return index+start_index+1
                    
        if not value.startswith("env-"):
            return value
        depends=value[4:]
        if '?' not in depends:
            if depends in config_map:
                value=self.process_env_macro(config_map[depends],config_map)
            else:
                my_dbg_vanzo("%s depends %s,but %s not set"%(value,depends,depends),LEVEL_ERROR)
                sys.exit(-1)
        else:
            index_yes=depends.find('?')
            index_no=depends.rfind(':')
            #print "index_yes:",index_yes
            #index_no=get_pair_index(index_yes,depends)
            #print "index_yes,index_no,depends",index_yes,index_no,depends

            yes_value=depends[index_yes+1:index_no].strip()
            if index_no > 0:
                no_value=depends[index_no+1:].strip()
            else:
                #no_value=""
                #left to future to expand
                return value
            
            depends_key=depends[:index_yes].strip()
            if depends_key in config_map:
                depends_value=config_map[depends_key]
                depends_value=self.expand_value(depends_value,config_map).lower()
                '''
                if  depends_value != "yes" and depends_value != "no":
                    my_dbg_vanzo("Error %s depends %s,but %s value is %s not yes or no"%(value,depends_key,depends_key,depends_value),LEVEL_ERROR)
                    sys.exit(-1)
                '''
                if depends_value.lower() == "yes" or depends_value.lower() == "y" or (depends_value.isdigit() and int(depends_value)!=0) or (not depends_value.isdigit() and depends_value.lower() != "no" and depends_value.lower()!="n" and len(depends_value)>0):
                    value=self.process_env_macro(yes_value,config_map)
                else:
                    value=self.process_env_macro(no_value,config_map)
            else:
                my_dbg_vanzo("%s depends %s,but %s not set"%(value,depends_key,depends_key),LEVEL_ERROR)
                sys.exit(-1)
        #print "depends %s,value %s\n"%(depends,value)

        return value
    def process_cmds_value(self,value,config_map):
        start_index=value.find("`")
        if start_index < 0:
            my_dbg_vanzo("format start error in process_cmds_value\n",LEVEL_ERROR)
            sys.exit(-1)
        start_value=value[:start_index]
        end_index=value.rfind("`")
        if end_index < 0:
            my_dbg_vanzo("format end error in process_cmds_value\n",LEVEL_ERROR)
            sys.exit(-1)
        end_value=value[end_index+1:]
        cmd=value[start_index+1:end_index].strip()

        index=cmd.find("env-")
        if index>=0:
            '''
            segs_list=cmd.split()
            real_value=""
            for one_seg in segs_list:
                if len(one_seg.split("`"))==3:
                    one_seg=self.process_cmds_value(one_seg,config_map)
                if one_seg.startswith("env-"):
                    one_seg=self.process_env_macro(one_seg,config_map)
                real_value+=one_seg+" "
            cmd=real_value.strip()
            if len(cmd.split("`"))==3:
                cmd=self.process_cmds_value(cmd,config_map)
            '''
            cmd=self.expand_value(cmd,config_map)

        returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        if returncode != 0:
            my_dbg_vanzo("cmd %s run error\n"%(cmd),LEVEL_ERROR)
            sys.exit(-1)
        cmd_value=stdoutdata.strip()
        
        return_value=start_value+cmd_value+end_value

        #my_dbg_vanzo("value %s,cmds value:%s\n"%(value,return_value),LEVEL_DBG)
        return return_value

    def process_logic_bool(self,value,config_map):
        bool_worker=BoolCalculator(value)
        bool_value=bool_worker.get_result()
        #my_dbg_vanzo("Bool value:%s is %s\n"%(value,bool_value),LEVEL_DBG)
        if bool_value:
            return 'yes'
        else:
            return 'no'
    def process_minus(self,value):
        if value.find('-') < 0:
            return value
        current_list=value.split() 
        if len(current_list)<=1:
            if not self.is_normal_string(value):
                return value
        add_list=[] 
        minus_list=[]
        for item in current_list:
            if item.startswith('-'):
                minus_list.append(item[1:]) 
            else:
               add_list.append(item) 
        for item in minus_list:
            if item in add_list:
                add_list.remove(item)
        return ' '.join(add_list)

    def expand_value(self,value,config_map):
        if not value:
            #my_dbg_vanzo("Error value can not be none\n",LEVEL_ERROR)
            return value

        #segs_list=value.split()
        value=value.strip()
        empty_regex=re.compile("\s")
        one_line=""
        split=0
        s_quotes=0
        d_quotes=0
        segs_list=[]
        for index,item in enumerate(value):
            #print "index,item:",index,item
            if re.match(empty_regex,item):
                if len(one_line)>0 and (s_quotes % 2 == 0) and (d_quotes % 2 == 0) :
                    one_line+=item
                    segs_list.append(one_line)
                    one_line=""
                else:
                    one_line+=item
            else:
                if item=="\'":
                    s_quotes+=1 
                    if s_quotes % 2 == 0 and len(one_line)>0:
                        one_line+=item
                        segs_list.append(one_line)
                        one_line=""
                        s_quotes = 0
                    else:
                        one_line+=item
                elif item == "\"":
                    d_quotes+=1 
                    if d_quotes % 2 == 0 and len(one_line)>0:
                        one_line+=item
                        segs_list.append(one_line)
                        one_line=""
                        d_quotes = 0
                    else:
                        one_line+=item
                else:
                    one_line+=item
        else:
            if len(one_line.strip()) > 0:
                segs_list.append(one_line)
                
        #print "segs_list:",segs_list

        real_value=""
        for one_seg in segs_list:
            one_seg=one_seg.strip()
            if len(one_seg)<1:
                continue
                    
            #here to remove the '\'
            if one_seg.find("\\") >= 0:
                one_seg=one_seg.replace("\n"," ")
                values_list=one_seg.split("\\")
                one_seg=" ".join(values_list)
            if one_seg.startswith("env-"):
                one_seg=self.process_env_macro(one_seg,config_map)
            if len(one_seg.split("`"))==3:
                one_seg=self.process_cmds_value(one_seg,config_map)
            real_value+=one_seg+" "


        value=real_value.strip()
        if value.startswith("env-"):
            value=self.process_env_macro(value,config_map)
        if len(value.split("`"))==3:
            value=self.process_cmds_value(value,config_map)
        if value.find("env-")<0 and value.find("`")<0:
            if value.find("echo")<0 and value.find("grep")<0:
                if value.find("!")>=0 or value.find("&&")>=0 or value.find("||")>=0:
                    value=self.process_logic_bool(value,config_map)

        value=value.strip()
        value=self.process_minus(value)
        return value

    def process_name_value_macro_compatible(self,config_map):
        writes_list=[]
        for item in self.by_value_macro_list:
            if item not in config_map:
                continue
            value_list=config_map[item].replace("\"","").strip()
            if len(value_list)<1:
                continue
            value_list=value_list.split()
            for one_value in value_list:
                if one_value in config_map:
                    if config_map[one_value]!="yes":
                        my_dbg_vanzo("Strange %s already be defined as %s"%(one_value,config_map[one_value]),LEVEL_WARNING)
                    continue
                line="%s=yes"%(one_value.upper())
                writes_list.append(line)
        #here must consider the old mtk projectconfig global define
        mtk_value_list=config_map["AUTO_ADD_GLOBAL_DEFINE_BY_VALUE"].replace("\"","").split()
        for item in mtk_value_list:
            if item not in config_map:
                continue
            value_list=config_map[item].replace("\"","").strip()
            if len(value_list)<1:
                continue
            value_list=value_list.split()
            for one_value in value_list:
                if one_value in config_map:
                    if config_map[one_value]!="yes":
                        my_dbg_vanzo("Strange %s already be defined as %s"%(one_value,config_map[one_value]),LEVEL_WARNING)
                    continue
                line="%s=yes"%(one_value.upper())
                writes_list.append(line)
            
        return writes_list

    def process_plugins(self,config_map):
        #here process the inner macros use plugins
        writes_list=[]
        pwd=os.getcwd()
        os.chdir("zprojects/scripts/plugins")
        from plugins import *
        os.chdir(pwd)
        #print "cwd:",os.getcwd()
        #for item in self.inner_macro_map:
            #nocase_value=self.inner_macro_map[item].lower().strip()
            #if nocase_value == "no" or nocase_value=="" or nocase_value == "n":
                #continue
            #if item in self.inner_macro_map:
        self.plugins_list.sort()
        self.plugins_list.reverse()
        for plugin_str in self.plugins_list:
            #try:
                #print "plugins_str:",plugin_str
                #print "after from"
                #__import__("BasePlugin",globals(),locals(),["BasePlugin"])
                type_name=eval(plugin_str)
                plugin=type_name()
                if plugin.match(config_map):
                    res,error_info=plugin.process(config_map)
                    if res < 0 :
                    #<0 means error
                        assert False, "run {0} failed".format(plugin_str)
                        return False,error_info 
                    elif res > 0:
                    #>0 means break pass,and  the error_info means need added to the writes_list
                        if res == 1:
                            if error_info and len(error_info)>0: 
                                writes_list.extend(error_info)
                        #other value left to future
            #except Exception,e:
            #    print "exception:",e
        return writes_list
    def real_parse_worker(self,config_map):
        writes_list=[]
        #res,error_info = self.preprocess_config(config_map)
        #if res == False:
            #return res,error_info
        self.process_presuffix(config_map)
        for key,value in config_map.items()[:]:
            key=key.strip()
            value=value.strip()
            index=value.find("#")
            if index>=0:
                value=value[0:index]
            #here we support env config used for some depends settings
            value=value.strip()
            value=self.expand_value(value,config_map)
            config_map[key]=value
                
            nocase_value=value.lower()
            if key.startswith("VANZO_RESOURCE_"):
                self.resource_map[key]=value
                #for resource we do not need export the env
                continue
            #for po files
            if key.startswith("VANZO_PO_CONFIG"):
                self.po_map[key]=value
                #for resource we do not need export the env
                continue
            #for some variable depends the other variable
            if key.startswith("VANZO_RAW_"):
                #for raw declare just export to mk file used in other mkfile
                writes_list.append(value)
                continue
            else:
                writes_list.append("%s=%s"%(key,value))
            if key.startswith("VANZO_INNER_"):
                self.inner_macro_map[key]=value
            if key.startswith("VANZO_FEATURE_"):
                #print "key1,value2:",key,value
                if '"' not in value:
                    if self.is_normal_string(nocase_value):
                        self.feature_option_map[key]='"'+value+'"'
                    else:
                        self.feature_option_map[key]=value
                else:
                    self.feature_option_map[key]=value

            if key.startswith("CONFIG_"):
                if len(value)<1:
                    self.kernel_config_map[key]='n'
                else:
                    if not self.is_normal_string(nocase_value):
                        self.kernel_config_map[key]=value 
                    else:
                        if '"' not in value:
                            self.kernel_config_map[key]='"'+value+'"'
                        else:
                            self.kernel_config_map[key]=value 
                #if nocase_value != 'y' and nocase_value != 'yes' and nocase_value != 'n' and nocase_value != 'no' and not nocase_value.isdigit() and len(nocase_value)>=1:
                if self.is_normal_string(nocase_value):
                    #self.by_value_macro_list.extend(value.split())
                    if key.find("_BY_NAME_VALUE")>=0:
                        self.name_value_macro_map[key]=value
                    else:
                        if value.find("-")<0:
                            self.by_value_macro_list.append(key)
                else:
                    if nocase_value == 'y' or nocase_value == 'yes':
                        self.by_name_macro_list.append(key)

            if key.startswith("VANZO_"):
                if key.find("_BY_VALUE")>=0:
                    #self.by_value_macro_list.extend(value.split())
                    if self.is_normal_string(nocase_value):
                        self.by_value_macro_list.append(key)

                elif key.find("_BY_NAME_VALUE")>=0:
                    self.name_value_macro_map[key]=value
                else:
                    #print "name key:",key
                    if nocase_value == 'y' or nocase_value == 'yes':
                        self.by_name_macro_list.append(key)
            elif key.startswith("MTK_"):
                config_key="CONFIG_"+key
                if nocase_value == 'y' or nocase_value == 'yes':
                    if config_key not in self.by_name_macro_list:
                        self.by_name_macro_list.append(config_key)
                    if config_key not in config_map:
                        writes_list.append("%s=y"%(config_key))
                        #self.kernel_config_map[config_key]='y'
                '''
                elif nocase_value == 'n' or nocase_value == 'no':
                    self.kernel_config_map[config_key]='n'
                else:
                    self.kernel_config_map[config_key]=value
                '''

            elif key in self.old_special_name_value_list:
                self.name_value_macro_map["CONFIG_"+key]=value
                writes_list.append("%s=%s"%("CONFIG_"+key,value))
            elif key in self.old_special_value_list:
                self.by_value_macro_list.append("CONFIG_"+key)
                writes_list.append("%s=%s"%("CONFIG_"+key,value))

            if key in self.old_by_value_list:
                if key not in self.by_value_macro_list:
                    self.by_value_macro_list.append(key)
            elif key in self.old_by_name_value_list:
                if key not in self.name_value_macro_map:
                    self.name_value_macro_map[key]=value
            elif key in self.old_by_name_list:
                if nocase_value == 'y' or nocase_value == 'yes':
                    if key not in self.by_name_macro_list:
                        self.by_name_macro_list.append(key)

        return writes_list
    def parse_map(self,config_map):
        '''
        here we must divide into some parts
        resource_map,inner_macro_map, by_name_list,by_value_map,name_value_map,feature_option_map,common_macro_mk
        '''
        if not config_map or len(config_map)<1:
            return False,"No element in config map"
        
        if not "VANZO_INNER_PROJECT_NAME" in config_map:
            my_dbg_vanzo("Error,VANZO_INNER_PROJECT_NAME must be set",LEVEL_ERROR)
            return False,"Error,VANZO_INNER_PROJECT_NAME must be set"
            
        #self.env_file=os.path.join(self.config_root,project_name,"%s.env"%(self.config_name))
        self.env_file=self.config_root+"/"+self.project_name+"/"+"%s.env"%(self.project_name)
        self.macro_file=os.path.join(self.config_root,self.project_name,"%s.mk"%(self.project_name))
        self.resource_file=os.path.join(self.config_root,self.project_name,"%s.cfg"%(self.project_name))
        self.po_file=os.path.join(self.config_root,self.project_name,"%s.po"%(self.project_name))
        self.feature_option_file=os.path.join(self.config_root,self.project_name,"%s.feature"%(self.project_name))
        self.kernel_config_file=os.path.join(self.config_root,self.project_name,"%s.kconfig"%(self.project_name))
        #print "self.env_file %s,macro_file %s,resource_file %s,po file %s"%(self.env_file,self.macro_file,self.resource_file,self.po_file)
        #first delete old
        cmd="rm -rf %s %s %s %s %s %s"%(self.env_file,self.macro_file,self.resource_file,self.po_file,self.feature_option_file,self.kernel_config_file)
        os.system(cmd)
        writes_list=self.real_parse_worker(config_map)
        if not self.output:
            return True,None
                        
        writes_list.extend(self.process_plugins(config_map))
        #here I think I should process the plugins modified macros
        if "VANZO_INNER_PLUGINS_RESULTS" in config_map:
            plugins_map=config_map["VANZO_INNER_PLUGINS_RESULTS"]
            writes_list.extend(self.real_parse_worker(plugins_map))


        VANZO_DEFINE_BY_NAME = " ".join(self.by_name_macro_list)
        VANZO_DEFINE_BY_VALUE = " ".join(self.by_value_macro_list)
        VANZO_DEFINE_BY_NAME_VALUE = " ".join(self.name_value_macro_map.keys())
        #print("VANZO_DEFINE_BY_NAME %s,VANZO_DEFINE_BY_VALUE %s,VANZO_DEFINE_BY_NAME_VALUE %s"%(VANZO_DEFINE_BY_NAME,VANZO_DEFINE_BY_VALUE,VANZO_DEFINE_BY_NAME_VALUE))
        #here process the by value list,for mtk sometimes need use the value to yes ,for example in bootloader
        writes_list.extend(self.process_name_value_macro_compatible(config_map))

                
        env_handle=open(self.env_file,"w") 
        mk_handle=open(self.macro_file,"w")
        resource_handle=open(self.resource_file,"w")
        po_handle=open(self.po_file,"w")
        feature_handle=open(self.feature_option_file,"w")
        kernel_config_handle=open(self.kernel_config_file,"w")

        mk_line="VANZO_DEFINE_BY_NAME = %s\n"%(VANZO_DEFINE_BY_NAME)
        mk_handle.write(mk_line)
        mk_line="VANZO_DEFINE_BY_VALUE = %s\n"%(VANZO_DEFINE_BY_VALUE)
        mk_handle.write(mk_line)
        mk_line="VANZO_DEFINE_BY_NAME_VALUE = %s\n"%(VANZO_DEFINE_BY_NAME_VALUE)
        mk_handle.write(mk_line)
        '''
        #here add the overlay support
        #first is the config overlay,then extra overlay,then project overlay,then board overlay,then common/ui overlay
        overlay_name="overlay"
        ui_style="common_ui"
        if "VANZO_INNER_UI_STYLE" in config_map:
            ui_style=config_map["VANZO_INNER_UI_STYLE"]
        '''

        for item in writes_list:
            env_line="export %s\n"%(item)
            #for kernel config we do not export to env
            if not item.startswith("CONFIG_"):
                """ Vanzo:songlixin on: Sun, 01 Feb 2015 15:43:05 +0800
                if space inside, should add quotation
                """
                position = item.find("=")
                left = item[:position].strip()
                right = item[position+1:].strip()
                assert right.count('"') + right.count("'") != 1
                '''
                if right.count('"') + right.count("'") == 1:
                    print "item:",item
                    sys.exit(-1)
                '''
                if " " in right.strip() and (right.count('"') + right.count("'") == 0):
                    env_line="""export {0}="{1}"\n""".format(left, right)
                """ End of Vanzo:songlixin """
                env_handle.write(env_line)
            #for these ugly process for MTK_PLATFORM macro in the upper and kernel has the different value
            if item.startswith("MTK_PLATFORM"):
                continue
            #added for some no or empty config can not be output to mk file
            index=item.find('=')
            if index > 0:
                value=item[index+1:].strip().lower()
                #if len(value)<1:
                    #continue
                if value == "no" or value == "n":
                    if item.startswith("CONFIG_"):
                        item=item[:index+1]
                elif value == "yes" and item.startswith("CONFIG_"):
                    value="y"
                    item=item[:index+1]+value
            mk_handle.write(item+"\n")

        #here we need process some custom variable output ,for example in preloader
        path_list=self.get_custom_path_variable(config_map)
        if path_list and len(path_list)>0:
            for item in path_list:
                mk_handle.write(item)
                item="export %s\n"%(item)
                env_handle.write(item)

        #here to write the overlay to the last line
        overlay_settings=self.get_overlay_settings(config_map)
        #my_dbg_vanzo("the overlay_settings:%s\n"%(overlay_settings),LEVEL_DBG)
        if len(overlay_settings)>0:
            overlay_settings="PRODUCT_PACKAGE_OVERLAYS +="+overlay_settings
            #first write the header
            mk_header="ifndef VANZO_INNER_ADD_CUSTOM_OVERLAY\n"
            mk_handle.write(mk_header)
            mk_handle.write(overlay_settings)
            #here write the end of mk_handle
            label="VANZO_INNER_ADD_CUSTOM_OVERLAY=yes\n"
            mk_handle.write(label)
            end_line="endif\n"
            mk_handle.write(end_line)
        #here to process the prop settings
        prop_settings=self.get_prop_settings(config_map)
        #my_dbg_vanzo("the prop settings:%s\n"%(prop_settings),LEVEL_DBG)
        if prop_settings and len(prop_settings)>0:
            mk_header="ifndef VANZO_INNER_CUSTOM_PROP\n"
            mk_handle.write(mk_header)
            for item in prop_settings:
                mk_handle.write(item)
            label="VANZO_INNER_CUSTOM_PROP=yes\n"
            mk_handle.write(label)
            #here write the end of mk_handle
            end_line="endif\n"
            mk_handle.write(end_line)

        #here to process the file copy
        copy_settings=self.get_copy_settings(config_map)
        #my_dbg_vanzo("the copy settings:%s\n"%(copy_settings),LEVEL_DBG)
        if copy_settings and len(copy_settings)>0:
            mk_header="ifndef VANZO_INNER_CUSTOM_COPY\n"
            mk_handle.write(mk_header)
            for item in copy_settings:
                mk_handle.write(item)
            label="VANZO_INNER_CUSTOM_COPY=yes\n"
            mk_handle.write(label)
            #here write the end of mk_handle
            end_line="endif\n"
            mk_handle.write(end_line)
        


        resource_handle.write("[%s]\n"%(self.config_name))
        for key,value in self.resource_map.items():
            line="%s=%s\n"%(key,value)
            resource_handle.write(line)

        po_handle.write("[%s]\n"%(self.config_name))
        for key,value in self.po_map.items():
            line="%s=%s\n"%(key,value)
            po_handle.write(line)

        self.post_process_featureoption(self.feature_option_map,config_map)

        key_list=self.feature_option_map.keys()
        key_list.sort()
        for key in key_list:
            line="%s=%s\n"%(key,self.feature_option_map[key])
            feature_handle.write(line)

        key_list=self.kernel_config_map.keys()
        key_list.sort()
        for key in key_list:
            line="%s=%s\n"%(key,self.kernel_config_map[key])
            kernel_config_handle.write(line)
        

        env_handle.close()
        mk_handle.close()
        resource_handle.close()
        po_handle.close()
        feature_handle.close()
        kernel_config_handle.close()

        cmd="%s %s"%(self.feature_tool,self.feature_option_file)
        res = os.system(cmd)
        #print "cmd:",cmd
        #returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
        #print returncode,stdoutdata,stderrdata

        #close(env_handle)
        #close(mk_handle)
        #close(resource_handle)
        #here to process the inner

        # Vanzo:yucheng on: Fri, 23 Sep 2016 15:21:42 +0800
        # Modify to sync Project config
        cmd="cp %s %s.bak"%(self.macro_file, self.project_config_path)
        res=os.system(cmd)
        #print "copy command:\"%s\", current path:%s, return value:%d"%(cmd, os.getcwd(), res)
        if res != 0:
            my_dbg_vanzo("sync project config error(error cmd:%s)\n"%cmd, LEVEL_ERROR)
            sys.exit(-1)
        # End of Vanzo: yucheng

        return True,None
    def get_project_name(self):
        return self.project_name
    def clean_obj(self):
        os.remove(self.env_file)
        os.remove(self.macro_file)
        os.remove(self.resource_file)
        os.remove(self.po_file)
        os.remove(self.feature_option_file)
        os.remove(self.kernel_config_file)
    def compile_modem(self):
        res = get_modem(self.modem_root,self.product_map["VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE"],self.product_map["CUSTOM_MODEM"].split())
        #print "compile res:",res
        if res != 0:
            my_dbg_vanzo("compile modem error\n",LEVEL_ERROR)
            sys.exit(-1)
        return True,None

    def before_compile(self,compile_modem=False):
        if compile_modem:
            return self.compile_modem()
        return True,None
    def after_compile(self):
        #1,first copy the logo.bin
        logo_path=os.path.join(self.config_root,"obj/logo/logo.bin")
        dst_path="out/target/product/%s/"%(self.board_project_name)
        #for VANZO_INNER_USE_CUSTOM_LOGO must be yes
        if os.path.exists(logo_path):
            #my_dbg_vanzo("cp %s to %s\n"%(logo_path,dst_path),LEVEL_DBG)
            cmd="cp %s %s"%(logo_path,dst_path)
            returncode, stdoutdata, stderrdata=self.worker.RunCommand(cmd)
            #print returncode,stderrdata,stderrdata
            if returncode != 0:
                return False,"copy %s to %s error,now %s"%(logo_path,dst_path,os.getcwd())
        self.clean_obj()
        return True,None


             
            
                    
                



if __name__ == '__main__':
    prj=Project(sys.argv[1])
    sys.exit()
