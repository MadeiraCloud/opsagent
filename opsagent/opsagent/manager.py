'''
@author: Thibault BRONCHAIN
'''

# gevent
import gevent
# gevent monkey patch
from gevent import monkey
monkey.patch_all()

# libraries
import ws4py
from ws4py.client.geventclient import WebSocketClient

# globals
import globals

# internal import
from SaltExec import SaltExec
from NetworkConnector import NetworkConnector

class OpsAgent():
    def __init__(self):
        self.__running = True
        self.__network = NetworkConnector()
        self.__salt = SaltExec()
        self.__saltWorker = None
        self.__networkWorker = None

    def __update(self, states):
        print states
        #update REQ
        globals.REQ['states_version'] = 2

    def __interruptSalt(self):
        if self.__saltWorker is not None:
            self.__saltWorker.kill()
            self.__saltWorker = None
            return True
        return False

    def __getStates(self):
        while True:
            states = self.network.recv()
            self.__update(states)
            if globals.REQ['states_version'] != self.__salt.getVersion():
                if self.__salt.isRunning():
                    self.__network.send("exec interrupt")
                    self.__interruptSalt()
                self.__saltWorker = gevent.spawn(self.__saltRun)

    def __saltRun(self):
        states = {'1':"foo",'2':"bar"}
        while len(globals.REQ['current_states']):
            state = globals.REQ['current_states'].pop()
            self.__salt.runState(states[state])
            #?self.__network.send(globals.REQ)
            self.__network.send("state done")
        self.__salt.setVersion()

    def __getID(self):
        globals.REQ['instance_id'] = 1

    def stop(self):
        self.__running = False

    def run(self):
        self.__getID()
        # run scheduling
        while self.__running:
            self.__networkWorker = gevent.spawn(__getStates)
            self.__networkWorker.join()
