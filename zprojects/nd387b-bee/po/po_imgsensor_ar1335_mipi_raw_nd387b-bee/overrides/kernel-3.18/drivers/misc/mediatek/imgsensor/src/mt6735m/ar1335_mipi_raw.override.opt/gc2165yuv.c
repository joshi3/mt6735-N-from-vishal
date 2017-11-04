#include <linux/videodev2.h>
#include <linux/i2c.h>
#include <linux/platform_device.h>
#include <linux/delay.h>
#include <linux/cdev.h>
#include <linux/uaccess.h>
#include <linux/fs.h>
#include <asm/atomic.h>
#include <linux/types.h>

#include "kd_camera_typedef.h"
#include "kd_camera_hw.h"
#include "kd_imgsensor.h"
#include "kd_imgsensor_define.h"
#include "kd_imgsensor_errcode.h"
#include "kd_camera_feature.h"

#include "gc2165yuv.h"

extern char cam2Status;
extern int iReadRegI2C2(u8 *a_pSendData , u16 a_sizeSendData, u8 * a_pRecvData, u16 a_sizeRecvData, u16 i2cId);
extern int iWriteRegI2C2(u8 *a_pSendData , u16 a_sizeSendData, u16 i2cId);

kal_uint16 GC2165_write_cmos_sensor(kal_uint8 addr, kal_uint8 para)
{
	char puSendCmd[2] = {(char)(addr & 0xFF) , (char)(para & 0xFF)};
	iWriteRegI2C2(puSendCmd , 2,GC2165_WRITE_ID_0);
	return 0;
}

kal_uint8 GC2165_read_cmos_sensor(kal_uint8 addr)
{
	kal_uint16 get_byte=0;
	char puSendCmd = { (char)(addr & 0xFF) };
	iReadRegI2C2(&puSendCmd , 1, (u8*)&get_byte,1,GC2165_WRITE_ID_0);
	return get_byte;
}

kal_uint32 GC2165_GetSensorID(void)
{
    int  retry = 3; 
    kal_uint32 sensorID;
    do {
        sensorID=GC2165_read_cmos_sensor(0x04);
		printk("[GC2165]*sensorID = 0x%04x\n", sensorID);
        if (sensorID == 0xd1)
        {
            cam2Status = 1;
            return ERROR_NONE;
        }
        retry--; 
    } while (retry > 0);

    return 0;    
}

