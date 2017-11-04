#ifndef __SENSOR_H
#define __SENSOR_H


#define GC2165_SENSOR_ID         (0xd1)

#define GC2165_WRITE_ID_0		(0x50)
#define GC2165_READ_ID_0			(0x51)

#define GC2165_WRITE_ID_1		(0x50)
#define GC2165_READ_ID_1			(0x51)


UINT32 GC2165Open(void);
kal_uint32 GC2165_Read_Shutter1(void);
kal_uint32 GC2165_Read_Shutter2(void);

#endif 
