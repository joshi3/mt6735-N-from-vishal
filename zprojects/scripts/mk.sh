#!/bin/bash
if [ $# -lt 1 ];then
    echo "Usage:$0 project_name"
    exit
fi
project_name=$1
shift
eng=$1
shift
cwd=`pwd`
source zprojects/$project_name/$project_name.env
source build/envsetup.sh
export USE_CCACHE=1
echo "board name is $VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE"
echo "eng:$eng"
if [ $eng -eq 1 ];then
    lunch full_$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE-eng
    def_config_name=`ls kernel*/arch/arm*/configs/${VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE}_debug_defconfig`
elif [ $eng -eq 2 ];then
    lunch full_$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE-userdebug
    def_config_name=`ls kernel*/arch/arm*/configs/${VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE}_defconfig`
else
    lunch full_$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE-user
    def_config_name=`ls kernel*/arch/arm*/configs/${VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE}_defconfig`
fi

echo "def_config_name:$def_config_name"
#here first to produce the kernelconfig
#script_name="zprojects/scripts/merge_config.sh"
script_name=`ls ./kernel*/scripts/kconfig/merge_config.sh`
out_dir="zprojects/obj/"
#out_dir="out/target/product/$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE"
echo "out_dir:$out_dir,script_name:$script_name"
mkdir -p $out_dir
custom_config="zprojects/$project_name/$project_name.kconfig"
if [ ! -x $script_name ];then
    chmod u+x $script_name
fi

merge_res=`$script_name -O $out_dir -m $def_config_name $custom_config`
merge_res=$?
echo "merge_res:$merge_res"
if [ $merge_res -eq 0 ];then
    cp $def_config_name $out_dir/
    cp $out_dir/.config $def_config_name
fi

first=$1
if [ $first"yes" == "yes" ];then
    cmd="make -j32"
else
    if [ $first == "preloader" -o $first == "pl" ];then
        echo "Compile preloader beginning..."
        cd vendor/mediatek/proprietary/bootable/bootloader/preloader
        TARGET_PRODUCT=$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE ./build.sh 2>&1 | tee $cwd/pl.log
        res=$?
        cd -
        if [ -e  vendor/mediatek/proprietary/bootable/bootloader/preloader/bin/preloader_$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE.bin ];then
        cp -f vendor/mediatek/proprietary/bootable/bootloader/preloader/bin/preloader_$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE.bin  out/target/product/$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE/
        elif [ -e out/target/product/$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE/obj/PRELOADER_OBJ/bin/preloader_$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE.bin ];then
        cp -f out/target/product/$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE/obj/PRELOADER_OBJ/bin/preloader_$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE.bin   out/target/product/$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE/
        fi
        exit
    elif [ $first == "lk" ];then
        echo "Compile lk beginning..."
        cd vendor/mediatek/proprietary/bootable/bootloader/lk
        make -j24 $VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE 2>&1 | tee $cwd/lk.log
        res=$?
        cd -
        cp -f vendor/mediatek/proprietary/bootable/bootloader/lk/build-$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE/lk.bin out/target/product/$VANZO_INNER_BOARD_PROJECT_BY_NAME_VALUE/
        exit
    else
        cmd=$@ 
    fi
fi

echo "cmd is:$cmd"

$cmd

compile_res=$?
if [ $merge_res -eq 0 ];then
    cp $out_dir/`basename $def_config_name` $def_config_name
fi
exit $compile_res
