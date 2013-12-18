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

# system imports
import json
import urllib2

class NetworkConnector():
    def __init__(self):
        self.__buff = []
        self.__uri = globals.URI
        self._connect()

    def _connect(self):
        self.ws = WebSocketClient(self.__uri, protocols=['http-only', 'chat'])
        self.ws.connect()

    def send(self, msg):
        self.ws.send(msg)

    def recv(self):
        r = ""
        while True:
            msg = self.ws.receive()
            if msg is not None: r += msg
            else: break
        return r

    def getResponse(self):
        return (self.__buff.pop() if self.__buff else None)

    def query(self, jsonRes=True):
        send = json.dumps(globals.REQ)
        req = urllib2.Request(self.__uri, send, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        self.__buff.append((json.load(f) if jsonRes else f.read()))
        f.close()
