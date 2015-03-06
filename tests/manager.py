'''
VisualOps agent Manager Unit Tests
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

import ut

import opsagent
from opsagent.config import Config
from opsagent.manager import Manager

def run():
    c = Config("opsagent.conf")
    c.parse_file()
    config = c.getConfig()
    manager = Manager(url=config['userdata']['ws_uri'], config=config, statesworker=None)
    try:
        print "Connecting ..."
        manager.connect()
        print "Connected"
        manager.run_forever()
        print "Disconnected"
    except Exception as e:
        print "Unknown error: %s"%e
        return -1
    return (0 if config["runtime"].get("test") else -1)


if __name__ == '__main__':
    ut.ut(run,__file__)
