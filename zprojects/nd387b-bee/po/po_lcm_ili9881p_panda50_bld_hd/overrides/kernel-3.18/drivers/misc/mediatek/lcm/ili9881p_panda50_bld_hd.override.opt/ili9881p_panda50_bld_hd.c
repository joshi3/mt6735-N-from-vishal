/* Copyright Statement:
 *
 * This software/firmware and related documentation ("MediaTek Software") are
 * protected under relevant copyright laws. The information contained herein
 * is confidential and proprietary to MediaTek Inc. and/or its licensors.
 * Without the prior written permission of MediaTek inc. and/or its licensors,
 * any reproduction, modification, use or disclosure of MediaTek Software,
 * and information contained herein, in whole or in part, shall be strictly prohibited.
 */
/* MediaTek Inc. (C) 2010. All rights reserved.
 *
 * BY OPENING THIS FILE, RECEIVER HEREBY UNEQUIVOCALLY ACKNOWLEDGES AND AGREES
 * THAT THE SOFTWARE/FIRMWARE AND ITS DOCUMENTATIONS ("MEDIATEK SOFTWARE")
 * RECEIVED FROM MEDIATEK AND/OR ITS REPRESENTATIVES ARE PROVIDED TO RECEIVER ON
 * AN "AS-IS" BASIS ONLY. MEDIATEK EXPRESSLY DISCLAIMS ANY AND ALL WARRANTIES,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR NONINFRINGEMENT.
 * NEITHER DOES MEDIATEK PROVIDE ANY WARRANTY WHATSOEVER WITH RESPECT TO THE
 * SOFTWARE OF ANY THIRD PARTY WHICH MAY BE USED BY, INCORPORATED IN, OR
 * SUPPLIED WITH THE MEDIATEK SOFTWARE, AND RECEIVER AGREES TO LOOK ONLY TO SUCH
 * THIRD PARTY FOR ANY WARRANTY CLAIM RELATING THERETO. RECEIVER EXPRESSLY ACKNOWLEDGES
 * THAT IT IS RECEIVER'S SOLE RESPONSIBILITY TO OBTAIN FROM ANY THIRD PARTY ALL PROPER LICENSES
 * CONTAINED IN MEDIATEK SOFTWARE. MEDIATEK SHALL ALSO NOT BE RESPONSIBLE FOR ANY MEDIATEK
 * SOFTWARE RELEASES MADE TO RECEIVER'S SPECIFICATION OR TO CONFORM TO A PARTICULAR
 * STANDARD OR OPEN FORUM. RECEIVER'S SOLE AND EXCLUSIVE REMEDY AND MEDIATEK'S ENTIRE AND
 * CUMULATIVE LIABILITY WITH RESPECT TO THE MEDIATEK SOFTWARE RELEASED HEREUNDER WILL BE,
 * AT MEDIATEK'S OPTION, TO REVISE OR REPLACE THE MEDIATEK SOFTWARE AT ISSUE,
 * OR REFUND ANY SOFTWARE LICENSE FEES OR SERVICE CHARGE PAID BY RECEIVER TO
 * MEDIATEK FOR SUCH MEDIATEK SOFTWARE AT ISSUE.
 *
 * The following software/firmware and/or related documentation ("MediaTek Software")
 * have been modified by MediaTek Inc. All revisions are subject to any receiver's
 * applicable license agreements with MediaTek Inc.
 */

