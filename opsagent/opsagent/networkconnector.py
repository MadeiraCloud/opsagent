'''
Madeira OpsAgent network communicator

@author: Thibault BRONCHAIN
'''


# Gevent import
import gevent
# Gevent monkey patch
from gevent import monkey
monkey.patch_all()

# libraries
import ws4py
from ws4py.client.geventclient import WebSocketClient

# System imports
import json
import time


# Defines
RETRY=5


# Network communicator
class NetworkConnector():
    def __init__(self, uri, retry=True):
        self.__uri = uri
        self.__retry = retry
        self.__ws = None
        self.__connect(self.__retry)

    def __connect(self, retry):
        try:
            utils.log("DEBUG", "Connecting to backend '%s'."%(self._uri),('__connect',self))
            self.__ws = WebSocketClient(self.__uri, protocols=['http-only', 'chat']) #TODO: change protocol
            self.__ws.connect()
            utils.log("INFO", "Connected to backend '%s'"%(self.__uri))
        except Exception as e:
            utils.log("ERROR", "Can't connect to backend '%s': '%s'"%(self.__uri,e))
            if retry:
                utils.log("INFO", "Retrying connection in %s second"%(RETRY))
                gevent.sleep(RETRY)
                self.__connect(retry)
            else:
                raise NetworkConnectionException

    def send(self, msg):
        try:
            utils.log("DEBUG", "Sending data '%s'..."%(msg),('send',self))
            toSend = json.dumps(msg)
            self.__ws.send(toSend)
            utils.log("DEBUG", "Data sent.",('send',self))
        except Exception as e: #TODO see which exception to catch
            utils.log("ERROR", "Write error: '%s'"%(e))
            self.__connect(self._retry)

    def recv(self):
        msg = None
        try:
            utils.log("DEBUG", "Receiving data ...",('recv',self))
            msg = self.__ws.receive()
            utils.log("DEBUG", "Data received '%s'."%(msg),('recv',self))
            msg = json.loads(msg)#TODO load/loads?
        except Exception as e: #TODO see which exception to catch
            utils.log("ERROR", "Read error: '%s'"%(e))
            self.__connect(self.__retry)
        return msg

#        r = ""
#        while True:
#            msg = self.ws.receive()
#            if msg is not None: r += msg
#            else: break
#        return r
