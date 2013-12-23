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
import json
import time

# Libraries imports
import ws4py
from ws4py.client.geventclient import WebSocketClient

# Custom imports
import opsagent.utils
import opsagent.exception


# Defines
RETRY=5


# Network communicator object
class NetworkConnector():
    def __init__(self, config, retry=True):
        self.__uri = config['network']['ws_uri']
        self.__retry = retry
        self.__ws = None
        self.__writers = []
        self.__connect(self.__retry)

    # DONE
    # TODO add log
    # Add a new writer in queue (executes once previous is done)
    def __addWriter(self, func, *args, **kw_args):
        if self.__writers[:1] != self.__writers[-1:]:
            self.__writers[0].wait()
            self.__writers.pop(0)
        func(*args, **kw_args)

    # DONE
    # Connect to WS server
    def __connect(self, retry):
        try:
            utils.log("DEBUG", "Connecting to backend '%s'."%(self._uri),('__connect',self))
            self.__ws = WebSocketClient(self.__uri)
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

    # TMP DONE
    # TODO debug log
    # Write on socket
    def __sendGreenlet(self, toSend):
        try:
            self.__ws.send(toSend)
        except Exception as e: #TODO see which exception to catch
            utils.log("ERROR", "Write error: '%s'"%(e))
            self.__connect(self.__retry)

    # DONE
    # Create a writer object
    def send(self, msg):
        utils.log("DEBUG", "Sending data '%s'..."%(msg),('send',self))
        toSend = json.dumps(msg)
        self.__writers.append(gevent.spawn(self.addWriter, self.__sendGreenlet, toSend))
        utils.log("DEBUG", "Data sent.",('send',self))

    # DONE
    # Receive some data
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
