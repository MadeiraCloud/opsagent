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
# Time to wait before retrying handshake
WAIT_CONNECT=1
##

## GLOBALS
# Curent state
STATUS=0
global STATUS
##


## MANAGER OBJECT
# Manages the WebSocket
class Manager(WebSocketClient):
    def __init__(self, config, statesworker):
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
        self.__states_worker = statesworker


    ## ACTIONS
    # Renegociate Hangshake if app not started
    def __act_retry_hs(self, data):
        utils.log("INFO", "Handshake rejected by server.",'__act_retry_hs',self)
        self.__config['init'] = self.__get_id()
        utils.log("INFO", "Retrying in %s seconds."%(WAIT_CONNECT),'__act_retry_hs',self)
        time.sleep(WAIT_CONNECT)
        utils.log("DEBUG", "Reconnecting ...",'__act_retry_hs',self)
        self.send_json(send.handshake(self.__config['init'], self.__error_proc))

    # Recipe object received
    def __act_recipe(self, data):
        utils.log("INFO", "New recipe received.",'__act_recipe',self)
        version = data.get("recipe_version")
        if not version:
            utils.log("ERROR", "Invalid version.",'__act_recipe',self)
            raise ManagerInvalidStateFormatException

        states = data.get("states")
        if states:
            if type(states) is not list:
                utils.log("ERROR", "Invalid states: not list.",'__act_recipe',self)
                raise ManagerInvalidStateFormatException
            for state in states:
                if type(state) is not dict:
                    utils.log("ERROR", "Invalid state: not a dict.",'__act_recipe',self)
                    raise ManagerInvalidStateFormatException
                if ("stateid" not in state) or ("module" not in state) or ("parameter" not in state):
                    utils.log("ERROR", "Invalid state: parameter missing.",'__act_recipe',self)
                    raise ManagerInvalidStateFormatException

        utils.log("DEBUG", "Valid data.",'__act_recipe',self)

        curent_version = self.__states_worker.get_version()
        if (not curent_version) or (curent_version != version):
            utils.log("INFO", "Loading states received ...",'__act_recipe',self)
            self.__states_worker.load(version=version,states=states)
            utils.log("INFO", "States loaded.",'__act_recipe',self)
        else:
            utils.log("WARNING", "Version '%s' is already the current version."%(version),'__act_recipe',self)

    # Waited state succeed
    def __act_wait(self, data):
        utils.log("INFO", "Waited state done received.",'__act_wait',self)
        version = data.get("recipe_version")
        if not version:
            utils.log("ERROR", "Invalid version.",'__act_wait',self)
            raise ManagerInvalidWaitFormatException
        id = data.get("stateid")
        if not id:
            utils.log("ERROR", "Invalid state id.",'__act_wait',self)
            raise ManagerInvalidWaitFormatException

        utils.log("DEBUG", "Valid data.",'__act_wait',self)

        curent_version = self.__states_worker.get_version()
        if (curent_version) and (curent_version == version):
            utils.log("INFO", "Adding state '%s' to done list."%(id),'__act_wait',self)
            self.__states_worker.state_done(id)
            utils.log("DEBUG", "State '%s' added to done list."%(id),'__act_wait',self)
        else:
            utils.log("WARNING", "Wrong version number, curent='%s', received='%s'"%(curent_version,version),'__act_wait',self)
    ##


    ## INIT METHODS
    # Mount/ensure /proc FileSystem
    def __mount_proc(self):
        # TODO
        return None

    # Get instance id and user data from AWS
    def __get_id(self):
        utils.log("INFO", "Fetching instance data from AWS ...",'__get_id',self)
        instance_id = aws.instance_id(self.__config)
        utils.log("DEBUG", "Instance ID: '%s'"%(instance_id),'__get_id',self)
        (app_id,token) = aws.user_data(self.__config)
        utils.log("DEBUG", "App ID: '%s' - Token: '%s'"%(app_id,token),'__get_id',self)
        return ({
                'instance_id':instance_id,
                'app_id':app_id,
                'instance_token':token,
                })
    ##


    ## NETWORK METHODS
    # Close socket
    def __close(self, code=1000, reason='', reset=False):
        utils.log("INFO", "Closing connection ... (code='%s', reason='%s')"%(code,reason),'__close',self)
        if reset:
            utils.log("INFO", "Reset flag set, reseting states execution ...",'__close',self)
            self.__states_worker.kill()
            STATUS = 0
            utils.log("DEBUG", "Reset succeed",'__close',self)
        utils.log("DEBUG", "Setting closing stream",'__close',self)
        self.stream.closing = self.stream.close(code, reason)
        # TODO close()?
        utils.log("DEBUG", "Terminating socket ...",'__close',self)
        self.terminate()
        utils.log("INFO", "Socket terminated, connection closed.",'__close',self)

    # Send data to backend
    def send_json(self, data):
        utils.log("INFO", "Attempt to send data to backend ...",'send_json',self)
        utils.log("DEBUG", "Data: '%s'"%(raw_data),'send_json',self)
        try:
            utils.log("DEBUG", "Converting sending data to json",'send_json',self)
            json_data = json.dumps(msg)
            utils.log("DEBUG", "Sending data successfully converted to json",'send_json',self)
        except Exception as e:
            utils.log("ERROR", "Can't convert received data to json. FATAL",'send_json',self)
            self.__close(reset=True,
                         code=codes.C_INVALID_JSON_SEND,
                         reson=codes.M_INVALID_JSON_SEND)
        else:
            utils.log("INFO", "Sending data ...",'send_json',self)
            try:
                self.send(json_data)
            except Exception as e:
                utils.log("ERROR", "Data failed to send: '%s'."%(e),'send_json',self)
                self.__close(reset=False,
                             code=codes.C_INVALID_WRITE,
                             reason=codes.M_INVALID_WRITE)
            else:
                utils.log("INFO", "Data successfully sent to backend.",'send_json',self)
    ##


    ## WEBSOCKET ABSTRACT METHOD IMPLEMENTATION
    # On socket closing
    def closed(self):
        utils.log("INFO", "Socket closed, reconnection will start in '%s' seconds ..."%(WAIT_RECONNECT),'closed',self)
        self.__states_worker.set_manager(None)
        time.sleep(WAIT_RECONNECT)
        utils.log("DEBUG", "Ready to reconnect",'closed',self)

    # On socket opening
    def opened(self):
        utils.log("INFO", "Socket opened, initiating handshake ...",'opened',self)
        self.send_json(send.handshake(self.__config['init'], self.__error_proc))
        utils.log("DEBUG", "Handshake init message send",'opened',self)

    # On message received
    def received_message(self, raw_data):
        utils.log("INFO", "New message received from backend.",'received_message',self)
        utils.log("DEBUG", "Data: '%s'"%(raw_data),'received_message',self)
        try:
            utils.log("DEBUG", "Converting received json data to dict",'received_message',self)
            data = json.loads(raw_data)
            utils.log("INFO", "Message converted to json.",'received_message',self)
        except Exception as e:
            utils.log("ERROR", "Can't convert received json data to dict. FATAL",'received_message',self)
            self.__close(reset=True,
                         code=codes.C_INVALID_JSON_RECV,
                         reson=codes.M_INVALID_JSON_RECV)
        else:
            if data.get('code') in self.__actions:
                utils.log("DEBUG", "Action found",'received_message',self)
                try:
                    self.__action[data['code']](data)
                except ManagerInvalidStateFormatException:
                    utils.log("ERROR", "Invalid states format",'received_message',self)
                except ManagerInvalidWaitFormatException:
                    utils.log("ERROR", "Invalid wait format",'received_message',self)
                except Exception as e:
                    utils.log("ERROR", "Unknown exception cought '%s'"%(e),'received_message',self)
                else:
                    utils.log("INFO", "Action on code '%s' succeed"%(data['code']),'received_message',self)
            else:
                utils.log("WARNING", "No action binded to received data",'received_message',self)

    ##
## ENF OF OBJECT