/*****************************************************************************
 *  Copyright Statement:
 *  --------------------
 *  This software is protected by Copyright and the information contained
 *  herein is confidential. The software may not be copied and the information
 *  contained herein may not be used or disclosed except with the written
 *  permission of MediaTek Inc. (C) 2008
 *
 *  BY OPENING THIS FILE, BUYER HEREBY UNEQUIVOCALLY ACKNOWLEDGES AND AGREES
 *  THAT THE SOFTWARE/FIRMWARE AND ITS DOCUMENTATIONS ("MEDIATEK SOFTWARE")
 *  RECEIVED FROM MEDIATEK AND/OR ITS REPRESENTATIVES ARE PROVIDED TO BUYER ON
 *  AN "AS-IS" BASIS ONLY. MEDIATEK EXPRESSLY DISCLAIMS ANY AND ALL WARRANTIES,
 *  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF
 *  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR NONINFRINGEMENT.
 *  NEITHER DOES MEDIATEK PROVIDE ANY WARRANTY WHATSOEVER WITH RESPECT TO THE
 *  SOFTWARE OF ANY THIRD PARTY WHICH MAY BE USED BY, INCORPORATED IN, OR
 *  SUPPLIED WITH THE MEDIATEK SOFTWARE, AND BUYER AGREES TO LOOK ONLY TO SUCH
 *  THIRD PARTY FOR ANY WARRANTY CLAIM RELATING THERETO. MEDIATEK SHALL ALSO
 *  NOT BE RESPONSIBLE FOR ANY MEDIATEK SOFTWARE RELEASES MADE TO BUYER'S
 *  SPECIFICATION OR TO CONFORM TO A PARTICULAR STANDARD OR OPEN FORUM.
 *
 *  BUYER'S SOLE AND EXCLUSIVE REMEDY AND MEDIATEK'S ENTIRE AND CUMULATIVE
 *  LIABILITY WITH RESPECT TO THE MEDIATEK SOFTWARE RELEASED HEREUNDER WILL BE,
 *  AT MEDIATEK'S OPTION, TO REVISE OR REPLACE THE MEDIATEK SOFTWARE AT ISSUE,
 *  OR REFUND ANY SOFTWARE LICENSE FEES OR SERVICE CHARGE PAID BY BUYER TO
 *  MEDIATEK FOR SUCH MEDIATEK SOFTWARE AT ISSUE.
 *
 *  THE TRANSACTION CONTEMPLATED HEREUNDER SHALL BE CONSTRUED IN ACCORDANCE
 *  WITH THE LAWS OF THE STATE OF CALIFORNIA, USA, EXCLUDING ITS CONFLICT OF
 *  LAWS PRINCIPLES.  ANY DISPUTES, CONTROVERSIES OR CLAIMS ARISING THEREOF AND
 *  RELATED THERETO SHALL BE SETTLED BY ARBITRATION IN SAN FRANCISCO, CA, UNDER
 *  THE RULES OF THE INTERNATIONAL CHAMBER OF COMMERCE (ICC).
 *
 *****************************************************************************/
#include "lcm_drv.h"
#ifdef BUILD_LK
#include <platform/upmu_common.h>
#include <platform/mt_gpio.h>
#include <platform/gpio_const.h>
#include <platform/mt_i2c.h>
#include <platform/mt_pmic.h>
#include <string.h>
#elif defined(BUILD_UBOOT)
#include <asm/arch/mt_gpio.h>
#else
#include <mt-plat/mt_gpio.h>
#include <mach/gpio_const.h>
/*#include <mach/mt_pm_ldo.h>*/
#include "disp_dts_gpio.h"
#ifdef CONFIG_MTK_LEGACY
#include <mach/mt_gpio.h>
#endif
#endif
#ifdef CONFIG_MTK_LEGACY
#include <cust_gpio_usage.h>
#endif
#ifndef CONFIG_FPGA_EARLY_PORTING
#if defined(CONFIG_MTK_LEGACY)
#include <cust_i2c.h>
#endif
#endif
#if defined(BUILD_LK)
#define LCM_DEBUG  printf
#define LCM_FUNC_TRACE() printf("huyl [uboot] %s\n",__func__)
#else
#define LCM_DEBUG  printk
#define LCM_FUNC_TRACE() printk("huyl [kernel] %s\n",__func__)
#endif
// ---------------------------------------------------------------------------
//  Local Constants
// ---------------------------------------------------------------------------

#define FRAME_WIDTH  (720)
#define FRAME_HEIGHT (1280)

#define LCM_ID			(0x93)

#ifndef TRUE
#define TRUE 1
#endif

