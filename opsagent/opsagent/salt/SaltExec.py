'''
Madeira OpsAgent Salt interface

@author: Thibault BRONCHAIN
'''


# Gevent import
import gevent
# Gevent monkey patch
from gevent import monkey
monkey.patch_all()

# Custom imports
import ..globals

#TMP
import time


# Salt interface
class SaltExec():
    def __init__(self):
        self.__currentVersion = None
        self.__running = False

    def getVersion(self):
        return self.__currentVersion

    def setVersion(self):
        self.__currentVersion = globals.REQ['states_version']

    def isRunning(self):
        return self.__running

    def runState(self, state):
        self.__running = True
        print "salt start"
        print "%s"%(state)
        time.sleep(10)
        print "salt end"
        self.__running = False
