'''
Madeira OpsAgent State runner object

@author: Thibault BRONCHAIN
'''


# Gevent import
import gevent
# Gevent monkey patch
from gevent import monkey
monkey.patch_all()

# System imports
import subprocess


# State runner object
class StateRunner():
    def __init__(self, config):
        self.__runner = None
        self.__running = False
        self.__config = config

    def haltState(self):
        if self.__running:
            self.__runner.kill()

    def runState(self, state):
        self.__running = True
        utils.log("DEBUG", "Salt start",('runState',None))
        utils.log("DEBUG", "State content '%s'"%(state),('runState',None))


        # TEST
        utils.log("DEBUG", "Starting subprocess",('runState',None))
        self.__runner = subprocess.Popen(["sleep", "200"])
        utils.log("DEBUG", "Subprocess started",('runState',None))
        (outlog,errorlog) = self.__runner.communicate()
        utils.log("DEBUG", "Salt end",('runState',None))



        self.__running = False
        return (outlog,errorlog)