#ifndef FALSE
#define FALSE 0
#endif
//blestech add 
extern int g_bl229x_enbacklight ;
extern int lcm_off_flag ;
//blestech end
static unsigned int lcm_esd_test = FALSE;      ///only for ESD test

// ---------------------------------------------------------------------------
//  Local Variables
// ---------------------------------------------------------------------------

static LCM_UTIL_FUNCS lcm_util = {0};
//#define GPIO_LCM_RST (GPIO146 | 0x80000000)
#define SET_RESET_PIN(v)    (lcm_util.set_reset_pin((v)))

#define UDELAY(n) (lcm_util.udelay(n))
#define MDELAY(n) (lcm_util.mdelay(n))

#define REGFLAG_DELAY             							0XFE
#define REGFLAG_END_OF_TABLE      							0x100   // END OF REGISTERS MARKER

// ---------------------------------------------------------------------------
//  Local Functions
// ---------------------------------------------------------------------------

#define dsi_set_cmdq_V2(cmd, count, ppara, force_update)	        lcm_util.dsi_set_cmdq_V2(cmd, count, ppara, force_update)
#define dsi_set_cmdq(pdata, queue_size, force_update)		lcm_util.dsi_set_cmdq(pdata, queue_size, force_update)
#define wrtie_cmd(cmd)										lcm_util.dsi_write_cmd(cmd)
#define write_regs(addr, pdata, byte_nums)					lcm_util.dsi_write_regs(addr, pdata, byte_nums)
#define read_reg(cmd)											lcm_util.dsi_dcs_read_lcm_reg(cmd)
#define read_reg_v2(cmd, buffer, buffer_size)   				lcm_util.dsi_dcs_read_lcm_reg_v2(cmd, buffer, buffer_size)

#define dsi_lcm_set_gpio_mode(pin, mode)                                    lcm_util.set_gpio_mode(pin, mode)
#define dsi_lcm_set_gpio_dir(pin, dir)                                      lcm_util.set_gpio_dir(pin, dir)
#define dsi_lcm_set_gpio_pull_enable(pin, en)                               lcm_util.set_gpio_pull_enable(pin, en)
#define dsi_lcm_set_gpio_out(pin, out)                                      lcm_util.set_gpio_out(pin, out)

extern void set_lcm_rst_pin(int state);

struct LCM_setting_table {
  unsigned cmd;
  unsigned char count;
  unsigned char para_list[64];
};

static struct LCM_setting_table lcm_initialization_setting[] = {
{0xFF,3,{0x98,0x81,0x01}},
{0x44,1,{0x31}},

{0xFF,3,{0x98,0x81,0x05}},
{0x1B,1,{0x11}}, 
{0x04,1,{0x21}},
{0x30,1,{0xF7}}, 
//{0x36,1,{0x03}}, 
{0x29,1,{0x00}},
{0x2A,1,{0x10}},//0x14 
{0x38,1,{0xA8}}, 
{0x52,1,{0x5F}},
{0x54,1,{0x28}},
{0x55,1,{0x25}},
{0x1A,1,{0x50}},

{0xFF,3,{0x98,0x81,0x02}},
{0x15,1,{0x10}},
{0x42,1,{0x2F}},//0x25
{0x01,1,{0x50}},

{0x57,1,{0x00}},
{0x58,1,{0x28}},
{0x59,1,{0x38}},
{0x5A,1,{0x14}},
{0x5B,1,{0x18}},
{0x5C,1,{0x2B}},
{0x5D,1,{0x1F}},
{0x5E,1,{0x20}},
{0x5F,1,{0xA0}},
{0x60,1,{0x1E}},
{0x61,1,{0x2A}},
{0x62,1,{0x82}},
{0x63,1,{0x1A}},
{0x64,1,{0x17}},
{0x65,1,{0x4C}},
{0x66,1,{0x20}},
{0x67,1,{0x26}},
{0x68,1,{0x4A}},
{0x69,1,{0x58}},
{0x6A,1,{0x30}},

{0x6B,1,{0x00}},
{0x6C,1,{0x28}},
{0x6D,1,{0x38}},
{0x6E,1,{0x14}},
{0x6F,1,{0x18}},
{0x70,1,{0x2B}},
{0x71,1,{0x1F}},
{0x72,1,{0x20}},
{0x73,1,{0xA0}},
{0x74,1,{0x1E}},
{0x75,1,{0x2A}},
{0x76,1,{0x82}},
{0x77,1,{0x1A}},
{0x78,1,{0x17}},
{0x79,1,{0x4C}},
{0x7A,1,{0x20}},
{0x7B,1,{0x26}},
{0x7C,1,{0x4A}},
{0x7D,1,{0x58}},
{0x7E,1,{0x30}},


{0xFF,3,{0x98,0x81,0x06}},
{0x01,1,{0x03}},
{0x2B,1,{0x0A}},
//{0x4B,1,{0x1F}},

{0xFF,3,{0x98,0x81,0x00}},
  {0x35, 1,{0x00}},
  {0x11,0,{0x00}},
  {REGFLAG_DELAY, 120, {}}, 
  {0x29,0,{0x00}},
  {REGFLAG_DELAY, 10, {}},

