#!/usr/bin/env python
import ConfigParser
import sys



if __name__ == '__main__':
    paser = ConfigParser.ConfigParser()
    paser.optionxform=str
    paser.read(sys.argv[1])
    sections = paser.sections()

    config_map={}
    for sec in sections:
        config_map[sec] = dict(paser.items(sec))
    print config_map
