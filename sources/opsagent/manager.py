'''
Madeira OpsAgent manager

@author: Thibault BRONCHAIN
'''

## IMPORTS
# Native imports
import json
import time
import os
import subprocess
import re
# Library imports
from ws4py.client.threadedclient import WebSocketClient
# Custom import
from opsagent.objects import codes
from opsagent.objects import send
from opsagent.objects import aws
from opsagent.state.worker import StateWorker
from opsagent.exception import *
from opsagent import utils
##

## DEFINES
# Time to wait before retrying handshake
WAIT_CONNECT=5
WAIT_RECONNECT=5
##


## MANAGER OBJECT
# Manages the WebSocket
class Manager(WebSocketClient):
    def __init__(self, url, config, statesworker):
        # init WS
        WebSocketClient.__init__(self, url)

        # variables
        self.__config = config
        self.__connected = False
        self.__run = True

        # actions map
        self.__actions = {
            codes.APP_NOT_EXIST : self.__act_retry_hs,
            codes.RECIPE_DATA   : self.__act_recipe,
            codes.WAIT_DATA     : self.__act_wait,
            }

        # init
        self.__error_dir = self.__init_dir()
        self.__error_proc = self.__mount_proc()
        self.__config['init'] = self.__get_id()

        # states worker
        self.__states_worker = statesworker


    ## HELPERS
    # runnign status
    def running(self):
        return self.__run
    ##


    ## ACTIONS
    # Renegociate Hangshake if app not started
    def __act_retry_hs(self, data):
        utils.log("INFO", "Handshake rejected by server.",('__act_retry_hs',self))
        self.__config['init'] = self.__get_id()
        utils.log("INFO", "Retrying in %s seconds."%(WAIT_CONNECT),('__act_retry_hs',self))
        time.sleep(WAIT_CONNECT)
        utils.log("DEBUG", "Reconnecting ...",('__act_retry_hs',self))
        self.send_json(send.handshake(self.__config['init'], [self.__error_proc,self.__error_dir]))

    # Recipe object received
    def __act_recipe(self, data):
        utils.log("INFO", "New recipe received.",('__act_recipe',self))

        # check version
        version = data.get("recipe_version")
        if not version or type(version) is not str:
            utils.log("ERROR", "Invalid version.",('__act_recipe',self))
            raise ManagerInvalidStateFormatException

        # check module
        module = data.get("module")
        if module and type(module) is dict:
            module_repo = module.get("repo")
            if not module_repo or type(module_repo) is not str:
                utils.log("ERROR", "Invalid modules branch.",('__act_recipe',self))
                raise ManagerInvalidStateFormatException
            module_tag = module.get("tag")
            if not module_tag or type(module_tag) is not str:
                utils.log("ERROR", "Invalid modules tag.",('__act_recipe',self))
                raise ManagerInvalidStateFormatException
        else:
            utils.log("ERROR", "No modules details.",('__act_recipe',self))
            raise ManagerInvalidStateFormatException

        # check states
        states = data.get("states")
        if states:
            if type(states) is not list:
                utils.log("ERROR", "Invalid states: not list.",('__act_recipe',self))
                raise ManagerInvalidStateFormatException
            for state in states:
                if type(state) is not dict:
                    utils.log("ERROR", "Invalid state: not a dict.",('__act_recipe',self))
                    raise ManagerInvalidStateFormatException
                if ("id" not in state) or ("module" not in state) or ("parameter" not in state):
                    utils.log("ERROR", "Invalid state: parameter missing.",('__act_recipe',self))
                    raise ManagerInvalidStateFormatException

        utils.log("DEBUG", "Valid data.",('__act_recipe',self))

        # update repo
        clone = False
        if module_repo != self.__config['module']['mod_repo']:
            utils.log("DEBUG", ".",('__act_recipe',self))
            clone = utils.clone_repo(self.__config['module']['root'],self.__config['module']['name'],module_repo)
            self.__config['module']['mod_repo'] = module_repo
            try:
                with open(self.__config['runtime']['config_path'], 'r+') as f:
                    content = re.sub(r'mod_repo=(.+)\n',"mod_repo=%s\n"%(module_repo),f.read())
                    f.seek(0)
                    f.write(content)
            except Exception as e:
                utils.log("WARNING", "Can't save URI repo in config file '%s'."%(),('__act_recipe',self))
        if clone or module_tag != self.__config['module']['mod_tag']:
            utils.checkout_repo(self.__config['module']['root'],self.__config['module']['name'],module_tag)
            self.__config['module']['mod_tag'] = module_tag
            try:
                with open(self.__config['runtime']['config_path'], 'r+') as f:
                    content = re.sub(r'mod_tag=(.+)\n',"mod_tag=%s\n"%(module_tag),f.read())
                    f.seek(0)
                    f.write(content)
            except Exception as e:
                utils.log("WARNING", "Can't save tag version in config file '%s'."%(),('__act_recipe',self))

        # load recipes
        curent_version = self.__states_worker.get_version()
        if (not curent_version) or (curent_version != version):
            utils.log("INFO", "Killing current execution ...",('__act_recipe',self))
            self.__states_worker.kill()
            utils.log("DEBUG", "Execution killed.",('__act_recipe',self))
            utils.log("INFO", "Loading states received ...",('__act_recipe',self))
            self.__states_worker.load(version=version,states=states)
            utils.log("INFO", "States loaded.",('__act_recipe',self))
        else:
            utils.log("WARNING", "Version '%s' is already the current version."%(version),('__act_recipe',self))


    # Waited state succeed
    def __act_wait(self, data):
        utils.log("INFO", "Waited state done received.",('__act_wait',self))
        version = data.get("recipe_version")
        if not version:
            utils.log("ERROR", "Invalid version.",('__act_wait',self))
            raise ManagerInvalidWaitFormatException
        id = data.get("id")
        if not id:
            utils.log("ERROR", "Invalid state id.",('__act_wait',self))
            raise ManagerInvalidWaitFormatException

        utils.log("DEBUG", "Valid data.",('__act_wait',self))

        curent_version = self.__states_worker.get_version()
        if (curent_version) and (curent_version == version):
            utils.log("INFO", "Adding state '%s' to done list."%(id),('__act_wait',self))
            self.__states_worker.state_done(id)
            utils.log("DEBUG", "State '%s' added to done list."%(id),('__act_wait',self))
        else:
            utils.log("WARNING", "Wrong version number, curent='%s', received='%s'"%(curent_version,version),('__act_wait',self))
    ##


    ## INIT METHODS
    # Create directories
    def __init_dir(self):
        dirs = [
            self.__config['global']['watch'],
            self.__config['salt']['srv_root'],
            self.__config['salt']['extension_modules'],
            self.__config['salt']['cachedir'],
            ]
        errors = []
        for dir in dirs:
            try:
                if not os.path.isdir(dir):
                    os.makedirs(dir,0700)
                if not os.access(dir, os.W_OK):
                    raise ManagerInitDirDeniedException
            except ManagerInitDirDeniedException:
                err = "'%s' directory not writable. FATAL."%(dir)
                utils.log("ERROR", err,('__init_dir',self))
                errors.append(err)
            except Exception as e:
                err = "Can't create '%s' directory: '%s'. FATAL."%(dir,e)
                utils.log("ERROR", err,('__init_dir',self))
                errors.append(err)
        return (" ".join(errors) if errors else None)

    # Mount proc FileSystem
    def __mount_proc_try(self, proc, dir=False):
        utils.log("WARNING", "procfs not present, attempting to mount...",('__mount_proc_try',self))
        if not dir:
            try:
                os.makedirs(proc,0755)
            except Exception as e:
                err = "Can't create '%s' directory: '%s'. FATAL."%(proc,e)
                utils.log("ERROR", err,('__mount_proc_try',self))
                return err
        p = subprocess.Popen(['mount','-t','proc','proc',proc])
        if p.wait():
            err = "Can't mount procfs on '%s'. FATAL."%(proc)
            utils.log("ERROR", err,('__mount_proc_try',self))
            return err
        return None

    # Ensure proc FileSystem
    def __mount_proc(self):
        proc = self.__config['global']['proc']
        try:
            if not os.path.isdir(proc):
                return self.__mount_proc_try(proc, dir=False)
            elif not os.path.isfile(os.path.join(proc, 'stat')):
                return self.__mount_proc_try(proc, dir=True)
            self.__config['runtime']['proc'] = True
        except Exception as e:
            err = "Unknown error: can't mount procfs on %s: '%s'. FATAL."%(e,proc)
            utils.log("ERROR", err,('__mount_proc',self))
            return err
        self.__config['runtime']['proc'] = True
        return None

    # Get instance id and user data from AWS
    def __get_id(self):
        utils.log("INFO", "Fetching instance data from AWS ...",('__get_id',self))
        instance_id = aws.instance_id(self.__config, self)
        utils.log("INFO", "Instance ID: '%s'"%(instance_id),('__get_id',self))
        app_id = aws.app_id(self.__config, self)
        utils.log("INFO", "App ID: '%s'"%(app_id),('__get_id',self))
        token = aws.token(self.__config)
        utils.log("DEBUG", "Token: '%s'"%(token),('__get_id',self))
        return ({
                'instance_id':instance_id,
                'app_id':app_id,
                'instance_token':token,
                })
    ##


    ## NETWORK METHODS
    # Stop
    def stop(self):
        utils.log("INFO", "Stopping manager ...",('stop',self))
        self.__close(code=codes.C_STOP,reason=codes.M_STOP)
        self.__run = False

    # Close socket
    def __close(self, code=1000, reason='', reset=False):
        utils.log("INFO", "Closing connection ... (code='%s', reason='%s')"%(code,reason),('__close',self))
        self.__run = False
        if reset:
            utils.log("INFO", "Reset flag set, reseting states execution ...",('__close',self))
            self.__states_worker.kill()