  {REGFLAG_END_OF_TABLE, 0x00, {}}

};
static struct LCM_setting_table lcm_sleep_out_setting[] = {
  // Sleep Out
  {0x11, 0, {0x00}},
  {REGFLAG_DELAY, 120, {}},

  // Display ON
  {0x29, 0, {0x00}},
  {REGFLAG_DELAY, 10, {}},

  {REGFLAG_END_OF_TABLE, 0x00, {}}
};


static struct LCM_setting_table lcm_sleep_mode_in_setting[] = {

  // Display off sequence

  {0x28, 0, {0x00}},
  {REGFLAG_DELAY, 20, {}},

  // Sleep Mode On
  {0x10, 0, {0x00}},
  {REGFLAG_DELAY, 120, {}},
  {REGFLAG_END_OF_TABLE, 0x00, {}}
};
static struct LCM_setting_table lcm_compare_id_setting[] = {
  // Display off sequence

  {REGFLAG_DELAY, 10, {}},

  {REGFLAG_END_OF_TABLE, 0x00, {}}
};


static void push_table(struct LCM_setting_table *table, unsigned int count, unsigned char force_update)
{
  unsigned int i;

  for(i = 0; i < count; i++) {

    unsigned cmd;
    cmd = table[i].cmd;

    switch (cmd) {

      case REGFLAG_DELAY :
        MDELAY(table[i].count);
        break;

      case REGFLAG_END_OF_TABLE :
        break;

      default:
        dsi_set_cmdq_V2(cmd, table[i].count, table[i].para_list, force_update);
        //MDELAY(2);
    }
  }

}

// ---------------------------------------------------------------------------
//  LCM Driver Implementations
// ---------------------------------------------------------------------------

static void lcm_set_util_funcs(const LCM_UTIL_FUNCS *util)
{
  memcpy(&lcm_util, util, sizeof(LCM_UTIL_FUNCS));
}

