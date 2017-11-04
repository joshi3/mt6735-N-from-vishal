#ifndef AUDIO_CUSTOM_H
#define AUDIO_CUSTOM_H

/* define Gain For Normal */
/* Normal volume: TON, SPK, MIC, FMR, SPH, SID, MED */
#define GAIN_NOR_TON_VOL        8     // reserved
#define GAIN_NOR_KEY_VOL       43    // TTY_CTM_Mic
#define GAIN_NOR_MIC_VOL       26    // IN_CALL BuiltIn Mic gain
// GAIN_NOR_FMR_VOL is used as idle mode record volume
#define GAIN_NOR_FMR_VOL        0     // Normal BuiltIn Mic gain
#define GAIN_NOR_SPH_VOL       20     // IN_CALL EARPIECE Volume
#define GAIN_NOR_SID_VOL      100  // IN_CALL EARPICE sidetone
#define GAIN_NOR_MED_VOL       25   // reserved

/* define Gain For Headset */
/* Headset volume: TON, SPK, MIC, FMR, SPH, SID, MED */
#define GAIN_HED_TON_VOL        8     // reserved
#define GAIN_HED_KEY_VOL       24    // reserved
#define GAIN_HED_MIC_VOL       20    // IN_CALL BuiltIn headset gain
#define GAIN_HED_FMR_VOL       24     // reserved
#define GAIN_HED_SPH_VOL       12     // IN_CALL Headset volume
#define GAIN_HED_SID_VOL      100  // IN_CALL Headset sidetone
#define GAIN_HED_MED_VOL       12   // Idle, headset Audio Buf Gain setting

/* define Gain For Handfree */
/* Handfree volume: TON, SPK, MIC, FMR, SPH, SID, MED */
/* GAIN_HND_TON_VOL is used as class-D Amp gain*/
#define GAIN_HND_TON_VOL        8     // use for ringtone volume
#define GAIN_HND_KEY_VOL       24    // reserved
#define GAIN_HND_MIC_VOL       20    // IN_CALL LoudSpeak Mic Gain = BuiltIn Gain
#define GAIN_HND_FMR_VOL       24     // reserved
#define GAIN_HND_SPH_VOL       12     // IN_CALL LoudSpeak
#define GAIN_HND_SID_VOL      100  // IN_CALL LoudSpeak sidetone
#define GAIN_HND_MED_VOL       12   // Idle, loudSPK Audio Buf Gain setting
    /* 0: Input FIR coefficients for 2G/3G Normal mode */
    /* 1: Input FIR coefficients for 2G/3G/VoIP Headset mode */
    /* 2: Input FIR coefficients for 2G/3G Handfree mode */
    /* 3: Input FIR coefficients for 2G/3G/VoIP BT mode */
    /* 4: Input FIR coefficients for VoIP Normal mode */
    /* 5: Input FIR coefficients for VoIP Handfree mode */
#define SPEECH_INPUT_FIR_COEFF \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0
    /* 0: Output FIR coefficients for 2G/3G Normal mode */
    /* 1: Output FIR coefficients for 2G/3G/VoIP Headset mode */
    /* 2: Output FIR coefficients for 2G/3G Handfree mode */
    /* 3: Output FIR coefficients for 2G/3G/VoIP BT mode */
    /* 4: Output FIR coefficients for VoIP Normal mode */
    /* 5: Output FIR coefficients for VoIP Handfree mode */
#define SPEECH_OUTPUT_FIR_COEFF \
      -20,  -183,   391,  -225,    20,\
     -364,   380,   354,    16,   566,\
     -581,   110, -1365,  1356, -2050,\
     1833, -2059,  2799, -2426,  6913,\
    -7092, 32767, 32767, -7092,  6913,\
    -2426,  2799, -2059,  1833, -2050,\
     1356, -1365,   110,  -581,   566,\
       16,   354,   380,  -364,    20,\
     -225,   391,  -183,   -20,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
       73,  -235,   142,  -263,   -63,\
     -129,   206,   179,   264,   892,\
     -767,    60,  -983,   774, -1202,\
      735, -1538,  2201, -1885,  6538,\
    -6932, 32767, 32767, -6932,  6538,\
    -1885,  2201, -1538,   735, -1202,\
      774,  -983,    60,  -767,   892,\
      264,   179,   206,  -129,   -63,\
     -263,   142,  -235,    73,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
                                      \
    32767,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0
#define   DG_DL_Speech    0xe3d
#define   DG_Microphone    0x1400
#define   FM_Record_Vol    6     /* 0 is smallest. each step increase 1dB.
                            Be careful of distortion when increase too much.
                            Generally, it's not suggested to tune this parameter */
/*
* The Bluetooth DAI Hardware COnfiguration Parameter
*/
#define   DEFAULT_BLUETOOTH_SYNC_TYPE    0
#define   DEFAULT_BLUETOOTH_SYNC_LENGTH    1
    /* 0: Input FIR coefficients for 2G/3G Normal mode */
    /* 1: Input FIR coefficients for 2G/3G/VoIP Headset mode */
    /* 2: Input FIR coefficients for 2G/3G Handfree mode */
    /* 3: Input FIR coefficients for 2G/3G/VoIP BT mode */
    /* 4: Input FIR coefficients for VoIP Normal mode */
    /* 5: Input FIR coefficients for VoIP Handfree mode */
#define WB_Speech_Input_FIR_Coeff \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0
    /* 0: Output FIR coefficients for 2G/3G Normal mode */
    /* 1: Output FIR coefficients for 2G/3G/VoIP Headset mode */
    /* 2: Output FIR coefficients for 2G/3G Handfree mode */
    /* 3: Output FIR coefficients for 2G/3G/VoIP BT mode */
    /* 4: Output FIR coefficients for VoIP Normal mode */
    /* 5: Output FIR coefficients for VoIP Handfree mode */
#define WB_Speech_Output_FIR_Coeff \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
                                       \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0,\
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0

/* Input FIR coefficients for 2G/3G HAC mode */
#define DEFAULT_SPEECH_HAC_INPUT_FIR_COEFF \
    32767,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0

/* Output FIR coefficients for 2G/3G HAC mode */
#define DEFAULT_SPEECH_HAC_OUTPUT_FIR_COEFF \
    32767,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0

/* WB Input FIR coefficients for 2G/3G HAC mode */
#define DEFAULT_WB_SPEECH_HAC_INPUT_FIR_COEFF \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0

/* WB Output FIR coefficients for 2G/3G HAC mode */
#define DEFAULT_WB_SPEECH_HAC_OUTPUT_FIR_COEFF \
    32767,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0, \
        0,     0,     0,     0,     0,     0,     0,     0,     0,     0
#endif
