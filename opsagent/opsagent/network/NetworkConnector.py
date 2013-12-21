'''
Madeira OpsAgent network communicator

@author: Thibault BRONCHAIN
'''


# Gevent import
import gevent
# Gevent monkey patch
from gevent import monkey
monkey.patch_all()

# System imports
#import json
import time


# Defines
RETRY=5


# TODO: backend communication
# TODO: init, persistency, action on reconnect

# Network communicator
class NetworkConnector():
    def __init__(self, uri, retry=True):
        self._uri = uri
        self._retry = retry
        self._ws = None
        self._connect(self._retry)

    def _connect(self, retry):
        try:
            utils.log("DEBUG", "Connecting to backend '%s'."%(self._uri),('_connect',self))
            self._ws = WebSocketClient(self._uri, protocols=['http-only', 'chat'])
            self._ws.connect()
            utils.log("INFO", "Connected to backend '%s'"%(self._uri))
        except Exception as e:
            utils.log("ERROR", "Can't connect to backend '%s': '%s'"%(self._uri,e))
            if retry:
                utils.log("INFO", "Retrying connection in %s second"%(RETRY))
                time.sleep(RETRY)
                self._connect(retry)
            else:
                raise NetworkConnectionException

    def send(self, msg):
        try:
            utils.log("DEBUG", "Sending data '%s'..."%(msg),('send',self))
            self._ws.send(msg)
            utils.log("DEBUG", "Data sent.",('send',self))
        except Exception as e: #TODO see which exception to catch
            utils.log("ERROR", "Write error: '%s'"%(e))
            self._connect(self._retry)

    def recv(self):
        msg = None
        try:
            utils.log("DEBUG", "Receiving data ...",('recv',self))
            msg = self._ws.receive()
            utils.log("DEBUG", "Data received '%s'."%(msg),('recv',self))
        except Exception as e: #TODO see which exception to catch
            utils.log("ERROR", "Read error: '%s'"%(e))
            self._connect(self._retry)
        return msg

#        r = ""
#        while True:
#            msg = self.ws.receive()
#            if msg is not None: r += msg
#            else: break
#        return r