static void lcm_get_params(LCM_PARAMS *params)
{

  memset(params, 0, sizeof(LCM_PARAMS));

  params->type = LCM_TYPE_DSI;

  params->width = FRAME_WIDTH;
  params->height = FRAME_HEIGHT;

  // enable tearing-free
  params->dbi.te_mode = LCM_DBI_TE_MODE_VSYNC_ONLY;
  params->dbi.te_edge_polarity = LCM_POLARITY_RISING;

  params->dsi.mode   = SYNC_PULSE_VDO_MODE; //SYNC_PULSE_VDO_MODE;//BURST_VDO_MODE;

  // DSI
  /* Command mode setting */
  params->dsi.LANE_NUM = LCM_FOUR_LANE;
  //The following defined the fomat for data coming from LCD engine.
  params->dsi.data_format.color_order = LCM_COLOR_ORDER_RGB;
  params->dsi.data_format.trans_seq = LCM_DSI_TRANS_SEQ_MSB_FIRST;
  params->dsi.data_format.padding = LCM_DSI_PADDING_ON_LSB;
  params->dsi.data_format.format = LCM_DSI_FORMAT_RGB888;

  params->dsi.intermediat_buffer_num = 0;	//because DSI/DPI HW design change, this parameters should be 0 when video mode in MT658X; or memory leakage

  params->dsi.PS = LCM_PACKED_PS_24BIT_RGB888;
  params->dsi.word_count = 720 * 3;

  params->dsi.vertical_sync_active				= 4;// 3    2
  params->dsi.vertical_backporch					= 16;//11;// 16   1
  params->dsi.vertical_frontporch					= 20;//8; // 1  12
  params->dsi.vertical_active_line				= FRAME_HEIGHT;

  params->dsi.horizontal_sync_active				= 40;//30;// 50  2
  params->dsi.horizontal_backporch				= 60; //65 ;
  params->dsi.horizontal_frontporch				= 60; //30 ;
  params->dsi.horizontal_active_pixel				= FRAME_WIDTH;


  params->dsi.PLL_CLOCK =220;//270;
  params->dsi.ssc_disable = 1;  // ssc disable control (1: disable, 0: enable, default: 0)

  params->dsi.noncont_clock=1; 
  params->dsi.noncont_clock_period=1;    
  params->dsi.esd_check_enable = 1; 
  params->dsi.customization_esd_check_enable = 1; 
  params->dsi.lcm_esd_check_table[0].cmd = 0x0a; 
  params->dsi.lcm_esd_check_table[0].count = 1; 
  params->dsi.lcm_esd_check_table[0].para_list[0] = 0x9c; 

}
extern void lcm_set_enp_bias(bool Val);
static void lcm_init_power(void)
{
#ifdef BUILD_LK
  dsi_lcm_set_gpio_mode(GPIO_LCD_BIAS_ENP_PIN, GPIO_MODE_00);
  dsi_lcm_set_gpio_dir(GPIO_LCD_BIAS_ENP_PIN, GPIO_DIR_OUT);
  dsi_lcm_set_gpio_out(GPIO_LCD_BIAS_ENP_PIN, GPIO_OUT_ONE);
  mt_set_gpio_mode(GPIO_LCM_PWR, GPIO_MODE_00);
  mt_set_gpio_dir(GPIO_LCM_PWR, GPIO_DIR_OUT);
  mt_set_gpio_out(GPIO_LCM_PWR, GPIO_OUT_ONE);
#else
  lcm_set_enp_bias(1);
#endif

}

static void lcm_suspend_power(void)
{
#ifdef BUILD_LK
  dsi_lcm_set_gpio_mode(GPIO_LCD_BIAS_ENP_PIN, GPIO_MODE_00);
  dsi_lcm_set_gpio_dir(GPIO_LCD_BIAS_ENP_PIN, GPIO_DIR_OUT);
  dsi_lcm_set_gpio_out(GPIO_LCD_BIAS_ENP_PIN, GPIO_OUT_ZERO);
  mt_set_gpio_mode(GPIO_LCM_PWR, GPIO_MODE_00);
  mt_set_gpio_dir(GPIO_LCM_PWR, GPIO_DIR_OUT);
  mt_set_gpio_out(GPIO_LCM_PWR, GPIO_OUT_ZERO);
#else
  lcm_set_enp_bias(0);
#endif

}

static void lcm_resume_power(void)
{
#ifdef BUILD_LK
  dsi_lcm_set_gpio_mode(GPIO_LCD_BIAS_ENP_PIN, GPIO_MODE_00);
  dsi_lcm_set_gpio_dir(GPIO_LCD_BIAS_ENP_PIN, GPIO_DIR_OUT);
  dsi_lcm_set_gpio_out(GPIO_LCD_BIAS_ENP_PIN, GPIO_OUT_ONE);
  mt_set_gpio_mode(GPIO_LCM_PWR, GPIO_MODE_00);
  mt_set_gpio_dir(GPIO_LCM_PWR, GPIO_DIR_OUT);
  mt_set_gpio_out(GPIO_LCM_PWR, GPIO_OUT_ONE);
#else
  lcm_set_enp_bias(1);
#endif

}
//blestech add
static struct LCM_setting_table lcm_on_setting[] = {
  // Sleep Out
  //{0x11, 0, {0x00}},
  //{REGFLAG_DELAY, 120, {}},

