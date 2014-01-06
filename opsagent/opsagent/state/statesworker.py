'''
Madeira OpsAgent States worker object

@author: Thibault BRONCHAIN
'''


## IMPORTS
# System imports
import threading
# Custom imports
import opsagent.utils
from opsagent.objects import send
##

## DEFINES
# State succeed
SUCCESS=True
# State failed
FAIL=False
##


## STATES WORKER OBJECT
# Manages the states execution
class StatesWorker(threading.Thread):
    def __init__(self, config, manager, version, states):
        # config
        self.__config = config

        # manager object
        self.__manager = manager

        # load data
        self.__version = version
        self.__states = states

        # states variables
        self.__version = None
        self.__done = []
        self.__states = None

        # flags
        self.__stop = False
        self.__waiting = False

        # builtins map
        self.__builtins = {
            # TODO change wait name
            'wait': self.__exec_wait,
            }

    # Return waiting state
    def isWaiting(self):
        return self.__waiting

    # Return version ID
    def getVersion(self):
        return self.__version

    # Add state to done list
    def stateDone(self, id):
        self.__done.append(id)

    # Find child process
    def __findChilds(self):
        # TODO
        pass

    # Kills the current execution
    def kill(self, version=None, states=None):
        # TODO
        # kill the child process
        # stop wait
        self.__stop = True

    def __exec_wait(self):
        # TODO
        return (SUCCESS,"ERR WAIT","OUT WAIT")
    def __exec_salt(self):
        # TODO
        return (SUCCESS,"ERR SALT","OUT SALT")

    # Callback on start
    def run(self):
        self.__stop = False
        while not self.__stop:
            state = self.__states[status]
            if state.get('module') in self.__builtins:
                (result,err_log,out_log) = self.__builtins[state['module']]()
            else:
                (result,err_log,out_log) = self.__exec_salt()
            self.__waiting = False
            if self.__stop:
                # TODO about log sending
                pass
            else:
                manager.send_json(send.statelog(init=self.__config['init'],
                                                version=self.__version,
                                                id=state['stateid'],
                                                result=result,
                                                err_log=err_log,
                                                out_log=out_log))
                if result == SUCCESS:
                    # global status iteration
                    status += 1
                    if status == len(self.__states):
                        status = 0

    # Kills child process if destroyed
    def __del__(self):
        self.kill()
##
