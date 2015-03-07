'''
VisualOps agent Worker Unit Tests
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

import os
import json

import ut

import opsagent
from opsagent.config import Config
from opsagent.state.worker import StateWorker


def run():
    scenarios = os.listdir("scenarios")

    c = Config(os.path.dirname(os.path.realpath("opsagent.conf")))
    c.parse_file()
    config = c.getConfig()
    config['runtime']['config_path'] = os.path.dirname(os.path.realpath("opsagent.conf"))
    sw = StateWorker(config=config)

    for sf in scenarios:
        print "--- Test file: %s"%(os.path.join("scenarios",sf))
        with open(os.path.join("scenarios",sf)) as f:
            content = f.read()
        if not content:
            print "Error reading file: %s"%os.path.join("scenarios",sf)
            return -1
        try:
            states = json.loads(content)
        except Exception as e:
            print "Error loading json, file %s: %s"%(os.path.join("scenarios",sf),e)
            return -1
        if not states:
            print "Error loading json (empty states), file: %s"%os.path.join("scenarios",sf)
            return -1
        try:
            sw.load(version=sf,states=states)
        except Exception as e:
            print "Error loading states, file %s: %s"%(os.path.join("scenarios",sf),e)
            return -1
        try:
            sw.load_modules()
        except Exception as e:
            print "Error loading modules, file %s: %s"%(os.path.join("scenarios",sf),e)
            return -1
        try:
            while (sw.get_status() < len(sw.get_states())):
                (result,comment,out_log) = sw.run_state()
                print "result = '%s'"%result
                print "comment = '%s'"%comment
                print "out_log = '%s'"%out_log
                if not result:
                    print "State #%s failed"%(sw.get_status())
                    return -1
                else:
                    print "State #%s succeed"%(sw.get_status())
        except Exception as e:
            print "Error loading modules, file %s: %s"%(os.path.join("scenarios",sf),e)
            return -1
        print "--- File tested: %s"%(os.path.join("scenarios",sf))
    return 0

if __name__ == '__main__':
    exit(ut.ut(run,__file__))
