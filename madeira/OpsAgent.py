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

# internal import
from SaltExec import SaltExec
from NetworkConnector import NetworkConnector

class OpsAgent():
    def __init__(self):
        self.__running = True
        self.__network = NetworkConnector()
        self.__salt = SaltExec()
        self.__workers = []

    def __update(self):
        response = self.__network.getResponse()
        print "res=%s"%response
        #update REQ
        globals.REQ['states_version'] = 2

    def __schedule(self, delay, func, *args, **kw_args):
        e = gevent.spawn_later(0, func, *args, **kw_args)
        self.__workers.append(e)
        self.__workers.append(gevent.spawn_later(delay, self.__schedule, delay, func, *args, **kw_args))
        e.join()
        self.__update()
        if globals.REQ['states_version'] != self.__salt.getVersion() and not self.__salt.isRunning():
            self.__salt.run()

    def __getID(self):
        globals.REQ['instance_id'] = 1

    def stop(self):
        self.__running = False

    def run(self):
        self.__getID()
        # run scheduling
        self.__schedule(globals.HEARTBEAT, self.__network.query)
        while self.__running:
            gevent.joinall(self.__workers)
