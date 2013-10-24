# gevent
import gevent
# gevent monkey patch
from gevent import monkey
monkey.patch_all()

# patched imports
import time
import json
import urllib2

# global
global URI,REQ,HEARTBEAT,WK
HEARTBEAT = 2
WK = []
URI = "https://api.madeiracloud.com/session/"
REQ = {
    'jsonrpc':  '2.0',
    'id':       '1728A6D7-7871-405D-BE74-2EA302F139F9',
    'method':   'login',
    'params':   ['thibaultbronchain','Superdry0'],
    # REAL
    'instance_id'    : None,
    'states_version' : None,
    'current_states' : [],
    'wait_states'    : [],
    }


class NetworkConnector():
    def __init__(self):
        self.__buff = []
        self.__uri = URI

    def getResponse(self):
        return (self.__buff.pop() if self.__buff else None)

    def query(self, jsonRes=True):
        send = json.dumps(REQ)
        req = urllib2.Request(self.__uri, send, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.__buff.append((json.load(f) if jsonRes else f.read()))
        f.close()

class Salt():
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
        self.__currentVersion = REQ['states_version']
        print "salt end"
        self.__running = False

class OpsAgent():
    def __init__(self):
        self.__running = True
        self.__network = NetworkConnector()
        self.__salt = Salt()

    def __update(self):
        response = self.__network.getResponse()
        print "res=%s"%response
        #update REQ
        REQ['states_version'] = 2

    def __schedule(self, delay, func, *args, **kw_args):
        e = gevent.spawn_later(0, func, *args, **kw_args)
        WK.append(e)
        WK.append(gevent.spawn_later(delay, self.__schedule, delay, func, *args, **kw_args))
        e.join()
        self.__update()
        if REQ['states_version'] != self.__salt.getVersion() and not self.__salt.isRunning():
            self.__salt.run()

    def __getID(self):
        REQ['instance_id'] = 1

    def stop(self):
        self.__running = False

    def run(self):
        self.__getID()
        # run scheduling
        self.__schedule(HEARTBEAT, self.__network.query)
        while self.__running:
            gevent.joinall(WK)


if __name__ == "__main__":
    a = OpsAgent()
    a.run()
