'''
Madeira OpsAgent States worker object

@author: Thibault BRONCHAIN
'''


## IMPORTS
# System imports
import threading
import time
import os
import signal
import re
# Custom imports
from opsagent import utils
from opsagent.objects import send
from opsagent.exception import *

from adaptor import Adaptor
##

## DEFINES
# State succeed
SUCCESS=True
# State failed
FAIL=False
# Time to resend if failure
WAIT_RESEND=1
# Time before retrying state execution
WAIT_STATE_RETRY=1
##


## STATES WORKER OBJECT
# Manages the states execution
class StatesWorker(threading.Thread):
    def __init__(self, config):
        # init thread and object
        threading.Thread.__init__(self)
        self.__config = config
        self.__manager = None

        # state transfer
        self.__adaptor = Adaptor(config=config['salt'])

        # events
        self.__cv = threading.Condition()
        self.__wait_event = threading.Event()

        # states variables
        self.__version = None
        self.__states = None
        self.__done = []
        self.__status = 0

        # flags
        self.__run = False
        self.__waiting = False
        self.__abort = False

        # builtins methods map
        self.__builtins = {
            'general.wait' : self.__exec_wait,
            }


    ## NETWORK RELAY
    # retry sending after disconnection
    def __send(self, data):
        utils.log("DEBUG", "Attempting to send data to backend ...",('__send',self))
        try:
            if not self.__manager:
                raise SWNoManagerException
            self.__manager.send_json(data)
        except Exception as e:
            utils.log("ERROR", "Can't send data '%s', reason: '%s'."%(data,e),('__send',self))
            if self.__run:
                utils.log("WARNING", "Still running, retrying in %s seconds.",('__send',self))
                time.sleep(WAIT_RESEND)
                self.__send(data)
            else:
                utils.log("WARNING", "Not running, aborting send.",('__send',self))
        else:
            utils.log("DEBUG", "Data successfully sent.",('__send',self))
    ##


    ## CONTROL METHODS
    # Switch manager
    def set_manager(self, manager):
        utils.log("DEBUG", "Setting new manager",('set_manager',self))
        self.__manager = manager

    # Return waiting state
    def is_waiting(self):
        utils.log("DEBUG", "Wait status: %s"%(self.__waiting),('is_waiting',self))
        return self.__waiting

    # Return version ID
    def get_version(self):
        utils.log("DEBUG", "Curent version: %s"%(self.__version),('get_version',self))
        return self.__version

    # Reset states status
    def reset(self):
        self.__status = 0

    # End program
    def abort(self):
        self.__abort = True

    # Program status
    def aborted(self):
        return self.__aborted
    ##


    ## KILL PROCESS
    # Kill child process
    def __kill_childs(self):
        utils.log("DEBUG", "Killing states execution...",('__kill_childs',self))
        if not self.__config['runtime']['proc']:
            utils.log("WARNING", "/!\ procfs is disabled, and you shouldn't do this. Potential hazardous behaviour can happen ...",('__kill_childs',self))
            return
        proc = self.__config['global']['proc']
        flag = False
        cur_pid = os.getpid()
        pids = [pid for pid in os.listdir(proc) if pid.isdigit()]
        for pid in pids:
            try:
                filename = os.path.join(proc, pid, 'status')
                file = open(filename, "r")
                for line in file:
                    if re.search(r'PPid.*%s'%(cur_pid), line):
                        utils.log("INFO", "State execution process found #%s. Killing ..."%(pid),('kill',self))
                        os.kill(int(pid),signal.SIGKILL)
                        utils.log("DEBUG", "Process killed.",('kill',self))
                        flag = True
            except Exception as e:
                utils.log("DEBUG", "Kill child error on pid #%s: '%s'."%(pid,e),('__kill_childs',self))
        if not flag:
            utils.log("INFO", "No state execution found.",('__kill_childs',self))

    # Halt wait
    def __kill_wait(self):
        utils.log("DEBUG", "killing wait status",('kill',self))
        self.__wait_event.set()

    # Kill the current execution
    def kill(self):
        if self.__run:
            utils.log("DEBUG", "Sending stop execution signal.",('kill',self))
            self.__run = False
            if self.__waiting:
                self.__kill_wait()
            self.__kill_childs()
            utils.log("INFO", "Execution killed.",('kill',self))
        else:
            utils.log("DEBUG", "Execution not running, nothing to do.",('kill',self))
    ##


    ## LOAD PROCESS
    # Load new recipe
    def load(self, version=None, states=None):
        utils.log("DEBUG", "Aquire conditional lock ...",('load',self))
        self.__cv.acquire()
        utils.log("DEBUG", "Conditional lock acquired.",('load',self))
        self.__version = version
        if states:
            utils.log("INFO", "Loading new states.",('load',self))
            self.__states = states
        else:
            utils.log("INFO", "No change in states.",('load',self))
        utils.log("DEBUG", "Reseting status.",('load',self))
        self.reset()
        utils.log("DEBUG", "Allow to run.",('load',self))
        self.__run = True
        utils.log("DEBUG", "Notify execution thread.",('load',self))
        self.__cv.notify()
        utils.log("DEBUG", "Release conditional lock.",('load',self))
        self.__cv.release()
    ##


    ## WAIT PROCESS
    # Add state to done list
    def state_done(self, id):
        utils.log("DEBUG", "Adding id '%s' to done states list."%(id),('state_done',self))
        self.__done.append(id)
        self.__wait_event.set()
    ##


    ## MAIN EXECUTION
    # Action on wait
    def __exec_wait(self, id, module, parameter):
        utils.log("INFO", "Waiting for external states ...",('__exec_wait',self))
        self.__waiting = True
        while (id not in self.__done) and (self.__run):
            self.__wait_event.wait()
            self.__wait_event.clear()
            utils.log("INFO", "New state status received, analysing ...",('__exec_wait',self))
        self.__waiting = False
        if id in self.__done:
            value = SUCCESS
            utils.log("INFO", "Waited state completed.",('__exec_wait',self))
        else:
            value = FAIL
            utils.log("WARNING", "Waited state ABORTED.",('__exec_wait',self))
        return (value,None,None)

    import hashlib

    # Write hash
    def __create_hash(self, target, hash, file):
        utils.log("DEBUG", "Writing new hash for file '%s' in '%s': '%s'"%(file, target, hash),('__create_hash',self))
        f = open(target, 'w')
        f.write(hash)
        f.close()

    # Call salt library
    def __exec_salt(self, id, module, parameter):
        utils.log("INFO", "Loading state ID '%s' from module '%s' ..."%(id,module),('__exec_salt',self))
        first = True

        # Watch process
        if type(parameter) is dict and parameter.get("watch"):
            utils.log("DEBUG", "Watched state detected."%(watch),('__exec_salt',self))
            watch = parameter.get("watch")
            del parameter["watch"]
            try:
                if not os.path.isfile(watch):
                    err = "Can't access watched file '%s'."%(watch)
                    utils.log("ERROR", err,('__exec_salt',self))
                    return (FAIL,err,None)
                else:
                    utils.log("DEBUG", "Watched file '%s' found."%(watch),('__exec_salt',self))
                    curent_hash = hashlib.md5(watch).hexdigest()
                    cs = os.path.join(self.__config['global']['watch'], id)
                    if os.path.isfile(cs):
                        first = False
                        with open(cs, 'r') as f:
                            old_hash = f.read()
                        if old_hash != curent_hash:
                            utils.log("INFO","Watch event triggered, replacing standard action ...",('__exec_salt',self))
                            parameter["watch"] = True
                            utils.log("DEBUG","Standard action replaced.",('__exec_salt',self))
                        else:
                            utils.log("DEBUG","No watched event triggered.",('__exec_salt',self))
                    else:
                        utils.log("DEBUG","No old record, creating hash and executing normal command ...",('__exec_salt',self))
                        self.__create_hash(cs, curent_hash, file)
                        utils.log("DEBUG","Hash stored.",('__exec_salt',self))
            except Exception as e:
                err = "Unknown error during watch process on file '%s': %s."%(watch,e)
                utils.log("WARNING", err,('__exec_salt',self))
                return (FAIL,err,None)

        # Standard execution
        # TODO dict conversion + salt call
