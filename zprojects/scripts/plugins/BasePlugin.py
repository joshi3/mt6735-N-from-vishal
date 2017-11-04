from vanzo_worker import VanzoWorker

class BasePlugin():
    def __init__(self):
        self.match_item={}
        self.worker=VanzoWorker()
    def match(self,config_map):
        if "VANZO_INNER_PROJECT_NAME" not in config_map:
            return False
        for item in self.match_item.keys():
            if item in config_map:
                #print "find match key:",item
                value=config_map[item].strip().lower()
                if len(value)>0 and value != "no":
                    return True
        return False
    def process(self,config_map):
        return 1,None
