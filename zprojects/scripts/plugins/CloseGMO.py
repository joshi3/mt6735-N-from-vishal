import math
from BasePlugin import BasePlugin
class CloseGMO(BasePlugin):
    def __init__(self):
        BasePlugin.__init__(self)
        self.match_item={"VANZO_CUSTOM_MEMORY_BY_NAME_VALUE":None}

    def process(self,config_map):
        if "VANZO_INNER_PM_PROJECT_NAME" not in config_map:
            return -1,"VANZO_INNER_PM_PROJECT_NAME must be exist"


        config_string = []
        if int(config_map["VANZO_CUSTOM_MEMORY_BY_NAME_VALUE"].split(".")[-1].split("p")[1].split("d")[0]) < 8:
            print "opening mtk gmo ram / rom op"
            config_string = ["MTK_GMO_RAM_OPTIMIZE=yes", "MTK_GMO_ROM_OPTIMIZE=yes", "CONFIG_MTK_GMO_RAM_OPTIMIZE=y", "CONFIG_MTK_GMO_ROM_OPTIMIZE=y",]
        else:
            print "closing mtk gmo ram / rom op"
            config_string = ["MTK_GMO_RAM_OPTIMIZE=no", "MTK_GMO_ROM_OPTIMIZE=no", "CONFIG_MTK_GMO_RAM_OPTIMIZE=n", "CONFIG_MTK_GMO_ROM_OPTIMIZE=n",]

        return 1, config_string

