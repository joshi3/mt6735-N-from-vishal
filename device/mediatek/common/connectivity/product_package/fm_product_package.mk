# FM Configuration
# lib
PRODUCT_PACKAGES += libfmjni
PRODUCT_PACKAGES += libfmtxjni
PRODUCT_PACKAGES += radio.fm.mt6735m
PRODUCT_PACKAGES += radio.fm.mt6737m
PRODUCT_PACKAGES += radio.fm.mt6580
PRODUCT_PACKAGES += libfmcust

# cust cfg
PRODUCT_PACKAGES += fm_cust.cfg

# dsp patch
FM_CHIP := $(subst _FM,,$(subst MT,mt,$(strip $(MTK_FM_CHIP))))

ifeq ($(FM_CHIP), mt6625)
  FM_CHIP := mt6627
endif

PRODUCT_PACKAGES += $(FM_CHIP)_fm_v1_patch.bin
PRODUCT_PACKAGES += $(FM_CHIP)_fm_v1_coeff.bin
PRODUCT_PACKAGES += $(FM_CHIP)_fm_v2_patch.bin
PRODUCT_PACKAGES += $(FM_CHIP)_fm_v2_coeff.bin

PRODUCT_PACKAGES += mt6630_fm_v1_patch_tx.bin
PRODUCT_PACKAGES += mt6630_fm_v1_coeff_tx.bin
PRODUCT_PACKAGES += mt6630_fm_v2_patch_tx.bin
PRODUCT_PACKAGES += mt6630_fm_v2_coeff_tx.bin
