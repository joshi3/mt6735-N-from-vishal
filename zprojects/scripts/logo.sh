#!/bin/bash
BOOT_LOGO=$1
project_name=$2
custom_sp=$3
watermark=$4
# Vanzo:yucheng on: Fri, 03 Jun 2016 16:50:17 +0800
# Added for logo.bin customization
SUPPORT_PUMP_EXPRESS=$5
MTK_WIRELESS_CHARGER_SUPPORT=$6
# End of Vanzo: yucheng

work_dir=zprojects/obj/logo
mkdir -p $work_dir

BMP_TO_RAW=zprojects/tools/bmp_to_raw
ZPIPE=zprojects/tools/zpipe
MKIMG=zprojects/tools/mkimage
#echo "PRODUCT_OUT is $PRODUCT_OUT,BOOT_LOGO:$BOOT_LOGO"

boot_logo_resource=$BOOT_LOGO.raw
logo_image=$work_dir/logo.bin
origin_source_dir="vendor/mediatek/proprietary/bootable/bootloader/lk/dev/logo/"

BASE_LOGO=${BOOT_LOGO##*_}
#echo "BASE_LOGO:before :$BASE_LOGO"
if [ ! -e ${origin_source_dir}/${BASE_LOGO} ]; then 
  BASE_LOGO=$BOOT_LOGO
fi

#echo "the BASE_LOGO:$BASE_LOGO"

#SUPPORT_PUMP_EXPRESS=no
#if [ $MTK_PUMP_EXPRESS_SUPPOR"yes" == "yesyes" ];then
#    SUPPORT_PUMP_EXPRESS=yes
#elif [ $MTK_PUMP_EXPRESS_PLUS_SUPPORT"yes" == "yesyes" ];then
#    SUPPORT_PUMP_EXPRESS=yes
#fi

if [ -e  $origin_source_dir/$BASE_LOGO ];then
    cp -a $origin_source_dir/$BASE_LOGO $work_dir/
fi
mkdir -p $work_dir/$BASE_LOGO
if [ $BASE_LOGO != $BOOT_LOGO -a -e $origin_source_dir/$BOOT_LOGO ];then
    cp -a $origin_source_dir/$BOOT_LOGO/* $work_dir/$BASE_LOGO/
fi
#echo "logo:zprojects/$project_name/binary/logo/$custom_sp/$BOOT_LOGO"
if [ -e zprojects/$project_name/binary/logo/$custom_sp/$BOOT_LOGO ];then
cp -a zprojects/$project_name/binary/logo/$custom_sp/$BOOT_LOGO/* $work_dir/$BASE_LOGO/ 2>/dev/null
fi

SOURCE_LIST="${work_dir}/${BASE_LOGO}/${BOOT_LOGO}_uboot.bmp"
if [ $watermark"yes" == "yesyes" ];then
    cp -f zprojects/resources/watermark* /tmp/
    rm -f /tmp/*.bmp
    phatch -c /tmp/watermark.phatch $SOURCE_LIST
    mv -f /tmp/`basename $SOURCE_LIST` $SOURCE_LIST
fi

if [ $MTK_ALPS_BOX_SUPPORT"yes" != "yesyes" ];then
echo  "logo.bin customization ----> inlude bat animation bmp"

SOURCE_LIST="$SOURCE_LIST \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_battery.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_low_battery.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_charger_ov.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_0.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_1.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_2.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_3.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_4.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_5.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_6.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_7.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_8.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_9.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_num_percent.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_01.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_02.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_03.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_04.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_05.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_06.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_07.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_08.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_09.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_animation_10.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_01.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_02.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_03.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_04.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_05.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_06.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_07.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_08.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_09.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_10_10.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_bg.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_img.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_bat_100.bmp \
            ${work_dir}/${BASE_LOGO}/${BOOT_LOGO}_uboot.bmp "
fi
if [ $SUPPORT_PUMP_EXPRESS"yes" == "yesyes" ];then

echo  "logo.bin customization ----> inlude fast charging bmp"
SOURCE_LIST="$SOURCE_LIST \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_100.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_ani-01.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_ani-02.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_ani-03.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_ani-04.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_ani-05.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_ani-06.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_00.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_01.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_02.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_03.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_04.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_05.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_06.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_07.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_08.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_09.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_fast_charging_percent.bmp"
fi

if [ $MTK_WIRELESS_CHARGER_SUPPORT"yes" == "yesyes" ];then
echo  "logo.bin customization ----> inlude wireless bat bmp"
SOURCE_LIST="$SOURCE_LIST \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_00.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_01.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_02.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_03.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_04.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_05.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_06.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_07.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_08.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_09.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_num_percent.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_10_0.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_10_1.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_10_2.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_10_3.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_30_0.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_30_1.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_30_2.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_30_3.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_60_0.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_60_1.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_60_2.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_60_3.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_90_0.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_90_1.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_90_2.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_90_3.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_0.bmp \
            ${work_dir}/${BASE_LOGO}/${BASE_LOGO}_wireless_bat_100.bmp"
fi

#echo "SOURCE_LIST:$SOURCE_LIST"

if [ ! -e $MKIMG -o ! -e $BMP_TO_RAW -o ! -e $ZPIPE ];then
    #echo "$MKIMG or $BMP_TO_RAW or $ZPIPE is not exist"
    exit
fi
if [ ! -x $MKIMG ]; then 
    chmod a+x $MKIMG; 
fi
if [ ! -x $BMP_TO_RAW ]; then 
    chmod a+x $BMP_TO_RAW; 
fi
if [ ! -x $ZPIPE ];then
    chmod a+x $ZPIPE
fi
OBJ_LIST=
for item in $SOURCE_LIST;
do
        basename=`basename $item`
        obj=$work_dir/${basename%.bmp}.raw
        $BMP_TO_RAW $obj $item
        OBJ_LIST="$OBJ_LIST $obj"
done
#echo "OBJ_LIST:$OBJ_LIST"
$ZPIPE -l 9 $boot_logo_resource $OBJ_LIST
$MKIMG $boot_logo_resource LOGO > $logo_image
#echo "logo.bin:$logo_image"