#            self.__states_worker.reset() TODO: remove?
            utils.log("DEBUG", "Reset succeed",('__close',self))
        utils.log("DEBUG", "Closing socket ...",('__close',self))
        self.close(code, reason)
# TODO don't?
#        try:
#            self.terminated = True
#        except Exception as e:
#            utils.log("WARNING", "Can't set terminated attribute: %s."%e,('__close',self))
        utils.log("INFO", "Socket closed, connection terminated.",('__close',self))

    # Send data to backend
    def send_json(self, raw_data):
        utils.log("INFO", "Attempt to send data to backend ...",('send_json',self))
        utils.log("DEBUG", "Data: '%s'"%(raw_data),('send_json',self))
        try:
            utils.log("DEBUG", "Converting sending data to json",('send_json',self))
            json_data = json.dumps(raw_data)
            utils.log("DEBUG", "Sending data successfully converted to json",('send_json',self))
        except Exception as e:
            utils.log("ERROR", "Can't convert received data to json. FATAL",('send_json',self))
            self.__close(reset=True,
                         code=codes.C_INVALID_JSON_SEND,
                         reason=codes.M_INVALID_JSON_SEND)
        else:
            utils.log("INFO", "Sending data ...",('send_json',self))
            try:
                self.send(json_data)
            except Exception as e:
                utils.log("ERROR", "Data failed to send: '%s'."%(e),('send_json',self))
                self.__close(reset=False,
                             code=codes.C_INVALID_WRITE,
                             reason=codes.M_INVALID_WRITE)
            else:
                utils.log("INFO", "Data successfully sent to backend.",('send_json',self))

    # Connection status
    def connected(self):
        return self.__connected
    ##


    ## WEBSOCKET ABSTRACT METHOD IMPLEMENTATION
    # On socket closing
    def closed(self, code, reason):
        utils.log("INFO", "Socket closed: %s, code '%s'"%(reason,code),('closed',self))
        utils.log("INFO", "Reconnection will start in '%s' seconds ..."%(WAIT_RECONNECT),('closed',self))
        self.__connected = False
        self.__run = False
        if self.__states_worker and self.__states_worker.is_alive():
            self.__states_worker.set_manager(None)
        time.sleep(WAIT_RECONNECT)
        utils.log("DEBUG", "Ready to reconnect",('closed',self))

    # On socket opening
    def opened(self):
        utils.log("INFO", "Socket opened, initiating handshake ...",('opened',self))
        self.__connected = True
        self.send_json(send.handshake(self.__config['init'], [self.__error_proc,self.__error_dir]))
        utils.log("DEBUG", "Handshake init message send",('opened',self))

    # On message received
    def received_message(self, raw_data):
        utils.log("INFO", "New message received from backend.",('received_message',self))
        utils.log("DEBUG", "Data: '%s'"%(raw_data),('received_message',self))
        try:
            utils.log("DEBUG", "Converting received json data to dict",('received_message',self))
            data = json.loads(u'%s'%(raw_data))
            utils.log("INFO", "Message converted from json.",('received_message',self))
        except Exception as e:
            utils.log("ERROR", "Can't convert received json data to dict '%s'. FATAL"%(e),('received_message',self))
            self.__close(reset=True,
                         code=codes.C_INVALID_JSON_RECV,
                         reason=codes.M_INVALID_JSON_RECV)
        else:
            if data.get('code') in self.__actions:
                utils.log("DEBUG", "Action found",('received_message',self))
                try:
                    self.__actions[data['code']](data)
                except ManagerInvalidStateFormatException:
                    utils.log("ERROR", "Invalid states format",('received_message',self))
                except ManagerInvalidWaitFormatException:
                    utils.log("ERROR", "Invalid wait format",('received_message',self))
                except ManagerInvalidStatesRepoException:
                    utils.log("ERROR", "Invalid states repository",('received_message',self))
                except Exception as e:
                    utils.log("ERROR", "Unknown exception caught '%s'"%(e),('received_message',self))
                else:
                    utils.log("INFO", "Action on code '%s' succeed"%(data['code']),('received_message',self))
            else:
                utils.log("WARNING", "No action binded to received data",('received_message',self))

    ##
## ENF OF OBJECT
