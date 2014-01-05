'''
Madeira OpsAgent manager

@author: Thibault BRONCHAIN
'''


# Gevent import
import gevent
# Gevent monkey patch
from gevent import monkey
monkey.patch_all()

# Custom import
from network.networkconnector import NetworkConnector
from state.staterunner import StateRunner
from actions.selector import selector
import actions.askers


# globals
WAITMETA=1


# Manager object
class Manager():
    def __init__(self, config):
        # variables
        self.__config = config
        self.__running = True
        self.__socket = NetworkConnector(config)
        self.__state = StateRunner(config)

        # greenlets
        self.__stateWorker = None

        # remote objects
        self.__meta = None
        self.__curentState = None


    # DONE
    # Return network socket, always valid
    def getSocket(self):
        return self.__socket

    # TMP DONE
    # TODO check leak + add debug log
    # Get/Set metadata
    def getMeta(self, copyVar=False):
        return (self.__meta if not copyVar else copy.deepcopy(self.__meta))
    def setMeta(self, data, specific=None):
        if specific:
            for s in specific:
                self.__meta[s] = data[s]
        else:
            self.__meta = data

    # TMP DONE
    # TODO check leak + add debug log
    # Get/Set/Update curent running state
    def getCurentState(self, copyVar=False):
        return (self.__curentState if not copyVar else copy.deepcopy(self.__curentState))
    def setCurentState(self, state):
        self.__curentState = state
    def updateCurentState(self):
        self.__curentState = (self.__meta['current_states'].pop()
                              if self.__meta
                              else None)
        return self.__curentState

    # Set worker manager id
    def setWorker(self, id):
        self.__stateWorker = id
    # Kills state worker
    def interruptWorker(self):
        self.__state.haltState() #TODO?
    # Launch state worker
    def startWorker(self, id, data):
        (out,err) = self.__state.runState(id, data)
        ## TODO: report out and err to server (send)
        # Ask next state
        actions.askers.askState(self.__socket, id, self.updateCurentState)


#    # TODO
#    # Add a new writer in queue (executes once previous is done)
#    def __interruptExec(self, killExec=False, killWrite=False, ignoreWrite=False):
#        utils.log("INFO", "Interrupting current execution ...")
#        if self.__stateWorker is not None:
#            utils.log("DEBUG", "state worker found",('__interruptExec',self))
#            if killExec:
#                utils.log("DEBUG", "killing worker",('__interruptExec',self))
#                self.__stateWorker.kill()
#                utils.log("INFO", "State execution aborted")
#            else:
#                utils.log("INFO", "Waiting for state execution to finish")
#                self.__stateWorker.join()
#                utils.log("INFO", "State execution done")
#            utils.log("INFO", "Waiting for state manager to terminate ...")
#            self.__stateManager.join()
#            self.__stateManager = None
#        self.__curentState = None
#        if self.__writers:
#            if not ignoreWrite and killWrite:
#                utils.log("DEBUG", "killing writers",('__interruptExec',self))
#                greenlet.killall(self.__writers)
#                utils.log("INFO", "writers killed")
#            elif not ignoreWrite:
#                utils.log("INFO", "Waiting for writers to finish")
#                greenlet.joinall(self.__writers)
#                utils.log("INFO", "Writers done")
#            else:
#                utils.log("INFO", "writers ignored during kill")

    # DONE
    # Bind action on data receipt
    def __getData(self):
        data = self.__socket.recv()
        if not data:
            utils.log("ERROR", "No data received.")
            return
        actionLabel = data.get("type")
        if not actionLabel:
            utils.log("ERROR", "No action received, data: '%s'"%(data))
            return
        try:
            action = selector.get(actionLabel)
            if not action:
                raise ManagerActionException
            utils.log("INFO", "Executing action '%s'"%(actionLabel))
            action(self, data.get("content"))
        except ManagerInvalidMetaFormatException:
            utils.log("ERROR", "Invalid metadata format, asking again")
            askers.askMeta(self.__socket)
        except ManagerInvalidStateIdException:
            utils.log("ERROR", "Invalid state ID, ignoring")
        except ManagerInvalidStateFormatException:
            utils.log("ERROR", "Invalid state format, regenerating metadata")
            askers.askMeta(self.__socket)
        except ManagerActionException:
            utils.log("ERROR", "Action not binded, label: '%s'"%(actionLabel))
        except Exception as e:
            utils.log("ERROR", "Uncaught exception '%s'"%(e))


    def __getID(self):
        self.__config['runtime']['instance_id'] = 1

    def stop(self):
        self.__running = False

    def run(self):
        self.__getID()

        # run
        while self.__running:
            self.__getData()
#            self.__networkWorker = gevent.spawn(__getData)
#            self.__networkWorker.join()