void GC2165_Init_Cmds(void) 
{
	GC2165_write_cmos_sensor(0x01, 0x01); //sleep on
	GC2165_write_cmos_sensor(0x01, 0x03); //sleep off
	GC2165_write_cmos_sensor(0x01, 0x01); //sleep on
	// PAGE 20
	GC2165_write_cmos_sensor(0x03, 0x20); // page 20
	GC2165_write_cmos_sensor(0x10, 0x0c); // AE off 60hz

	// PAGE 22
	GC2165_write_cmos_sensor(0x03, 0x22); // page 22
	GC2165_write_cmos_sensor(0x10, 0x69); // AWB off

	GC2165_write_cmos_sensor(0x03, 0x00); //Dummy 750us
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);

	GC2165_write_cmos_sensor(0x08, 0x0f); //131002
	GC2165_write_cmos_sensor(0x09, 0x07); //131002 pad strength 77->07
	GC2165_write_cmos_sensor(0x0a, 0x00); //131002 pad strength 07->00

	//PLL Setting
	GC2165_write_cmos_sensor(0x03, 0x00); 
	GC2165_write_cmos_sensor(0xd0, 0x05); //PLL pre_div 1/6 = 4 Mhz
	GC2165_write_cmos_sensor(0xd1, 0x34); //PLL maim_div 
	GC2165_write_cmos_sensor(0xd2, 0x05); //isp_div[1:0] mipi_4x_div[3:2]  mipi_1x_div[4] pll_bias_opt[7:5]    
	GC2165_write_cmos_sensor(0xd3, 0x20); //isp_clk_inv[0]  mipi_4x_inv[1]  mipi_1x_inv[2]
	GC2165_write_cmos_sensor(0xd0, 0x85);
	GC2165_write_cmos_sensor(0xd0, 0x85);
	GC2165_write_cmos_sensor(0xd0, 0x85);
	GC2165_write_cmos_sensor(0xd0, 0x95);

	GC2165_write_cmos_sensor(0x03, 0x00); //Dummy 750us
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x03, 0x00);

	///// PAGE 20 /////
	GC2165_write_cmos_sensor(0x03, 0x20); //page 20
	GC2165_write_cmos_sensor(0x10, 0x0c); //AE off 50hz

	///// PAGE 22 /////
	GC2165_write_cmos_sensor(0x03, 0x22); //page 22
	GC2165_write_cmos_sensor(0x10, 0x69); //AWB off

	///// Initial Start /////
	///// PAGE 0 Start /////
	GC2165_write_cmos_sensor(0x03, 0x00); //page 0
	GC2165_write_cmos_sensor(0x10, 0x10);
	GC2165_write_cmos_sensor(0x11, 0x93); //Windowing On + 1Frame Skip
	GC2165_write_cmos_sensor(0x12, 0x04); //Rinsing edge 0x04 // Falling edge 0x00
	GC2165_write_cmos_sensor(0x14, 0x05);

	GC2165_write_cmos_sensor(0x20, 0x00); //Row H
	GC2165_write_cmos_sensor(0x21, 0x04); //Row L
	GC2165_write_cmos_sensor(0x22, 0x00); //Col H
	GC2165_write_cmos_sensor(0x23, 0x04); //Col L

	GC2165_write_cmos_sensor(0x24, 0x04); //Window height_H //= 1200
	GC2165_write_cmos_sensor(0x25, 0xb0); //Window height_L //
	GC2165_write_cmos_sensor(0x26, 0x06); //Window width_H  //= 1600
	GC2165_write_cmos_sensor(0x27, 0x40); //Window wight_L

	GC2165_write_cmos_sensor(0x28, 0x04); //Full row start y-flip 
	GC2165_write_cmos_sensor(0x29, 0x01); //Pre1 row start no-flip
	GC2165_write_cmos_sensor(0x2a, 0x02); //Pre1 row start y-flip 

	GC2165_write_cmos_sensor(0x2b, 0x04); //Full wid start x-flip 
	GC2165_write_cmos_sensor(0x2c, 0x04); //Pre2 wid start no-flip
	GC2165_write_cmos_sensor(0x2d, 0x02); //Pre2 wid start x-flip 

	GC2165_write_cmos_sensor(0x40, 0x01); //Hblank 344
	GC2165_write_cmos_sensor(0x41, 0x58); 
	GC2165_write_cmos_sensor(0x42, 0x00); //Vblank 20
	GC2165_write_cmos_sensor(0x43, 0x14); 

	GC2165_write_cmos_sensor(0x50, 0x00); //Test Pattern

	///// BLC /////
	GC2165_write_cmos_sensor(0x80, 0x2e);
	GC2165_write_cmos_sensor(0x81, 0x7e);
	GC2165_write_cmos_sensor(0x82, 0x90);
	GC2165_write_cmos_sensor(0x83, 0x00);
	GC2165_write_cmos_sensor(0x84, 0xcc); //20130604 0x0c->0xcc
	GC2165_write_cmos_sensor(0x85, 0x00);
	GC2165_write_cmos_sensor(0x86, 0x00);
	GC2165_write_cmos_sensor(0x87, 0x0f);
	GC2165_write_cmos_sensor(0x88, 0x34);
	GC2165_write_cmos_sensor(0x8a, 0x0b);
	GC2165_write_cmos_sensor(0x8e, 0x80); //Pga Blc Hold

	GC2165_write_cmos_sensor(0x90, 0x10); //BLC_TIME_TH_ON
	GC2165_write_cmos_sensor(0x91, 0x10); //BLC_TIME_TH_OFF
	GC2165_write_cmos_sensor(0x92, 0x88); //BLC_AG_TH_ON
	GC2165_write_cmos_sensor(0x93, 0x80); //BLC_AG_TH_OFF
	GC2165_write_cmos_sensor(0x96, 0xdc); //BLC Outdoor Th On
	GC2165_write_cmos_sensor(0x97, 0xfe); //BLC Outdoor Th Off
	GC2165_write_cmos_sensor(0x98, 0x38);

	//OutDoor  BLC
	GC2165_write_cmos_sensor(0x99, 0x43); //R,Gr,B,Gb Offset

	//Dark BLC
	GC2165_write_cmos_sensor(0xa0, 0x43); //R,Gr,B,Gb Offset

	//Normal BLC
	GC2165_write_cmos_sensor(0xa8, 0x43); //R,Gr,B,Gb Offset
	///// PAGE 0 END /////

	///// PAGE 2 START /////
	GC2165_write_cmos_sensor(0x03, 0x02);
	GC2165_write_cmos_sensor(0x10, 0x00);
	GC2165_write_cmos_sensor(0x13, 0x00);
	GC2165_write_cmos_sensor(0x14, 0x00);
	GC2165_write_cmos_sensor(0x18, 0xcc);
	GC2165_write_cmos_sensor(0x19, 0x01); // pmos switch on (for cfpn)
	GC2165_write_cmos_sensor(0x1A, 0x39); //20130604 0x09->0xcc
	GC2165_write_cmos_sensor(0x1B, 0x00);
	GC2165_write_cmos_sensor(0x1C, 0x1a); // for ncp
	GC2165_write_cmos_sensor(0x1D, 0x14); // for ncp
	GC2165_write_cmos_sensor(0x1E, 0x30); // for ncp
	GC2165_write_cmos_sensor(0x1F, 0x10);

	GC2165_write_cmos_sensor(0x20, 0x77);
	GC2165_write_cmos_sensor(0x21, 0xde);
	GC2165_write_cmos_sensor(0x22, 0xa7);
	GC2165_write_cmos_sensor(0x23, 0x30);
	GC2165_write_cmos_sensor(0x24, 0x77);
	GC2165_write_cmos_sensor(0x25, 0x10);
	GC2165_write_cmos_sensor(0x26, 0x10);
	GC2165_write_cmos_sensor(0x27, 0x3c);
	GC2165_write_cmos_sensor(0x2b, 0x80);
	GC2165_write_cmos_sensor(0x2c, 0x02);
	GC2165_write_cmos_sensor(0x2d, 0x58);
	GC2165_write_cmos_sensor(0x2e, 0x11);//20130604 0xde->0x11
	GC2165_write_cmos_sensor(0x2f, 0x11);//20130604 0xa7->0x11

	GC2165_write_cmos_sensor(0x30, 0x00);
	GC2165_write_cmos_sensor(0x31, 0x99);
	GC2165_write_cmos_sensor(0x32, 0x00);
	GC2165_write_cmos_sensor(0x33, 0x00);
	GC2165_write_cmos_sensor(0x34, 0x22);
	GC2165_write_cmos_sensor(0x36, 0x75);
	GC2165_write_cmos_sensor(0x38, 0x88);
	GC2165_write_cmos_sensor(0x39, 0x88);
	GC2165_write_cmos_sensor(0x3d, 0x03);
	GC2165_write_cmos_sensor(0x3f, 0x02);

	GC2165_write_cmos_sensor(0x49, 0xc1);//20130604 0x87->0xd1 --> mode Change Issue modify -> 0xc1 
	GC2165_write_cmos_sensor(0x4a, 0x10);

	GC2165_write_cmos_sensor(0x50, 0x21);
	GC2165_write_cmos_sensor(0x53, 0xb1);
	GC2165_write_cmos_sensor(0x54, 0x10);
	GC2165_write_cmos_sensor(0x55, 0x1c); // for ncp
	GC2165_write_cmos_sensor(0x56, 0x11);
	GC2165_write_cmos_sensor(0x58, 0x3a);//20130604 add
	GC2165_write_cmos_sensor(0x59, 0x38);//20130604 add
	GC2165_write_cmos_sensor(0x5d, 0xa2);
	GC2165_write_cmos_sensor(0x5e, 0x5a);

	GC2165_write_cmos_sensor(0x60, 0x87);
	GC2165_write_cmos_sensor(0x61, 0x98);
	GC2165_write_cmos_sensor(0x62, 0x88);
	GC2165_write_cmos_sensor(0x63, 0x96);
	GC2165_write_cmos_sensor(0x64, 0x88);
	GC2165_write_cmos_sensor(0x65, 0x96);
	GC2165_write_cmos_sensor(0x67, 0x3f);
	GC2165_write_cmos_sensor(0x68, 0x3f);
	GC2165_write_cmos_sensor(0x69, 0x3f);

	GC2165_write_cmos_sensor(0x72, 0x89);
	GC2165_write_cmos_sensor(0x73, 0x95);
	GC2165_write_cmos_sensor(0x74, 0x89);
	GC2165_write_cmos_sensor(0x75, 0x95);
	GC2165_write_cmos_sensor(0x7C, 0x84);
	GC2165_write_cmos_sensor(0x7D, 0xaf);

	GC2165_write_cmos_sensor(0x80, 0x01);
	GC2165_write_cmos_sensor(0x81, 0x7a);
	GC2165_write_cmos_sensor(0x82, 0x13);
	GC2165_write_cmos_sensor(0x83, 0x24);
	GC2165_write_cmos_sensor(0x84, 0x78);
	GC2165_write_cmos_sensor(0x85, 0x7c);

	GC2165_write_cmos_sensor(0x92, 0x44);
	GC2165_write_cmos_sensor(0x93, 0x59);
	GC2165_write_cmos_sensor(0x94, 0x78);
	GC2165_write_cmos_sensor(0x95, 0x7c);

	GC2165_write_cmos_sensor(0xA0, 0x02);
	GC2165_write_cmos_sensor(0xA1, 0x74);
	GC2165_write_cmos_sensor(0xA4, 0x74);
	GC2165_write_cmos_sensor(0xA5, 0x02);
	GC2165_write_cmos_sensor(0xA8, 0x85);
	GC2165_write_cmos_sensor(0xA9, 0x8c);
	GC2165_write_cmos_sensor(0xAC, 0x10);
	GC2165_write_cmos_sensor(0xAD, 0x16);

	GC2165_write_cmos_sensor(0xB0, 0x99);
	GC2165_write_cmos_sensor(0xB1, 0xa3);
	GC2165_write_cmos_sensor(0xB4, 0x9b);
	GC2165_write_cmos_sensor(0xB5, 0xa2);
	GC2165_write_cmos_sensor(0xB8, 0x9b);
	GC2165_write_cmos_sensor(0xB9, 0x9f);
	GC2165_write_cmos_sensor(0xBC, 0x9b);
	GC2165_write_cmos_sensor(0xBD, 0x9f);

	GC2165_write_cmos_sensor(0xc4, 0x29);
	GC2165_write_cmos_sensor(0xc5, 0x40);
	GC2165_write_cmos_sensor(0xc6, 0x5c);
	GC2165_write_cmos_sensor(0xc7, 0x72);
	GC2165_write_cmos_sensor(0xc8, 0x2a);
	GC2165_write_cmos_sensor(0xc9, 0x3f);
	GC2165_write_cmos_sensor(0xcc, 0x5d);
	GC2165_write_cmos_sensor(0xcd, 0x71);

	GC2165_write_cmos_sensor(0xd0, 0x10);
	GC2165_write_cmos_sensor(0xd1, 0x14);
	GC2165_write_cmos_sensor(0xd2, 0x20);
	GC2165_write_cmos_sensor(0xd3, 0x00);
	GC2165_write_cmos_sensor(0xd4, 0x10); //DCDC_TIME_TH_ON
	GC2165_write_cmos_sensor(0xd5, 0x10); //DCDC_TIME_TH_OFF 
	GC2165_write_cmos_sensor(0xd6, 0x88); //DCDC_AG_TH_ON
	GC2165_write_cmos_sensor(0xd7, 0x80); //DCDC_AG_TH_OFF
	GC2165_write_cmos_sensor(0xdc, 0x00);
	GC2165_write_cmos_sensor(0xdd, 0xa3);
	GC2165_write_cmos_sensor(0xde, 0x00);
	GC2165_write_cmos_sensor(0xdf, 0x84);

	GC2165_write_cmos_sensor(0xe0, 0xa4);
	GC2165_write_cmos_sensor(0xe1, 0xa4);
	GC2165_write_cmos_sensor(0xe2, 0xa4);
	GC2165_write_cmos_sensor(0xe3, 0xa4);
	GC2165_write_cmos_sensor(0xe4, 0xa4);
	GC2165_write_cmos_sensor(0xe5, 0x01);
	GC2165_write_cmos_sensor(0xe8, 0x00);
	GC2165_write_cmos_sensor(0xe9, 0x00);
	GC2165_write_cmos_sensor(0xea, 0x77);

	GC2165_write_cmos_sensor(0xF0, 0x00);
	GC2165_write_cmos_sensor(0xF1, 0x00);
	GC2165_write_cmos_sensor(0xF2, 0x00);
	///// PAGE 2 END /////

	///// PAGE 10 START /////
	GC2165_write_cmos_sensor(0x03, 0x10); //page 10
	GC2165_write_cmos_sensor(0x10, 0x03); //S2D enable _ YUYV Order º¯°æ
	GC2165_write_cmos_sensor(0x11, 0x03);
	GC2165_write_cmos_sensor(0x12, 0xf0);
	GC2165_write_cmos_sensor(0x13, 0x03);

	GC2165_write_cmos_sensor(0x20, 0x00);
	GC2165_write_cmos_sensor(0x21, 0x40);
	GC2165_write_cmos_sensor(0x22, 0x0f);
	GC2165_write_cmos_sensor(0x24, 0x20);
	GC2165_write_cmos_sensor(0x25, 0x10);
	GC2165_write_cmos_sensor(0x26, 0x01);
	GC2165_write_cmos_sensor(0x27, 0x02);
	GC2165_write_cmos_sensor(0x28, 0x11);

	GC2165_write_cmos_sensor(0x40, 0x00);
	GC2165_write_cmos_sensor(0x41, 0x12); //D-YOffset Th
	GC2165_write_cmos_sensor(0x42, 0x82); //Cb Offset 08
	GC2165_write_cmos_sensor(0x43, 0x02); //Cr Offset
	GC2165_write_cmos_sensor(0x44, 0x80);
	GC2165_write_cmos_sensor(0x45, 0x80);
	GC2165_write_cmos_sensor(0x46, 0xf0);
	GC2165_write_cmos_sensor(0x48, 0x7a);
	GC2165_write_cmos_sensor(0x4a, 0x80);

	GC2165_write_cmos_sensor(0x50, 0x80); //D-YOffset AG

	GC2165_write_cmos_sensor(0x60, 0x4f);
	GC2165_write_cmos_sensor(0x61, 0x79);//82
	GC2165_write_cmos_sensor(0x62, 0x6c);//86
	GC2165_write_cmos_sensor(0x63, 0x68); //Auto-De Color

	GC2165_write_cmos_sensor(0x66, 0x42);
	GC2165_write_cmos_sensor(0x67, 0x22);

	GC2165_write_cmos_sensor(0x6a, 0x55); //White Protection Offset Dark/Indoor
	GC2165_write_cmos_sensor(0x74, 0x05); //White Protection Offset Outdoor
	GC2165_write_cmos_sensor(0x75, 0x76); //Sat over th
	GC2165_write_cmos_sensor(0x76, 0x01); //White Protection Enable
	GC2165_write_cmos_sensor(0x77, 0x82);
	//GC2165_write_cmos_sensor(0x78, 0xff); //Sat over ratio
	///// PAGE 10 END /////

	///// PAGE 11 START /////
	GC2165_write_cmos_sensor(0x03, 0x11); //page 11

	//LPF Auto Control
	GC2165_write_cmos_sensor(0x20, 0x00);
	GC2165_write_cmos_sensor(0x21, 0x00);
	GC2165_write_cmos_sensor(0x26, 0x62); //pga_dark1_min (on)
	GC2165_write_cmos_sensor(0x27, 0x60); //pga_dark1_max (off)
	GC2165_write_cmos_sensor(0x28, 0x0f);
	GC2165_write_cmos_sensor(0x29, 0x10);
	GC2165_write_cmos_sensor(0x2b, 0x30);
	GC2165_write_cmos_sensor(0x2c, 0x32);

	//GBGR 
	GC2165_write_cmos_sensor(0x70, 0x2b);
	GC2165_write_cmos_sensor(0x74, 0x30);
	GC2165_write_cmos_sensor(0x75, 0x18);
	GC2165_write_cmos_sensor(0x76, 0x30);
	GC2165_write_cmos_sensor(0x77, 0xff);
	GC2165_write_cmos_sensor(0x78, 0xa0);
	GC2165_write_cmos_sensor(0x79, 0xff); //Dark GbGr Th
	GC2165_write_cmos_sensor(0x7a, 0x30);
	GC2165_write_cmos_sensor(0x7b, 0x20);
	GC2165_write_cmos_sensor(0x7c, 0xf4); //Dark Dy Th B[7:4]
	GC2165_write_cmos_sensor(0x7d, 0x02);
	GC2165_write_cmos_sensor(0x7e, 0xb0);
	GC2165_write_cmos_sensor(0x7f, 0x10);
	///// PAGE 11 END /////

	///// PAGE 12 START /////
	GC2165_write_cmos_sensor(0x03, 0x12); //page 11

	//YC2D
	GC2165_write_cmos_sensor(0x10, 0x03); //Y DPC Enable
	GC2165_write_cmos_sensor(0x11, 0x08); //
	GC2165_write_cmos_sensor(0x12, 0x10); //0x30 -> 0x10
	GC2165_write_cmos_sensor(0x20, 0x53); //Y_lpf_enable
	GC2165_write_cmos_sensor(0x21, 0x03); //C_lpf_enable_on
	GC2165_write_cmos_sensor(0x22, 0xe6); //YC2D_CrCbY_Dy

	GC2165_write_cmos_sensor(0x23, 0x14); //Outdoor Dy Th
	GC2165_write_cmos_sensor(0x24, 0x1e); //Indoor Dy Th // For reso Limit 0x20
	GC2165_write_cmos_sensor(0x25, 0x20); //Dark Dy Th

	//Outdoor LPF Flat
	GC2165_write_cmos_sensor(0x30, 0xff); //Y Hi Th
	GC2165_write_cmos_sensor(0x31, 0x00); //Y Lo Th
	GC2165_write_cmos_sensor(0x32, 0xf0); //Std Hi Th //Reso Improve Th Low //50
	GC2165_write_cmos_sensor(0x33, 0x00); //Std Lo Th
	GC2165_write_cmos_sensor(0x34, 0xff); //Median ratio

	//Indoor LPF Flat
	GC2165_write_cmos_sensor(0x35, 0xff); //Y Hi Th
	GC2165_write_cmos_sensor(0x36, 0x00); //Y Lo Th
	GC2165_write_cmos_sensor(0x37, 0xff); //Std Hi Th //Reso Improve Th Low //50
	GC2165_write_cmos_sensor(0x38, 0x00); //Std Lo Th
	GC2165_write_cmos_sensor(0x39, 0xff); //Median ratio

	//Dark LPF Flat
	GC2165_write_cmos_sensor(0x3a, 0xff); //Y Hi Th
	GC2165_write_cmos_sensor(0x3b, 0x00); //Y Lo Th
	GC2165_write_cmos_sensor(0x3c, 0xff); //Std Hi Th //Reso Improve Th Low //50
	GC2165_write_cmos_sensor(0x3d, 0x00); //Std Lo Th
	GC2165_write_cmos_sensor(0x3e, 0x00); //Median ratio

	//Outdoor Cindition
	GC2165_write_cmos_sensor(0x46, 0xa0); //Out Lum Hi
	GC2165_write_cmos_sensor(0x47, 0x50); //Out Lum Lo

	//Indoor Cindition
	GC2165_write_cmos_sensor(0x4c, 0xa0); //Indoor Lum Hi
	GC2165_write_cmos_sensor(0x4d, 0x50); //Indoor Lum Lo

	//Dark Cindition
	GC2165_write_cmos_sensor(0x52, 0xa0); //Dark Lum Hi
	GC2165_write_cmos_sensor(0x53, 0x50); //Dark Lum Lo

	//C-Filter
	GC2165_write_cmos_sensor(0x70, 0x10); //Outdoor(2:1) AWM Th Horizontal
	GC2165_write_cmos_sensor(0x71, 0x0a); //Outdoor(2:1) Diff Th Vertical
	GC2165_write_cmos_sensor(0x72, 0x10); //Indoor,Dark1 AWM Th Horizontal
	GC2165_write_cmos_sensor(0x73, 0x0a); //Indoor,Dark1 Diff Th Vertical
	GC2165_write_cmos_sensor(0x74, 0x10); //Dark(2:3) AWM Th Horizontal
	GC2165_write_cmos_sensor(0x75, 0x0f); //Dark(2:3) Diff Th Vertical

	//DPC
	GC2165_write_cmos_sensor(0x90, 0x5d);
	GC2165_write_cmos_sensor(0x91, 0x34);
	GC2165_write_cmos_sensor(0x99, 0x28);
	GC2165_write_cmos_sensor(0x9c, 0x0f);
	GC2165_write_cmos_sensor(0x9d, 0x15);
	GC2165_write_cmos_sensor(0x9e, 0x28);
	GC2165_write_cmos_sensor(0x9f, 0x28);
	GC2165_write_cmos_sensor(0xb0, 0x0e); //Zipper noise Detault change (0x75->0x0e)
	GC2165_write_cmos_sensor(0xb8, 0x44);
	GC2165_write_cmos_sensor(0xb9, 0x15);
	///// PAGE 12 END /////

	///// PAGE 13 START /////
	GC2165_write_cmos_sensor(0x03, 0x13); //page 13
	GC2165_write_cmos_sensor(0x80, 0xc1); //Sharp2D enable _ YUYV Order
	GC2165_write_cmos_sensor(0x81, 0x07); //Sharp2D Clip/Limit
	GC2165_write_cmos_sensor(0x82, 0x73); //Sharp2D Filter
	GC2165_write_cmos_sensor(0x83, 0x00); //Sharp2D Low Clip
	GC2165_write_cmos_sensor(0x85, 0x00);

	GC2165_write_cmos_sensor(0x92, 0x33); //Sharp2D Slop n/p
	GC2165_write_cmos_sensor(0x93, 0x30); //Sharp2D LClip
	GC2165_write_cmos_sensor(0x94, 0x02); //Sharp2D HiClip1 Th
	GC2165_write_cmos_sensor(0x95, 0xf0); //Sharp2D HiClip2 Th
	GC2165_write_cmos_sensor(0x96, 0x1e); //Sharp2D HiClip2 Resolution
	GC2165_write_cmos_sensor(0x97, 0x40); 
	GC2165_write_cmos_sensor(0x98, 0x80);
	GC2165_write_cmos_sensor(0x99, 0x40);

	//Sharp Lclp
	GC2165_write_cmos_sensor(0xa2, 0x02); //Outdoor Lclip_N
	GC2165_write_cmos_sensor(0xa3, 0x02); //Outdoor Lclip_P
	GC2165_write_cmos_sensor(0xa4, 0x04); //Indoor Lclip_N 0x03 For reso Limit 0x0e
	GC2165_write_cmos_sensor(0xa5, 0x05); //Indoor Lclip_P 0x0f For reso Limit 0x0f
	GC2165_write_cmos_sensor(0xa6, 0x30); //Dark Lclip_N
	GC2165_write_cmos_sensor(0xa7, 0x30); //Dark Lclip_P

	//Outdoor Slope
	GC2165_write_cmos_sensor(0xb6, 0x34); //Lum negative Hi
	GC2165_write_cmos_sensor(0xb7, 0x36); //Lum negative middle
	GC2165_write_cmos_sensor(0xb8, 0x34); //Lum negative Low
	GC2165_write_cmos_sensor(0xb9, 0x34); //Lum postive Hi
	GC2165_write_cmos_sensor(0xba, 0x31); //Lum postive middle
	GC2165_write_cmos_sensor(0xbb, 0x31); //Lum postive Low

	//Indoor Slope
	GC2165_write_cmos_sensor(0xbc, 0x30); //Lum negative Hi
	GC2165_write_cmos_sensor(0xbd, 0x32); //Lum negative middle
	GC2165_write_cmos_sensor(0xbe, 0x30); //Lum negative Low
	GC2165_write_cmos_sensor(0xbf, 0x32); //Lum postive Hi
	GC2165_write_cmos_sensor(0xc0, 0x2e); //Lum postive middle
	GC2165_write_cmos_sensor(0xc1, 0x2e); //Lum postive Low

	//Dark Slope
	GC2165_write_cmos_sensor(0xc2, 0x30); //Lum negative Hi
	GC2165_write_cmos_sensor(0xc3, 0x30); //Lum negative middle
	GC2165_write_cmos_sensor(0xc4, 0x30); //Lum negative Low
	GC2165_write_cmos_sensor(0xc5, 0x30); //Lum postive Hi
	GC2165_write_cmos_sensor(0xc6, 0x30); //Lum postive middle
	GC2165_write_cmos_sensor(0xc7, 0x30); //Lum postive Low
	///// PAGE 13 END /////

	///// PAGE 14 START /////
	GC2165_write_cmos_sensor(0x03, 0x14); //page 14
	GC2165_write_cmos_sensor(0x10, 0x0f);

	GC2165_write_cmos_sensor(0x20, 0x80); //X-Center
	GC2165_write_cmos_sensor(0x21, 0x80); //Y-Center

	GC2165_write_cmos_sensor(0x22, 0x76); //LSC R 1b->15 20130125
	GC2165_write_cmos_sensor(0x23, 0x7a); //LSC G
	GC2165_write_cmos_sensor(0x24, 0x78); //LSC B

	GC2165_write_cmos_sensor(0x25, 0xf0); //LSC Off
	GC2165_write_cmos_sensor(0x26, 0xf0); //LSC On
	///// PAGE 14 END /////

	/////// PAGE 15 START ///////
	GC2165_write_cmos_sensor(0x03, 0x15); //15 Page
	GC2165_write_cmos_sensor(0x10, 0x21);
	GC2165_write_cmos_sensor(0x14, 0x42); //CMCOFSGH
	GC2165_write_cmos_sensor(0x15, 0x32); //CMCOFSGM
	GC2165_write_cmos_sensor(0x16, 0x22); //CMCOFSGL
	GC2165_write_cmos_sensor(0x17, 0x2f);

	GC2165_write_cmos_sensor(0x30, 0xdc);
	GC2165_write_cmos_sensor(0x31, 0x5d);
	GC2165_write_cmos_sensor(0x32, 0x01);
	GC2165_write_cmos_sensor(0x33, 0x39);
	GC2165_write_cmos_sensor(0x34, 0xd9);
	GC2165_write_cmos_sensor(0x35, 0x20);
	GC2165_write_cmos_sensor(0x36, 0x17);
	GC2165_write_cmos_sensor(0x37, 0x46);
	GC2165_write_cmos_sensor(0x38, 0xdd);

	//CMC OFS
	GC2165_write_cmos_sensor(0x40, 0x90);
	GC2165_write_cmos_sensor(0x41, 0x10);
	GC2165_write_cmos_sensor(0x42, 0x00);
	GC2165_write_cmos_sensor(0x43, 0x0f);
	GC2165_write_cmos_sensor(0x44, 0x0b);
	GC2165_write_cmos_sensor(0x45, 0x9a);
	GC2165_write_cmos_sensor(0x46, 0x9f);
	GC2165_write_cmos_sensor(0x47, 0x09);
	GC2165_write_cmos_sensor(0x48, 0x16);
	//CMC POFS
	GC2165_write_cmos_sensor(0x50, 0x00);
	GC2165_write_cmos_sensor(0x51, 0x98);
	GC2165_write_cmos_sensor(0x52, 0x18);
	GC2165_write_cmos_sensor(0x53, 0x04);
	GC2165_write_cmos_sensor(0x54, 0x00);
	GC2165_write_cmos_sensor(0x55, 0x84);
	GC2165_write_cmos_sensor(0x56, 0x02);
	GC2165_write_cmos_sensor(0x57, 0x00);
	GC2165_write_cmos_sensor(0x58, 0x82);
	///// PAGE 15 END /////

	///// PAGE 16 START /////
	GC2165_write_cmos_sensor(0x03, 0x16); //page 16 Gamma
	GC2165_write_cmos_sensor(0x10, 0x31);
	GC2165_write_cmos_sensor(0x18, 0x80);// Double_AG 5e->37
	GC2165_write_cmos_sensor(0x19, 0x7c);// Double_AG 5e->36
	GC2165_write_cmos_sensor(0x1a, 0x0e);
	GC2165_write_cmos_sensor(0x1b, 0x01);
	GC2165_write_cmos_sensor(0x1c, 0xdc);
	GC2165_write_cmos_sensor(0x1d, 0xfe);

	//Indoor
	GC2165_write_cmos_sensor(0x30, 0x01);
	GC2165_write_cmos_sensor(0x31, 0x08);
	GC2165_write_cmos_sensor(0x32, 0x11);
	GC2165_write_cmos_sensor(0x33, 0x22);
	GC2165_write_cmos_sensor(0x34, 0x52);
	GC2165_write_cmos_sensor(0x35, 0x74);
	GC2165_write_cmos_sensor(0x36, 0x8e);
	GC2165_write_cmos_sensor(0x37, 0xa4);
	GC2165_write_cmos_sensor(0x38, 0xb6);
	GC2165_write_cmos_sensor(0x39, 0xc5);
	GC2165_write_cmos_sensor(0x3a, 0xd1);
	GC2165_write_cmos_sensor(0x3b, 0xd9);
	GC2165_write_cmos_sensor(0x3c, 0xe2);
	GC2165_write_cmos_sensor(0x3d, 0xe7);
	GC2165_write_cmos_sensor(0x3e, 0xed);
	GC2165_write_cmos_sensor(0x3f, 0xf1);
	GC2165_write_cmos_sensor(0x40, 0xf8);
	GC2165_write_cmos_sensor(0x41, 0xfb);
	GC2165_write_cmos_sensor(0x42, 0xff);

	//Outdoor
	GC2165_write_cmos_sensor(0x50, 0x01);
	GC2165_write_cmos_sensor(0x51, 0x08);
	GC2165_write_cmos_sensor(0x52, 0x11);
	GC2165_write_cmos_sensor(0x53, 0x22);
	GC2165_write_cmos_sensor(0x54, 0x52);
	GC2165_write_cmos_sensor(0x55, 0x74);
	GC2165_write_cmos_sensor(0x56, 0x8e);
	GC2165_write_cmos_sensor(0x57, 0xa4);
	GC2165_write_cmos_sensor(0x58, 0xb6);
	GC2165_write_cmos_sensor(0x59, 0xc5);
	GC2165_write_cmos_sensor(0x5a, 0xd1);
	GC2165_write_cmos_sensor(0x5b, 0xd9);
	GC2165_write_cmos_sensor(0x5c, 0xe2);
	GC2165_write_cmos_sensor(0x5d, 0xe7);
	GC2165_write_cmos_sensor(0x5e, 0xed);
	GC2165_write_cmos_sensor(0x5f, 0xf1);
	GC2165_write_cmos_sensor(0x60, 0xf8);
	GC2165_write_cmos_sensor(0x61, 0xfb);
	GC2165_write_cmos_sensor(0x62, 0xff);

	//Dark
	GC2165_write_cmos_sensor(0x70, 0x01);
	GC2165_write_cmos_sensor(0x71, 0x08);
	GC2165_write_cmos_sensor(0x72, 0x11);
	GC2165_write_cmos_sensor(0x73, 0x22);
	GC2165_write_cmos_sensor(0x74, 0x52);
	GC2165_write_cmos_sensor(0x75, 0x74);
	GC2165_write_cmos_sensor(0x76, 0x8e);
	GC2165_write_cmos_sensor(0x77, 0xa4);
	GC2165_write_cmos_sensor(0x78, 0xb6);
	GC2165_write_cmos_sensor(0x79, 0xc5);
	GC2165_write_cmos_sensor(0x7a, 0xd1);
	GC2165_write_cmos_sensor(0x7b, 0xd9);
	GC2165_write_cmos_sensor(0x7c, 0xe2);
	GC2165_write_cmos_sensor(0x7d, 0xe7);
	GC2165_write_cmos_sensor(0x7e, 0xed);
	GC2165_write_cmos_sensor(0x7f, 0xf1);
	GC2165_write_cmos_sensor(0x80, 0xf8);
	GC2165_write_cmos_sensor(0x81, 0xfb);
	GC2165_write_cmos_sensor(0x82, 0xff);
	///// PAGE 16 END /////

	///// PAGE 17 START /////
	GC2165_write_cmos_sensor(0x03, 0x17); //page 17
	GC2165_write_cmos_sensor(0xc1, 0x00);
	GC2165_write_cmos_sensor(0xc4, 0x42); //FLK200 
	GC2165_write_cmos_sensor(0xc5, 0x37); //FLK240 
	GC2165_write_cmos_sensor(0xc6, 0x02);
	GC2165_write_cmos_sensor(0xc7, 0x20);
	///// PAGE 17 END /////

	///// PAGE 18 START /////
	GC2165_write_cmos_sensor(0x03, 0x18); //page 18
	GC2165_write_cmos_sensor(0x10, 0x00);	//Scale Off
	GC2165_write_cmos_sensor(0x11, 0x00);
	GC2165_write_cmos_sensor(0x12, 0x58);
	GC2165_write_cmos_sensor(0x13, 0x01);
	GC2165_write_cmos_sensor(0x14, 0x00); //Sawtooth
	GC2165_write_cmos_sensor(0x15, 0x00);
	GC2165_write_cmos_sensor(0x16, 0x00);
	GC2165_write_cmos_sensor(0x17, 0x00);
	GC2165_write_cmos_sensor(0x18, 0x00);
	GC2165_write_cmos_sensor(0x19, 0x00);
	GC2165_write_cmos_sensor(0x1a, 0x00);
	GC2165_write_cmos_sensor(0x1b, 0x00);
	GC2165_write_cmos_sensor(0x1c, 0x00);
	GC2165_write_cmos_sensor(0x1d, 0x00);
	GC2165_write_cmos_sensor(0x1e, 0x00);
	GC2165_write_cmos_sensor(0x1f, 0x00);
	GC2165_write_cmos_sensor(0x20, 0x05);	//zoom wid
	GC2165_write_cmos_sensor(0x21, 0x00);
	GC2165_write_cmos_sensor(0x22, 0x01);	//zoom hgt
	GC2165_write_cmos_sensor(0x23, 0xe0);
	GC2165_write_cmos_sensor(0x24, 0x00);	//zoom start x
	GC2165_write_cmos_sensor(0x25, 0x00);
	GC2165_write_cmos_sensor(0x26, 0x00);	//zoom start y
	GC2165_write_cmos_sensor(0x27, 0x00);
	GC2165_write_cmos_sensor(0x28, 0x05);	//zoom end x
	GC2165_write_cmos_sensor(0x29, 0x00);
	GC2165_write_cmos_sensor(0x2a, 0x01);	//zoom end y
	GC2165_write_cmos_sensor(0x2b, 0xe0);
	GC2165_write_cmos_sensor(0x2c, 0x0a);	//zoom step vert
	GC2165_write_cmos_sensor(0x2d, 0x00);
	GC2165_write_cmos_sensor(0x2e, 0x0a);	//zoom step horz
	GC2165_write_cmos_sensor(0x2f, 0x00);
	GC2165_write_cmos_sensor(0x30, 0x44);	//zoom fifo

	///// PAGE 18 END /////

	GC2165_write_cmos_sensor(0x03, 0x19); //Page 0x19
	GC2165_write_cmos_sensor(0x10, 0x7f); //mcmc_ctl1
	GC2165_write_cmos_sensor(0x11, 0x7f); //mcmc_ctl2
	GC2165_write_cmos_sensor(0x12, 0x1e); //mcmc_delta1
	GC2165_write_cmos_sensor(0x13, 0x48); //mcmc_center1
	GC2165_write_cmos_sensor(0x14, 0x1e); //mcmc_delta2
	GC2165_write_cmos_sensor(0x15, 0x80); //mcmc_center2
	GC2165_write_cmos_sensor(0x16, 0x1e); //mcmc_delta3
	GC2165_write_cmos_sensor(0x17, 0xb8); //mcmc_center3
	GC2165_write_cmos_sensor(0x18, 0x1e); //mcmc_delta4
	GC2165_write_cmos_sensor(0x19, 0xf0); //mcmc_center4
	GC2165_write_cmos_sensor(0x1a, 0x9e); //mcmc_delta5
	GC2165_write_cmos_sensor(0x1b, 0x22); //mcmc_center5
	GC2165_write_cmos_sensor(0x1c, 0x9e); //mcmc_delta6
	GC2165_write_cmos_sensor(0x1d, 0x5e); //mcmc_center6
	GC2165_write_cmos_sensor(0x1e, 0x40); //mcmc_sat_gain1
	GC2165_write_cmos_sensor(0x1f, 0x40); //mcmc_sat_gain2
	GC2165_write_cmos_sensor(0x20, 0x5a); //mcmc_sat_gain3
	GC2165_write_cmos_sensor(0x21, 0x5a); //mcmc_sat_gain4
	GC2165_write_cmos_sensor(0x22, 0x40); //mcmc_sat_gain5
	GC2165_write_cmos_sensor(0x23, 0x37); //mcmc_sat_gain6
	GC2165_write_cmos_sensor(0x24, 0x00); //mcmc_hue_angle1
	GC2165_write_cmos_sensor(0x25, 0x86); //mcmc_hue_angle2
	GC2165_write_cmos_sensor(0x26, 0x00); //mcmc_hue_angle3
	GC2165_write_cmos_sensor(0x27, 0x92); //mcmc_hue_angle4
	GC2165_write_cmos_sensor(0x28, 0x00); //mcmc_hue_angle5
	GC2165_write_cmos_sensor(0x29, 0x8a); //mcmc_hue_angle6

	GC2165_write_cmos_sensor(0x53, 0x10); //mcmc_ctl3
	GC2165_write_cmos_sensor(0x6c, 0xff); //mcmc_lum_ctl1
	GC2165_write_cmos_sensor(0x6d, 0x3f); //mcmc_lum_ctl2
	GC2165_write_cmos_sensor(0x6e, 0x00); //mcmc_lum_ctl3
	GC2165_write_cmos_sensor(0x6f, 0x00); //mcmc_lum_ctl4
	GC2165_write_cmos_sensor(0x70, 0x00); //mcmc_lum_ctl5
	GC2165_write_cmos_sensor(0x71, 0x3f); //rg1_lum_gain_wgt_th1
	GC2165_write_cmos_sensor(0x72, 0x3f); //rg1_lum_gain_wgt_th2
	GC2165_write_cmos_sensor(0x73, 0x3f); //rg1_lum_gain_wgt_th3
	GC2165_write_cmos_sensor(0x74, 0x3f); //rg1_lum_gain_wgt_th4
	GC2165_write_cmos_sensor(0x75, 0x30); //rg1_lum_sp1
	GC2165_write_cmos_sensor(0x76, 0x50); //rg1_lum_sp2
	GC2165_write_cmos_sensor(0x77, 0x80); //rg1_lum_sp3
	GC2165_write_cmos_sensor(0x78, 0xb0); //rg1_lum_sp4
	GC2165_write_cmos_sensor(0x79, 0x3f); //rg2_gain_wgt_th1
	GC2165_write_cmos_sensor(0x7a, 0x3f); //rg2_gain_wgt_th2
	GC2165_write_cmos_sensor(0x7b, 0x3f); //rg2_gain_wgt_th3
	GC2165_write_cmos_sensor(0x7c, 0x3f); //rg2_gain_wgt_th4
	GC2165_write_cmos_sensor(0x7d, 0x28); //rg2_lum_sp1
	GC2165_write_cmos_sensor(0x7e, 0x50); //rg2_lum_sp2
	GC2165_write_cmos_sensor(0x7f, 0x80); //rg2_lum_sp3
	GC2165_write_cmos_sensor(0x80, 0xb0); //rg2_lum_sp4
	GC2165_write_cmos_sensor(0x81, 0x28); //rg3_gain_wgt_th1
	GC2165_write_cmos_sensor(0x82, 0x3f); //rg3_gain_wgt_th2
	GC2165_write_cmos_sensor(0x83, 0x3f); //rg3_gain_wgt_th3
	GC2165_write_cmos_sensor(0x84, 0x3f); //rg3_gain_wgt_th4
	GC2165_write_cmos_sensor(0x85, 0x28); //rg3_lum_sp1
	GC2165_write_cmos_sensor(0x86, 0x50); //rg3_lum_sp2
	GC2165_write_cmos_sensor(0x87, 0x80); //rg3_lum_sp3
	GC2165_write_cmos_sensor(0x88, 0xb0); //rg3_lum_sp4
	GC2165_write_cmos_sensor(0x89, 0x1a); //rg4_gain_wgt_th1
	GC2165_write_cmos_sensor(0x8a, 0x28); //rg4_gain_wgt_th2
	GC2165_write_cmos_sensor(0x8b, 0x3f); //rg4_gain_wgt_th3
	GC2165_write_cmos_sensor(0x8c, 0x3f); //rg4_gain_wgt_th4
	GC2165_write_cmos_sensor(0x8d, 0x10); //rg4_lum_sp1
	GC2165_write_cmos_sensor(0x8e, 0x30); //rg4_lum_sp2
	GC2165_write_cmos_sensor(0x8f, 0x60); //rg4_lum_sp3
	GC2165_write_cmos_sensor(0x90, 0x90); //rg4_lum_sp4
	GC2165_write_cmos_sensor(0x91, 0x1a); //rg5_gain_wgt_th1
	GC2165_write_cmos_sensor(0x92, 0x28); //rg5_gain_wgt_th2
	GC2165_write_cmos_sensor(0x93, 0x3f); //rg5_gain_wgt_th3
	GC2165_write_cmos_sensor(0x94, 0x3f); //rg5_gain_wgt_th4
	GC2165_write_cmos_sensor(0x95, 0x28); //rg5_lum_sp1
	GC2165_write_cmos_sensor(0x96, 0x50); //rg5_lum_sp2
	GC2165_write_cmos_sensor(0x97, 0x80); //rg5_lum_sp3
	GC2165_write_cmos_sensor(0x98, 0xb0); //rg5_lum_sp4
	GC2165_write_cmos_sensor(0x99, 0x1a); //rg6_gain_wgt_th1
	GC2165_write_cmos_sensor(0x9a, 0x28); //rg6_gain_wgt_th2
	GC2165_write_cmos_sensor(0x9b, 0x3f); //rg6_gain_wgt_th3
	GC2165_write_cmos_sensor(0x9c, 0x3f); //rg6_gain_wgt_th4
	GC2165_write_cmos_sensor(0x9d, 0x28); //rg6_lum_sp1
	GC2165_write_cmos_sensor(0x9e, 0x50); //rg6_lum_sp2
	GC2165_write_cmos_sensor(0x9f, 0x80); //rg6_lum_sp3
	GC2165_write_cmos_sensor(0xa0, 0xb0); //rg6_lum_sp4

	GC2165_write_cmos_sensor(0xe5, 0x80); //add 20120709 Bit[7] On MCMC --> YC2D_LPF

	/////// PAGE 20 START ///////
	GC2165_write_cmos_sensor(0x03, 0x20);
	GC2165_write_cmos_sensor(0x10, 0x1c);
	GC2165_write_cmos_sensor(0x11, 0x0c);//14
	GC2165_write_cmos_sensor(0x18, 0x30);
	GC2165_write_cmos_sensor(0x20, 0x65); //8x8 Ae weight 0~7 Outdoor / Weight Outdoor On B[5]
	GC2165_write_cmos_sensor(0x21, 0x30);
	GC2165_write_cmos_sensor(0x22, 0x10);
	GC2165_write_cmos_sensor(0x23, 0x00);

	GC2165_write_cmos_sensor(0x28, 0xf7);
	GC2165_write_cmos_sensor(0x29, 0x0d);
	GC2165_write_cmos_sensor(0x2a, 0xff);
	GC2165_write_cmos_sensor(0x2b, 0x04); //Adaptive Off,1/100 Flicker

	GC2165_write_cmos_sensor(0x2c, 0x83); //AE After CI
	GC2165_write_cmos_sensor(0x2d, 0xe3); 
	GC2165_write_cmos_sensor(0x2e, 0x13);
	GC2165_write_cmos_sensor(0x2f, 0x0b);

	GC2165_write_cmos_sensor(0x30, 0x78);
	GC2165_write_cmos_sensor(0x31, 0xd7);
	GC2165_write_cmos_sensor(0x32, 0x10);
	GC2165_write_cmos_sensor(0x33, 0x2e);
	GC2165_write_cmos_sensor(0x34, 0x20);
	GC2165_write_cmos_sensor(0x35, 0xd4);
	GC2165_write_cmos_sensor(0x36, 0xfe);
	GC2165_write_cmos_sensor(0x37, 0x32);
	GC2165_write_cmos_sensor(0x38, 0x04);
	GC2165_write_cmos_sensor(0x39, 0x22);
	GC2165_write_cmos_sensor(0x3a, 0xde);
	GC2165_write_cmos_sensor(0x3b, 0x22);
	GC2165_write_cmos_sensor(0x3c, 0xde);
	GC2165_write_cmos_sensor(0x3d, 0xe1);

	GC2165_write_cmos_sensor(0x3e, 0xc9); //Option of changing Exp max
	GC2165_write_cmos_sensor(0x41, 0x23); //Option of changing Exp max

	GC2165_write_cmos_sensor(0x50, 0x45);
	GC2165_write_cmos_sensor(0x51, 0x88);

	GC2165_write_cmos_sensor(0x56, 0x03); // for tracking
	GC2165_write_cmos_sensor(0x57, 0xf7); // for tracking
	GC2165_write_cmos_sensor(0x58, 0x14); // for tracking
	GC2165_write_cmos_sensor(0x59, 0x88); // for tracking

	GC2165_write_cmos_sensor(0x5a, 0x04);
	GC2165_write_cmos_sensor(0x5b, 0x04);

	GC2165_write_cmos_sensor(0x5e, 0xc7);
	GC2165_write_cmos_sensor(0x5f, 0x95);

	GC2165_write_cmos_sensor(0x62, 0x10);
	GC2165_write_cmos_sensor(0x63, 0xc0);
	GC2165_write_cmos_sensor(0x64, 0x10);
	GC2165_write_cmos_sensor(0x65, 0x8a);
	GC2165_write_cmos_sensor(0x66, 0x58);
	GC2165_write_cmos_sensor(0x67, 0x58);

	GC2165_write_cmos_sensor(0x70, 0x50); //6c
	GC2165_write_cmos_sensor(0x71, 0x80); //81(+4),89(-4)

	GC2165_write_cmos_sensor(0x76, 0x21);
	GC2165_write_cmos_sensor(0x77, 0x71);
	GC2165_write_cmos_sensor(0x78, 0x22); //24
	GC2165_write_cmos_sensor(0x79, 0x22); // Y Target 70 => 25, 72 => 26 //
	GC2165_write_cmos_sensor(0x7a, 0x23); //23
	GC2165_write_cmos_sensor(0x7b, 0x22); //22
	GC2165_write_cmos_sensor(0x7d, 0x23);

	GC2165_write_cmos_sensor(0x03, 0x20); //Page 20

	GC2165_write_cmos_sensor(0x83, 0x09); //EXP Normal 10.00 fps 
	GC2165_write_cmos_sensor(0x84, 0xe8); 
	GC2165_write_cmos_sensor(0x85, 0xe0); 
	GC2165_write_cmos_sensor(0x86, 0x01); //EXPMin 13211.38 fps
	GC2165_write_cmos_sensor(0x87, 0xec); 
	GC2165_write_cmos_sensor(0x88, 0x10); //EXP Max 60hz 6.00 fps 
	GC2165_write_cmos_sensor(0x89, 0x84); 
	GC2165_write_cmos_sensor(0x8a, 0x20); 
	GC2165_write_cmos_sensor(0xa5, 0x0f); //EXP Max 50hz 6.25 fps 
	GC2165_write_cmos_sensor(0xa6, 0xdb); 
	GC2165_write_cmos_sensor(0xa7, 0x00); 
	GC2165_write_cmos_sensor(0x8B, 0xfd); //EXP100 
	GC2165_write_cmos_sensor(0x8C, 0xb0); 
	GC2165_write_cmos_sensor(0x8D, 0xd3); //EXP120 
	GC2165_write_cmos_sensor(0x8E, 0x68); 
	GC2165_write_cmos_sensor(0x9c, 0x20); //EXP Limit 777.14 fps 
	GC2165_write_cmos_sensor(0x9d, 0xac); 
	GC2165_write_cmos_sensor(0x9e, 0x01); //EXP Unit 
	GC2165_write_cmos_sensor(0x9f, 0xec); 
	GC2165_write_cmos_sensor(0xa3, 0x00); //Outdoor Int 
	GC2165_write_cmos_sensor(0xa4, 0xd3); 

	GC2165_write_cmos_sensor(0xb0, 0x50);
	GC2165_write_cmos_sensor(0xb1, 0x14);
	GC2165_write_cmos_sensor(0xb2, 0x80);
	GC2165_write_cmos_sensor(0xb3, 0x15);
	GC2165_write_cmos_sensor(0xb4, 0x16);
	GC2165_write_cmos_sensor(0xb5, 0x3c);
	GC2165_write_cmos_sensor(0xb6, 0x29);
	GC2165_write_cmos_sensor(0xb7, 0x23);
	GC2165_write_cmos_sensor(0xb8, 0x20);
	GC2165_write_cmos_sensor(0xb9, 0x1e);
	GC2165_write_cmos_sensor(0xba, 0x1c);
	GC2165_write_cmos_sensor(0xbb, 0x1b);
	GC2165_write_cmos_sensor(0xbc, 0x1b);
	GC2165_write_cmos_sensor(0xbd, 0x1a);

	GC2165_write_cmos_sensor(0xc0, 0x10);
	GC2165_write_cmos_sensor(0xc1, 0x40);
	GC2165_write_cmos_sensor(0xc2, 0x40);
	GC2165_write_cmos_sensor(0xc3, 0x40);
	GC2165_write_cmos_sensor(0xc4, 0x06);

	GC2165_write_cmos_sensor(0xc6, 0x80); //Exp max 1frame target AG

	GC2165_write_cmos_sensor(0xc8, 0x80);
	GC2165_write_cmos_sensor(0xc9, 0x80);
	///// PAGE 20 END /////

	///// PAGE 21 START /////
	GC2165_write_cmos_sensor(0x03, 0x21); //page 21

	GC2165_write_cmos_sensor(0x03, 0x21);
	GC2165_write_cmos_sensor(0x20, 0x11);
	GC2165_write_cmos_sensor(0x21, 0x11);
	GC2165_write_cmos_sensor(0x22, 0x11);
	GC2165_write_cmos_sensor(0x23, 0x11);
	GC2165_write_cmos_sensor(0x24, 0x11);
	GC2165_write_cmos_sensor(0x25, 0x11);
	GC2165_write_cmos_sensor(0x26, 0x11);
	GC2165_write_cmos_sensor(0x27, 0x11);
	GC2165_write_cmos_sensor(0x28, 0x12);
	GC2165_write_cmos_sensor(0x29, 0x22);
	GC2165_write_cmos_sensor(0x2a, 0x22);
	GC2165_write_cmos_sensor(0x2b, 0x21);
	GC2165_write_cmos_sensor(0x2c, 0x12);
	GC2165_write_cmos_sensor(0x2d, 0x33);
	GC2165_write_cmos_sensor(0x2e, 0x32);
	GC2165_write_cmos_sensor(0x2f, 0x21);
	GC2165_write_cmos_sensor(0x30, 0x12);
	GC2165_write_cmos_sensor(0x31, 0x33);
	GC2165_write_cmos_sensor(0x32, 0x32);
	GC2165_write_cmos_sensor(0x33, 0x21);
	GC2165_write_cmos_sensor(0x34, 0x12);
	GC2165_write_cmos_sensor(0x35, 0x22);
	GC2165_write_cmos_sensor(0x36, 0x22);
	GC2165_write_cmos_sensor(0x37, 0x21);
	GC2165_write_cmos_sensor(0x38, 0x11);
	GC2165_write_cmos_sensor(0x39, 0x11);
	GC2165_write_cmos_sensor(0x3a, 0x11);
	GC2165_write_cmos_sensor(0x3b, 0x11);
	GC2165_write_cmos_sensor(0x3c, 0x11);
	GC2165_write_cmos_sensor(0x3d, 0x11);
	GC2165_write_cmos_sensor(0x3e, 0x11);
	GC2165_write_cmos_sensor(0x3f, 0x11);
	GC2165_write_cmos_sensor(0x40, 0x11);
	GC2165_write_cmos_sensor(0x41, 0x11);
	GC2165_write_cmos_sensor(0x42, 0x11);
	GC2165_write_cmos_sensor(0x43, 0x11);
	GC2165_write_cmos_sensor(0x44, 0x11);
	GC2165_write_cmos_sensor(0x45, 0x11);
	GC2165_write_cmos_sensor(0x46, 0x11);
	GC2165_write_cmos_sensor(0x47, 0x11);
	GC2165_write_cmos_sensor(0x48, 0x11);
	GC2165_write_cmos_sensor(0x49, 0x33);
	GC2165_write_cmos_sensor(0x4a, 0x33);
	GC2165_write_cmos_sensor(0x4b, 0x11);
	GC2165_write_cmos_sensor(0x4c, 0x11);
	GC2165_write_cmos_sensor(0x4d, 0x33);
	GC2165_write_cmos_sensor(0x4e, 0x33);
	GC2165_write_cmos_sensor(0x4f, 0x11);
	GC2165_write_cmos_sensor(0x50, 0x11);
	GC2165_write_cmos_sensor(0x51, 0x33);
	GC2165_write_cmos_sensor(0x52, 0x33);
	GC2165_write_cmos_sensor(0x53, 0x11);
	GC2165_write_cmos_sensor(0x54, 0x11);
	GC2165_write_cmos_sensor(0x55, 0x33);
	GC2165_write_cmos_sensor(0x56, 0x33);
	GC2165_write_cmos_sensor(0x57, 0x11);
	GC2165_write_cmos_sensor(0x58, 0x11);
	GC2165_write_cmos_sensor(0x59, 0x11);
	GC2165_write_cmos_sensor(0x5a, 0x11);
	GC2165_write_cmos_sensor(0x5b, 0x11);
	GC2165_write_cmos_sensor(0x5c, 0x11);
	GC2165_write_cmos_sensor(0x5d, 0x11);
	GC2165_write_cmos_sensor(0x5e, 0x11);
	GC2165_write_cmos_sensor(0x5f, 0x11);


	///// PAGE 22 START /////
	GC2165_write_cmos_sensor(0x03, 0x22); //page 22
	GC2165_write_cmos_sensor(0x10, 0xfd);
	GC2165_write_cmos_sensor(0x11, 0x2e);
	GC2165_write_cmos_sensor(0x19, 0x03);//0x03->0x00
	GC2165_write_cmos_sensor(0x20, 0x30); //For AWB Speed
	GC2165_write_cmos_sensor(0x21, 0x80);
	GC2165_write_cmos_sensor(0x22, 0x00);
	GC2165_write_cmos_sensor(0x23, 0x00);
	GC2165_write_cmos_sensor(0x24, 0x01);
	GC2165_write_cmos_sensor(0x25, 0x4f); //2013-09-13 AWB Hunting

	GC2165_write_cmos_sensor(0x30, 0x80);
	GC2165_write_cmos_sensor(0x31, 0x80);
	GC2165_write_cmos_sensor(0x38, 0x11);
	GC2165_write_cmos_sensor(0x39, 0x34);
	GC2165_write_cmos_sensor(0x40, 0xe4); //Stb Yth
	GC2165_write_cmos_sensor(0x41, 0x33); //Stb cdiff
	GC2165_write_cmos_sensor(0x42, 0x22); //Stb csum
	GC2165_write_cmos_sensor(0x43, 0xf3); //Unstb Yth
	GC2165_write_cmos_sensor(0x44, 0x44); //Unstb cdiff55
	GC2165_write_cmos_sensor(0x45, 0x33); //Unstb csum
	GC2165_write_cmos_sensor(0x46, 0x00);
	GC2165_write_cmos_sensor(0x47, 0x09); //2013-09-13 AWB Hunting
	GC2165_write_cmos_sensor(0x48, 0x00); //2013-09-13 AWB Hunting
	GC2165_write_cmos_sensor(0x49, 0x0a);

	GC2165_write_cmos_sensor(0x60, 0x04);
	GC2165_write_cmos_sensor(0x61, 0xc4);
	GC2165_write_cmos_sensor(0x62, 0x04);
	GC2165_write_cmos_sensor(0x63, 0x92);
	GC2165_write_cmos_sensor(0x66, 0x04);
	GC2165_write_cmos_sensor(0x67, 0xc4);
	GC2165_write_cmos_sensor(0x68, 0x04);
	GC2165_write_cmos_sensor(0x69, 0x92);

	GC2165_write_cmos_sensor(0x80, 0x36);
	GC2165_write_cmos_sensor(0x81, 0x20);
	GC2165_write_cmos_sensor(0x82, 0x30);

	GC2165_write_cmos_sensor(0x83, 0x5a);
	GC2165_write_cmos_sensor(0x84, 0x21);
	GC2165_write_cmos_sensor(0x85, 0x44);
	GC2165_write_cmos_sensor(0x86, 0x1d);

	GC2165_write_cmos_sensor(0x87, 0x3e); //3b->46 awb_r_gain_max middle
	GC2165_write_cmos_sensor(0x88, 0x1e); //30->3b awb_r_gain_min middle
	GC2165_write_cmos_sensor(0x89, 0x28); //29->2c awb_b_gain_max middle
	GC2165_write_cmos_sensor(0x8a, 0x12); //18->1b awb_b_gain_min middle

	GC2165_write_cmos_sensor(0x8b, 0x3a); //3c->45 awb_r_gain_max outdoor
	GC2165_write_cmos_sensor(0x8c, 0x1f); //32->3b awb_r_gain_min outdoor
	GC2165_write_cmos_sensor(0x8d, 0x28); //2a->2c awb_b_gain_max outdoor
	GC2165_write_cmos_sensor(0x8e, 0x13); //1b->1b awb_b_gain_min outdoor

	GC2165_write_cmos_sensor(0x8f, 0x4f); // 56);// 4d); //4e awb_slope_th0
	GC2165_write_cmos_sensor(0x90, 0x44); // 4f);// 46); //4d awb_slope_th1
	GC2165_write_cmos_sensor(0x91, 0x3f); // 49);// 40); //4c awb_slope_th2
	GC2165_write_cmos_sensor(0x92, 0x3a); // 43);// 3a); //4a awb_slope_th3
	GC2165_write_cmos_sensor(0x93, 0x2d); // 38);// 2f); //46 awb_slope_th4
	GC2165_write_cmos_sensor(0x94, 0x21); // 2a);// 21); // awb_slope_th5
	GC2165_write_cmos_sensor(0x95, 0x1a); // 22);// 19); // awb_slope_th6
	GC2165_write_cmos_sensor(0x96, 0x19); // 1f);// 16); // awb_slope_th7
	GC2165_write_cmos_sensor(0x97, 0x18); // 1c);// 13); // awb_slope_th8
	GC2165_write_cmos_sensor(0x98, 0x17); // 1b);// 12); // awb_slope_th9
	GC2165_write_cmos_sensor(0x99, 0x16); // 1a);// 11); // awb_slope_th10
	GC2165_write_cmos_sensor(0x9a, 0x16); // 19);// 10); // awb_slope_th11

	GC2165_write_cmos_sensor(0x9b, 0x88);
	GC2165_write_cmos_sensor(0x9c, 0x99);
	GC2165_write_cmos_sensor(0x9d, 0x48);
	GC2165_write_cmos_sensor(0x9e, 0x38);
	GC2165_write_cmos_sensor(0x9f, 0x30);

	GC2165_write_cmos_sensor(0xa0, 0x70);
	GC2165_write_cmos_sensor(0xa1, 0x54);
	GC2165_write_cmos_sensor(0xa2, 0x6f);
	GC2165_write_cmos_sensor(0xa3, 0xff);

	GC2165_write_cmos_sensor(0xa4, 0x14); //1536fps
	GC2165_write_cmos_sensor(0xa5, 0x2c); //698fps
	GC2165_write_cmos_sensor(0xa6, 0xcf); //148fps

	GC2165_write_cmos_sensor(0xad, 0x2e);
	GC2165_write_cmos_sensor(0xae, 0x2a);

	GC2165_write_cmos_sensor(0xaf, 0x28); //Low temp Rgain
	GC2165_write_cmos_sensor(0xb0, 0x26); //Low temp Rgain

	GC2165_write_cmos_sensor(0xb1, 0x08);
	GC2165_write_cmos_sensor(0xb4, 0xbf); //For Tracking AWB Weight
	GC2165_write_cmos_sensor(0xb8, 0x02); //low(0+,1-)High Cb , (0+,1-)Low Cr
	GC2165_write_cmos_sensor(0xb9, 0x00);//high
	/////// PAGE 22 END ///////

	//// MIPI Setting /////
	GC2165_write_cmos_sensor(0x03, 0x48);
	GC2165_write_cmos_sensor(0x39, 0x4f); //lvds_bias_ctl    [2:0]mipi_tx_bias   [4:3]mipi_vlp_sel   [6:5]mipi_vcm_sel
	GC2165_write_cmos_sensor(0x10, 0x1c); //lvds_ctl_1       [5]mipi_pad_disable [4]lvds_en [0]serial_data_len 
	GC2165_write_cmos_sensor(0x11, 0x10); //lvds_ctl_2       [4]mipi continous mode setting
	//GC2165_write_cmos_sensor(0x14, 0x00} //ser_out_ctl_1  [2:0]serial_sout_a_phase   [6:4]serial_cout_a_phase

	GC2165_write_cmos_sensor(0x16, 0x00); //lvds_inout_ctl1  [0]vs_packet_pos_sel [1]data_neg_sel [4]first_vsync_end_opt
	GC2165_write_cmos_sensor(0x18, 0x80); //lvds_inout_ctl3
	GC2165_write_cmos_sensor(0x19, 0x00); //lvds_inout_ctl4
	GC2165_write_cmos_sensor(0x1a, 0xf0); //lvds_time_ctl
	GC2165_write_cmos_sensor(0x24, 0x1e); //long_packet_id

	//====== MIPI Timing Setting =========
	GC2165_write_cmos_sensor(0x36, 0x01); //clk_tlpx_time_dp
	GC2165_write_cmos_sensor(0x37, 0x05); //clk_tlpx_time_dn
	GC2165_write_cmos_sensor(0x34, 0x04); //clk_prepare_time
	GC2165_write_cmos_sensor(0x32, 0x15); //clk_zero_time
	GC2165_write_cmos_sensor(0x35, 0x04); //clk_trail_time
	GC2165_write_cmos_sensor(0x33, 0x0d); //clk_post_time

	GC2165_write_cmos_sensor(0x1c, 0x01); //tlps_time_l_dp
	GC2165_write_cmos_sensor(0x1d, 0x0b); //tlps_time_l_dn
	GC2165_write_cmos_sensor(0x1e, 0x06); //hs_zero_time
	GC2165_write_cmos_sensor(0x1f, 0x09); //hs_trail_time

	//long_packet word count 
	GC2165_write_cmos_sensor(0x30, 0x06);
	GC2165_write_cmos_sensor(0x31, 0x40); //long_packet word count

	/////// PAGE 20 ///////
	GC2165_write_cmos_sensor(0x03, 0x20);
	GC2165_write_cmos_sensor(0x10, 0x8c); //AE On 60hz

	/////// PAGE 22 ///////
	GC2165_write_cmos_sensor(0x03, 0x22);
	GC2165_write_cmos_sensor(0x10, 0xe9); //AWB On

	GC2165_write_cmos_sensor(0x03, 0x00);
	GC2165_write_cmos_sensor(0x01, 0x00);
}