#        import subprocess
#        p = subprocess.Popen(["sleep","5"])
#        result = (SUCCESS if p.wait() == 0 else FAIL)
#        (out_log,err_log) = p.communicate()
        # /TODO

        # Salt call
        (result, err_log, out_log) = self.__adaptor.prepare(id, module, parameter)

        utils.log("INFO", "State ID '%s' from module '%s' done, result '%s'."%(id,module,result),('__exec_salt',self))
        utils.log("DEBUG", "State out log='%s'"%(out_log),('__exec_salt',self))
        utils.log("DEBUG", "State error log='%s'"%(err_log),('__exec_salt',self))
        return (result,err_log,out_log)

    # Delay at the end of the states
    def __recipe_delay(self):
        utils.log("INFO", "Last state reached, execution paused for %s minutes."%(self.__config['salt']['delay']),('__recipe_delay',self))
        pid = os.fork()
        if (pid == 0):
            time.sleep(self.__config['salt']['delay']*60)
        else:
            os.waitpid(pid)
        utils.log("INFO", "Delay passed, execution restarting...",('__recipe_delay',self))

    # Render recipes
    def __runner(self):
        utils.log("INFO", "Running StatesWorker ...",('__runner',self))
        utils.log("DEBUG", "Waiting for recipes ...",('__runner',self))
        self.__cv.acquire()
        while not self.__run:
            self.__cv.wait()
        utils.log("DEBUG", "Ready to go ...",('__runner',self))
        while self.__run:
            if not self.__states:
                utils.log("WARNING", "Empty states list.",('__runner',self))
                self.__run = False
                continue
            state = self.__states[self.__status]
            utils.log("INFO", "Running state '%s', #%s"%(state['stateid'], self.__status),('__runner',self))
            try:
                if state.get('module') in self.__builtins:
                    (result,err_log,out_log) = self.__builtins[state['module']](state['stateid'],
                                                                                state['module'],
                                                                                state['parameter'])
                else:
                    (result,err_log,out_log) = self.__exec_salt(state['stateid'],
                                                                state['module'],
                                                                state['parameter'])
            except SWWaitFormatException:
                utils.log("ERROR", "Wrong wait request",('__runner',self))
                result = FAIL
                err_log = "Wrong wait request"
                out_log = None
            except Exception as e:
                utils.log("ERROR", "Unknown exception: '%s'."%(e),('__runner',self))
                result = FAIL
                err_log = "Unknown exception: '%s'."%(e)
                out_log = None
            self.__waiting = False
            if self.__run:
                utils.log("INFO", "Execution complete, reporting logs to backend.",('__runner',self))
                self.__send(send.statelog(init=self.__config['init'],
                                          version=self.__version,
                                          id=state['stateid'],
                                          result=result,
                                          err_log=err_log,
                                          out_log=out_log))
                if result == SUCCESS:
                    # global status iteration
                    self.__status += 1
                    if self.__status >= len(self.__states):
                        utils.log("INFO", "All good, last state succeed! Back to first one.",('__runner',self))
                        self.__recipe_delay()
                        self.__status = 0
                    else:
                        utils.log("INFO", "All good, switching to next state.",('__runner',self))
                else:
                    utils.log("WARNING", "Something went wrong, retrying current state in %s seconds"%(WAIT_STATE_RETRY),('__runner',self))
                    time.sleep(WAIT_STATE_RETRY)
            else:
                utils.log("WARNING", "Execution aborted.",('__runner',self))
            if self.__abort:
                utils.log("WARNING", "Exiting...",('__runner',self))
                self.__run = False
        self.__cv.release()

    # Callback on start
    def run(self):
        try:
            while not self.__abort:
                self.__runner()
        except Exception as e:
            utils.log("ERROR", "Unexpected error: %s."%(e),('run',self))
        if self.__manager:
            self.__manager.stop()
    ##
##
