'''
VisualOps agent Checksum library Unit Tests
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

import ut

import opsagent
from opsagent.config import Config
from opsagent.checksum import Checksum


def run():
    test_file = "/tmp/visualops/cs_test"
    cs_dir = "/tmp/visualops"
    with open(test_file, 'w') as f:
        f.write("test1")
    cs = Checksum(test_file,"cs_test_mk",cs_dir)
    ret = cs.update(persist=True,tfirst=False)
    print "testing first add ...."
    if ret:
        return -1
    with open(test_file, 'w') as f:
        f.write("test2")
    ret = cs.update(persist=True,tfirst=False)
    print "testing edit file ...."
    if not ret:
        return -1
    cs = Checksum(test_file,"cs_test_mk",cs_dir)
    ret = cs.update(persist=True,tfirst=False)
    print "testing same file ...."
    if ret:
        return -1
    return 0

if __name__ == '__main__':
    exit(ut.ut(run,__file__))
