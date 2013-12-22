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
        self.__running = False

    def isRunning(self):
        return self.__running

    def runState(self, state):
        self.__running = True
        utils.log("DEBUG", "Salt start",('runState',self))
        utils.log("DEBUG", "State content '%s'"%(state),('runState',self))
        time.sleep(10)
        utils.log("DEBUG", "Salt end",('runState',self))
        self.__running = False