kal_uint32 GC2165_Read_Shutter1(void)
{
	kal_uint8 temp_reg0, temp_reg1, temp_reg2;
	kal_uint32 shutter;

	GC2165_write_cmos_sensor(0x03, 0x20); 
	temp_reg0 = GC2165_read_cmos_sensor(0x80); 
	temp_reg1 = GC2165_read_cmos_sensor(0x81);
	temp_reg2 = GC2165_read_cmos_sensor(0x82); 
	shutter = (temp_reg0 << 16) | (temp_reg1 << 8) | (temp_reg2 & 0xFF);

	return shutter;
}   
kal_uint32 GC2165_Read_Shutter2(void)
{
    kal_uint8 temp_reg1;
    kal_uint16 shutter;
    GC2165_write_cmos_sensor(0x03, 0x20); //page 20
    shutter = GC2165_read_cmos_sensor(0xd3);
    if((shutter<30)&&(shutter>0))
        shutter=5;
    printk("hi258 shutter = %d\n",shutter);

    return shutter;
}
void GC2165_Initial_Cmds(void)
{
	kal_uint16 i,cnt;
	GC2165_Init_Cmds();
}
UINT32 GC2165Open(void)
{
    GC2165_GetSensorID();
    GC2165_Initial_Cmds();
    return ERROR_NONE;
}	
