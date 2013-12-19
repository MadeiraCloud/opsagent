'''
@author: Thibault BRONCHAIN
'''

# gevent
import gevent
# gevent monkey patch
from gevent import monkey
monkey.patch_all()

# globals
import globals

#TMP
import time

class SaltExec():
    def __init__(self):
        self.__currentVersion = None
        self.__running = False

    def getVersion(self):
        return self.__currentVersion

    def isRunning(self):
        return self.__running

    def run(self):
        self.__running = True
        print "salt start"
        time.sleep(10)
        self.__currentVersion = globals.REQ['states_version']
        print "salt end"
        self.__running = False
