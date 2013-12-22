'''
@author: Thibault BRONCHAIN
'''

# gevent
import gevent
# gevent monkey patch
from gevent import monkey
monkey.patch_all()

# globals
WAITMETA=1

# Custom import
from salt.saltexec import SaltExec
from network.networkconnector import NetworkConnector
from network.objects import *

class Manager():
    def __init__(self, config):
        self.__config = config
        self.__running = True
        self.__network = NetworkConnector()
        self.__salt = SaltExec()
        self.__execWorker = None
        self.__writers = []
        self.__networkWorker = None
        self.__meta = None
        self.__curentState = None
        self.__getAction = {
            "metadata": self.__updateMetadata,
            "state": self.__addState,
            }

    def __interruptExec(self, killExec=False, killWrite=False, ignoreWrite=False):
        utils.log("INFO", "Interrupting current execution ...")
        if self.__execWorker is not None:
            utils.log("DEBUG", "exec worker found",('__interruptExec',self))
            if killExec:
                utils.log("DEBUG", "killing worker",('__interruptExec',self))
                self.__execWorker.kill()
                utils.log("INFO", "State execution aborted")
            else:
                utils.log("INFO", "Waiting for state execution to finish")
                self.__execWorker.join()
                utils.log("INFO", "State execution done")
            self.__execWorker = None
        self.__curentState = None
        if self.__writers:
            if not ignoreWrite and killWrite:
                utils.log("DEBUG", "killing writers",('__interruptExec',self))
                greenlet.killall(self.__writers)
                utils.log("INFO", "writers killed")
            elif not ignoreWrite:
                utils.log("INFO", "Waiting for writers to finish")
                greenlet.joinall(self.__writers)
                utils.log("INFO", "Writers done")
            else:
                utils.log("INFO", "writers ignored during kill")

    def __checkMetaFormat(self, data):
        if not data.get("states_version"):
            utils.log("ERROR", "Server error, disformed data, version missing: '%s'"%(data))
            raise ManagerInvalidMetaFormatException
        utils.log("DEBUG", "Valid metadata received",('__checkMetaFormat',self))

    def __updateMetadata(self, data):
        self.__checkMetaFormat(data)
        version = data["states_version"]
        if self.__meta is None or (self.__meta.get("states_version") != version):
            old = (None if not self.__meta else self.__meta['version'])
            utils.log("INFO", "Curent version is %s, received version is %s, updating..."%(old,version))
            self.__interruptExec(killExec=True,killWrite=True,ignoreWrite=False)
            self.__meta = data
            if self.__meta['current_states']:
                utils.log("DEBUG", "States found",('__updateMetadata',self))
                self.__curentState = self.__meta['current_states'].pop()
                self.__writers.append(gevent.spawn(self.__askState, None, self.__curentState))
        else:
            utils.log("INFO", "States version already up to date")

    def __checkStateFormat(self, data):
        if data.get("state_id") == None:
            utils.log("ERROR", "Invalid state format: no ID found")
            raise ManagerInvalidStateFormatException
        elif data.get("content") == None:
            utils.log("ERROR", "Invalid state format: no content found")
            raise ManagerInvalidStateFormatException
        utils.log("DEBUG", "Valid state received",('__checkStateFormat',self))

    def __addState(self, data):
        self.__checkStateFormat(data)
        id = data["state_id"]
        if id != self.__curentState:
            raise ManagerInvalidStateIdException
        utils.log("INFO", "Starting curent state '%s'"%(self.__curentState))
        self.__execWorker = gevent.spawn(self.__salt.runState,data["content"])

    def __getData(self):
        data = self.__network.recv()
        actionLabel = data.get("type")
        if not actionLabel:
            utils.log("ERROR", "No action received, data: '%s'"%(data))
            return
        try:
            action = self.__getAction.get(actionLabel)
            if not action:
                raise ManagerActionException
            utils.log("INFO", "Executing action '%s'"%(actionLabel))
            action(data.get("content"))
        except ManagerInvalidMetaFormatException:
            utils.log("ERROR", "Invalid metadata format, asking again in %s second"%(WAITMETA))
            self.__writers.append(gevent.spawn_later(WAITMETA,self.__askMeta))
        except ManagerInvalidStateIdException:
            utils.log("ERROR", "Invalid state ID, ignoring")
        except ManagerInvalidStateFormatException:
            utils.log("ERROR", "Invalid state format, regenerating metadata")
            self.__writers.append(gevent.spawn(self.__askMeta))
        except ManagerActionException:
            utils.log("ERROR", "Action not binded, label: '%s'"%(actionLabel))
        except Exception as e:
            utils.log("ERROR", "Uncaught exception '%s'"%(e))
            

    def __askState(self, done, state):
        utils.log("INFO", "Reporting end of state %s, asking for states %s"%(done,state))
        object = copy.deepcopy(network.objects.stateRequest)
        object["content"]["state_req"] = state
        object["content"]["state_end"] = done
        self.__network.send(object)

    def __askMeta(self):
        utils.log("INFO", "Asking for metadatas")
        object = copy.deepcopy(network.objects.metaRequest)
        self.__network.send(object)

#    def __saltRun(self): #TODO
#        done = None
#        while len(self.__meta['current_states']):
#            curent = self.__meta['current_states'].pop()
#            self.__askState(done,curent)
#            
#            self.__salt.runState(states[state])
#            done = curent
#        self.__askState(done,None)

    def __getID(self):
        self.__config['runtime']['instance_id'] = 1

    def stop(self):
        self.__running = False

    def run(self):
        self.__getID()

        # run
        while self.__running:
            self.__networkWorker = gevent.spawn(__getData)
            self.__networkWorker.join()