  // Display ON
  {0x29, 0, {0x00}},
  {REGFLAG_DELAY, 10, {}},

  {REGFLAG_END_OF_TABLE, 0x00, {}}
};


static struct LCM_setting_table lcm_off_setting[] = {

  // Display off sequence

  {0x28, 0, {0x00}},
  {REGFLAG_DELAY, 20, {}},

  // Sleep Mode On
  //{0x10, 0, {0x00}},
  //{REGFLAG_DELAY, 120, {}},
  {REGFLAG_END_OF_TABLE, 0x00, {}}
};
//blestech
void ili9881_lcm_on(void)
{ 
        push_table(lcm_on_setting, sizeof(lcm_on_setting) / sizeof(struct LCM_setting_table), 1);
    lcm_off_flag = 0;
}

void ili9881_lcm_off(void)
{
        push_table(lcm_off_setting, sizeof(lcm_off_setting) / sizeof(struct LCM_setting_table), 1);
    lcm_off_flag = 1;
}
//blestech end

static void lcm_init(void)
{

  set_lcm_rst_pin(1);
  MDELAY(10);
  set_lcm_rst_pin(0);
  MDELAY(20);
  set_lcm_rst_pin(1);
  MDELAY(120);
  push_table(lcm_initialization_setting, sizeof(lcm_initialization_setting) / sizeof(struct LCM_setting_table), 1);
}

static void lcm_suspend(void)
{ 
  MDELAY(20);
  push_table(lcm_sleep_mode_in_setting, sizeof(lcm_sleep_mode_in_setting) / sizeof(struct LCM_setting_table), 1);
  set_lcm_rst_pin(0);
  MDELAY(20);
}

static unsigned int lcm_compare_id(void);
static void lcm_resume(void)
{
  lcm_init();
  //blestech add
  if(!g_bl229x_enbacklight)		
    ili9881_lcm_off();

  //blestech end
  //lcm_compare_id();
}
static unsigned int lcm_compare_id(void)
{	

  int array[4];
  char buffer[3];
  char id_high=0;
  char id_low=0;
  int id=0;
  //return 1;

  set_lcm_rst_pin(1);
  MDELAY(10);
  set_lcm_rst_pin(0);
  MDELAY(10);
  set_lcm_rst_pin(1);
  MDELAY(20);//Must over 6 ms

  MDELAY(10);

  array[0] = 0x00043902;
  array[1] = 0x068198FF;
  dsi_set_cmdq(array, 2, 1);

  array[0] = 0x00013700;
  dsi_set_cmdq(array, 1, 1);
  read_reg_v2(0xF2, &buffer[0], 1);  //0xOd

  id = buffer[0];

#if defined(BUILD_LK)
  printf("%s, [ili9881d_ivo50_txd_hd]  buffer[0] = [0x%x]  ID = [0x%x]\n",__func__,buffer[0], id);
#else
  printk("%s, [ili9881d_ivo50_txd_hd]  buffer[0] = [0x%x]  ID = [0x%x]\n",__func__,buffer[0], id);
#endif
  return (0x10 == id)?1:0;

}


LCM_DRIVER ili9881p_panda50_bld_hd_lcm_drv =
{
  .name			= "ili9881p_panda50_bld_hd",
  .set_util_funcs = lcm_set_util_funcs,
  .get_params     = lcm_get_params,
  .init           = lcm_init,
  .suspend        = lcm_suspend,
  .resume         = lcm_resume,
  .compare_id     = lcm_compare_id,
  .init_power     = lcm_init_power,
  .resume_power   = lcm_resume_power,
  .suspend_power  = lcm_suspend_power,
};
