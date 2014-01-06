'''
Madeira OpsAgent manager

@author: Thibault BRONCHAIN
'''


## IMPORTS
# Native imports
import json
import time
# Library imports
from ws4py.client.threadedclient import WebSocketClient
# Custom import
from objects import codes
from objects import send
from objects import aws
from state.statesworker import StatesWorker
import utils
##

## DEFINES
WAIT_CONNECT=1
WAIT_RESEND=0.1
##

## GLOBALS
# Curent state
status=0
global status
##


## MANAGER OBJECT
# Manages the WebSocket
class Manager(WebSocketClient):
    def __init__(self, config):
        # config
        self.__config = config

        # actions map
        self.__actions = {
            codes.APP_NOT_EXIST : self.__act_retry_hs,
            codes.RECIPE_DATA   : self.__act_recipe,
            codes.WAIT_DATA     : self.__act_wait,
            }

        # init
        self.__error_proc = self.__mount_proc()
        self.__config['init'] = self.__get_id()

        # states worker
        self.__states_worker = None

        # states version
        self.__states_version = None


    ## ACTIONS
    # Renegociate Hangshake if app not started
    def __act_retry_hs(self, data):
        self.__config['init'] = self.__get_id()
        time.sleep(WAIT_CONNECT)
        self.send_json(send.handshake(self.__config['init'], self.__error_proc))

    # Recipe object received
    def __act_recipe(self, data):
        version = data.get("recipe_version")
        if not version:
            raise ManagerInvalidStateFormatException

        states = data.get("states")
        if states:
            if type(states) is not list:
                raise ManagerInvalidStateFormatException
            for state in states:
                if type(state) is not dict:
                    raise ManagerInvalidStateFormatException
                if ("stateid" not in state) or ("module" not in state) or ("parameters" not in state):
                    raise ManagerInvalidStateFormatException

        if (not self.__states_version) or (self.__states_version != version):
            self.__states_version = version
            if self.__states_worker:
                del self.__states_worker
            self.__states_worker = StatesWorker(config=config,manager=self,version=version,states=states)
            self.__states_worker.start()

    # Waited state succeed
    def __act_wait(self, data):
        version = data.get("recipe_version")
        if not version:
            raise ManagerInvalidWaitFormatException
        id = data.get("stateid")
        if not id:
            raise ManagerInvalidWaitFormatException

        if (self.__version) and (self.__version == version):
            self.__states_worker.stateDone(id)
    ##


    ## INIT METHODS
    # Mount/ensure /proc FileSystem
    def __mount_proc(self):
        # TODO
        return None

    # Get instance id and user data from AWS
    def __get_id(self):
        instance_id = aws.instance_id(self.__config)
        (app_id,token) = aws.user_data(self.__config)
        return ({
                'instance_id':instance_id,
                'app_id':app_id,
                'instance_token':token,
                })
    ##


    ## NETWORK METHODS
    # Close socket
    def __close(self, code=1000, reason='', reset=False):
        self.__states_worker.kill()
        if reset:
            status = 0
        self.stream.closing = self.stream.close(code, reason)
        # TODO close()?
        self.terminate()

    # Send data to backend
    def send_json(self, data):
        try:
            json_data = json.dumps(msg)
        except Exception as e:
            self.__close(reset=True,
                         code=codes.C_INVALID_JSON_SEND,
                         reson=codes.M_INVALID_JSON_SEND)
        else:
            # TODO try?
            while not self.send(json_data):
                time.sleep(WAIT_RESEND)
    ##


    ## WEBSOCKET ABSTRACT METHOD IMPLEMENTATION
    # On socket closing
    def closed(self):
        # TODO not sure it can works ...
        self.connect()
        self.run_forever()

    # On socket opening
    def opened(self):
        self.send_json(send.handshake(self.__config['init'], self.__error_proc))

    # On message received
    def received_message(self, raw_data):
        try:
            data = json.loads(raw_data)
        except Exception as e:
            self.__close(reset=True,
                         code=codes.C_INVALID_JSON_RECV,
                         reson=codes.M_INVALID_JSON_RECV)
        else:
            if data.get('code') in self.__actions:
                try:
                    self.__action[data['code']](data)
                except ManagerInvalidStateFormatException:
                    pass
                except ManagerInvalidWaitFormatException:
                    pass
                except Exception as e:
                    pass
    ##
## ENF OF OBJECT
