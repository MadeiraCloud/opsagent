'''
VisualOps agent States worker object
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''


## IMPORTS
# System imports
from multiprocessing import Process,Manager
import threading
import time
import os
import signal
import re
import sys
#import hashlib
import copy
# Custom imports
from opsagent import utils
from opsagent.checksum import Checksum
from opsagent.objects import send
from opsagent.exception import \
    OpsAgentException, \
    SWNoManagerException, \
    SWWaitFormatException
##

## DEFINES
# State succeed
SUCCESS=True
# State failed
FAIL=False
# Time to resend if failure
WAIT_RESEND=30
# Time before retrying state execution
WAIT_STATE_RETRY=30
# Time to wait between each state (don't overload)
WAIT_STATE=1
# Reset value for recipe version counter (no overflow)
RECIPE_COUNT_RESET=4096
##


## STATES WORKER OBJECT
# Manages the states execution
class StateWorker(threading.Thread):
    def __init__(self, config):
        # init thread and object
        threading.Thread.__init__(self)
        self.__config = config
        self.__manager = None

        # state adaptor
        self.__state_adaptor = None
        # state runner
        self.__state_runner = None

        # events
        self.__cv = threading.Condition()
        self.__wait_event = threading.Event()

        # states variables
        self.__version = None
        self.__states = None
        self.__done = []
        self.__status = 0

        # flags
        self.__cv_wait = False
        self.__waiting = False
        self.__run = False
        self.__abort = 0
        self.__executing = None
        self.__recipe_count = 0

        # shared memory
        self.__manager = Manager()
        self.__results = self.__manager.dict()
        self.__results['result'] = FAIL
        self.__results['comment'] = None
        self.__results['out_log'] = None

        # builtins methods map
        self.__builtins = {
            'meta.wait': self.__exec_wait,
            'meta.comment': None,
            }

        # delay pid
        self.__delaypid = None


    ## NETWORK RELAY
    # retry sending after disconnection
    def __send(self, data):
        utils.log("DEBUG", "Attempting to send data to backend ...",('__send',self))
        success = False
        sent = False
        cur_count = self.__recipe_count
        while (not success) and (data) and (self.__run) and (cur_count == self.__recipe_count):
            try:
                if not self.__manager:
                    raise SWNoManagerException("Can't reach backend ...")
                sent = self.__manager.send_json(data)
            except Exception as e:
                utils.log("ERROR", "Can't send data '%s', reason: '%s'."%(data,e),('__send',self))
                utils.log("WARNING", "Retrying in %s seconds."%(WAIT_RESEND),('__send',self))
                time.sleep(WAIT_RESEND)
            else:
                if sent:
                    success = True
                    utils.log("DEBUG", "Data successfully sent.",('__send',self))
                else:
                    utils.log("WARNING", "Data not sent, retrying in %s seconds..."%(WAIT_RESEND),('__send',self))
                    time.sleep(WAIT_RESEND)
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
        self.__done[:] = []
        self.__run = False
        self.__waiting = False
        self.__wait_event.clear()

    # End program
    def abort(self, kill=False, end=False):
        if self.__abort == 1 or (self.__abort == 2 and not kill):
            utils.log("DEBUG", "Already aborting ...",('abort',self))
            return

        self.__abort = (1 if kill else 2)

        if not end:
            self.__run = False

        if kill:
            self.kill()
        else:
            self.__kill_delay()

        if self.__cv_wait:
            utils.log("DEBUG", "Aquire conditional lock ...",('abort',self))
            self.__cv.acquire()
            utils.log("DEBUG", "Conditional lock acquired.",('abort',self))
            utils.log("DEBUG", "Notify execution thread.",('abort',self))
            self.__cv.notify()
            utils.log("DEBUG", "Release conditional lock.",('abort',self))
            self.__cv.release()


    # Program status
    def is_running(self):
        return self.__run

    def aborted(self):
        return (True if self.__abort else False)
    ##


    ## KILL PROCESS
    # Kill end of recipe delay
    def __kill_delay(self):
        if self.__delaypid:
            utils.log("DEBUG", "Recipe ended and in delay process, aborting ...",('__kill_delay',self))
            while True:
                try:
                    os.kill(self.__delaypid, signal.SIGKILL)
                    time.sleep(0.1)
                except OSError as e:
                    if e.find("No such process"):
                        self.__delaypid = None
                        utils.log("DEBUG", "Delay process killed.",('__kill_delay',self))
                        break
                    else:
                        utils.log("WARNING", "Error killing delay: %s"%(e),('__kill_delay',self))
        else:
            utils.log("DEBUG", "Recipe not in delay process.",('__kill_delay',self))

    # Kill child process (obsolete?)
    def __kill_childs(self):
        utils.log("DEBUG", "Killing states execution...",('__kill_childs',self))
        if not self.__config['runtime']['proc']:
            utils.log("WARNING", "/!\\ procfs is disabled, and you shouldn't do this. Potential hazardous behaviour can happen ...",('__kill_childs',self))
            return False
        proc = self.__config['global']['proc']
        flag = False
        cur_pid = os.getpid()
        pids = [pid for pid in os.listdir(proc) if pid.isdigit()]
        for pid in pids:
            try:
                filename = os.path.join(proc, pid, 'status')
                f = open(filename, "r")
                for line in f:
                    if re.search(r'PPid.*%s'%(cur_pid), line):
                        utils.log("INFO", "State execution process found #%s. Killing ..."%(pid),('__kill_childs',self))
                        os.kill(int(pid),signal.SIGKILL)
                        utils.log("DEBUG", "Process killed.",('kill',self))
                        flag = True
            except Exception as e:
                utils.log("DEBUG", "Kill child error on pid #%s: '%s'."%(pid,e),('__kill_childs',self))
        if not flag:
            utils.log("INFO", "No state execution found.",('__kill_childs',self))
        return True

    # Kill execution
    def __kill_exec(self):
        if self.__executing:
            utils.log("DEBUG", "Killing execution, pgid#%s"%(self.__executing),('__kill_exec',self))
            while True:
                try:
                    os.killpg(self.__executing,signal.SIGKILL)
                    time.sleep(0.1)
                except OSError as e:
                    if e.find("No such process"):
                        utils.log("INFO", "Execution killed, pgid#%s"%(self.__executing),('__kill_exec',self))
                        self.__executing = None
                    else:
                        utils.log("WARNING", "Error trying to kill process: %s"%(e),('__kill_exec',self))
        else:
            utils.log("DEBUG", "Execution not running."%(self.__executing),('__kill_exec',self))

    # Halt wait
    def __kill_wait(self):
        if self.__waiting:
            utils.log("DEBUG", "killing wait status",('kill_wait',self))
            self.__wait_event.set()
            self.__waiting = False
        else:
            utils.log("DEBUG", "worker not waiting",('kill_wait',self))

    # Kill the current execution
    def kill(self):
        if self.__run:
            utils.log("DEBUG", "Sending stop execution signal.",('kill',self))
            self.__run = False
            self.__kill_delay()
            self.__kill_wait()
            self.__kill_exec()
#            while self.__kill_childs() and self.__executing:
#                time.sleep(0.1)
            utils.log("INFO", "Execution killed.",('kill',self))
        else:
            utils.log("DEBUG", "Execution not running, nothing to do.",('kill',self))
    ##


    ## LOAD PROCESS
    # Load states modules
    def __load_modules(self):
        # clone states if not exists
        if not os.path.isdir("%s/%s"%(self.__config['module']['root'],self.__config['module']['name'])):
            utils.clone_repo(self.__config,self.__config['module']['root'],self.__config['module']['name'],self.__config['module']['mod_repo'])
            utils.checkout_repo(self.__config,self.__config['module']['root'],self.__config['module']['name'],self.__config['module']['mod_tag'],self.__config['module']['mod_repo'])

        # state adaptor
        if self.__state_adaptor:
            utils.log("DEBUG", "Deleting adaptor...",('load_modules',self))
            del self.__state_adaptor
        utils.log("DEBUG", "Loading adaptor...",('load_modules',self))
        import opsagent.state.adaptor
        reload(opsagent.state.adaptor)
        from opsagent.state.adaptor import StateAdaptor
        self.__state_adaptor = StateAdaptor()

        # state runner
        if self.__state_runner:
            utils.log("DEBUG", "Deleting runner...",('load_modules',self))
            del self.__state_runner
        utils.log("DEBUG", "Loading runner...",('load_modules',self))
        import opsagent.state.runner
        reload(opsagent.state.runner)
        from opsagent.state.runner import StateRunner
        self.__state_runner = StateRunner(config=self.__config['salt'])

    # Load new recipe
    def load(self, version=None, states=None):
        utils.log("DEBUG", "Aquire conditional lock ...",('load',self))
        self.__cv.acquire()
        utils.log("DEBUG", "Conditional lock acquired.",('load',self))
        self.__version = version

        self.__recipe_count = (self.__recipe_count+1 if self.__recipe_count < RECIPE_COUNT_RESET else 0)
        exp = None
        try:
            if states:
                utils.log("INFO", "Loading new states.",('load',self))
                del self.__states
                self.__states = copy.deepcopy(states)
            else:
                utils.log("INFO", "No change in states.",('load',self))
            utils.log("DEBUG", "Allow to run.",('load',self))
            self.__run = True
        except Exception as e:
            exp = e

        utils.log("DEBUG", "Notify execution thread.",('load',self))
        self.__cv.notify()
        utils.log("DEBUG", "Release conditional lock.",('load',self))
        self.__cv.release()

        if exp: raise OpsAgentException(exp)
    ##


    ## WAIT PROCESS
    # Add state to done list
    def state_done(self, sid):
        utils.log("DEBUG", "Adding id '%s' to done states list."%(sid),('state_done',self))
        self.__done.append(sid)
        self.__wait_event.set()
    ##


    ## MAIN EXECUTION
    # Action on wait
    def __exec_wait(self, sid, module, parameter):
        utils.log("INFO", "Waiting for external states ...",('__exec_wait',self))
        self.__waiting = True
        while (sid not in self.__done) and (self.__run):
            self.__wait_event.wait()
            self.__wait_event.clear()
            utils.log("INFO", "New state status received, analysing ...",('__exec_wait',self))
        self.__waiting = False
        if sid in self.__done:
            value = SUCCESS
            utils.log("INFO", "Waited state completed.",('__exec_wait',self))
        else:
            value = FAIL
            utils.log("WARNING", "Waited state ABORTED.",('__exec_wait',self))
        return (value,None,None)

    # Call salt library
    def __exec_salt(self, sid, module, parameter):
        utils.log("INFO", "Loading state ID '%s' from module '%s' ..."%(sid,module),('__exec_salt',self))

        parameter = copy.deepcopy(parameter)

        # Watch process
        if parameter and type(parameter) is dict and parameter.get("watch"):
            watchs = parameter.get("watch")
            if type(watchs) is list:
                utils.log("DEBUG", "Watched state detected.",('__exec_salt',self))
                del parameter["watch"]
                for watch in watchs:
                    try:
                        if not os.path.isfile(watch):
                            err = "Can't access watched file '%s'."%(watch)
                            utils.log("ERROR", err,('__exec_salt',self))
                            return (FAIL,err,None)
                        else:
                            utils.log("DEBUG", "Watched file '%s' found."%(watch),('__exec_salt',self))
                            cs = Checksum(watch,sid,self.__config['global']['watch'])
                            if cs.update():
                                parameter["watch"] = True
                                utils.log("INFO","Watch event triggered, replacing standard action ...",('__exec_salt',self))
                    except Exception as e:
                        err = "Internal error while watch process on file '%s': %s."%(watch,e)
                        utils.log("ERROR", err,('__exec_salt',self))
                        return (FAIL,err,None)

        try:
            # state convert
            utils.log("INFO", "Begin to convert salt states...", ('__exec_salt', self))
            salt_states = self.__state_adaptor.convert(sid, module, parameter, self.__state_runner.os_type)

            # exec salt state
            utils.log("INFO", "Begin to execute salt states...", ('__exec_salt', self))
            (result, comment, out_log) = self.__state_runner.exec_salt(salt_states)
        except Exception as err:
            utils.log("ERROR", str(err), ('__exec_salt',self))
            return (FAIL, "Internal error: %s"%(err), None)

        utils.log("INFO", "State ID '%s' from module '%s' done, result '%s'."%(sid,module,result),('__exec_salt',self))
        utils.log("DEBUG", "State out log='%s'"%(out_log),('__exec_salt',self))
        utils.log("DEBUG", "State comment='%s'"%(comment),('__exec_salt',self))
        return (result,comment,out_log)

    # Delay at the end of the states
    def __recipe_delay(self):
        utils.log("INFO", "Last state reached, execution paused for %s minutes."%(self.__config['salt']['delay']),('__recipe_delay',self))
        self.__delaypid = os.fork()
        if (self.__delaypid == 0): # son
            time.sleep(int(self.__config['salt']['delay'])*60)
            sys.exit(0)
        else:
            os.waitpid(self.__delaypid,0)
        self.__delaypid = None
        utils.log("INFO", "Delay passed, execution restarting...",('__recipe_delay',self))

    # Run state
    def __run_state(self, state):
        utils.log("INFO", "Running state '%s', #%s"%(state['id'], self.__status),('__runner',self))
        result = FAIL
        comment = None
        out_log = None
        try:
            if state.get('module') in self.__builtins:
                (result,comment,out_log) = (self.__builtins[state['module']](state['id'],
                                                                             state['module'],
                                                                             state['parameter'])
                                            if self.__builtins[state['module']]
                                            else (SUCCESS,None,None))
            else:
                (result,comment,out_log) = self.__exec_salt(state['id'],
                                                            state['module'],
                                                            state['parameter'])
        except SWWaitFormatException:
            utils.log("ERROR", "Wrong wait request",('__runner',self))
            result = FAIL
            comment = "Wrong wait request"
            out_log = None
        except Exception as e:
            utils.log("ERROR", "Unknown exception: '%s'."%(e),('__runner',self))
            result = FAIL
            comment = "Internal error: '%s'."%(e)
            out_log = None
        self.__results['result'] = result
        self.__results['comment'] = comment
        self.__results['out_log'] = out_log

    # Render recipes
    def __runner(self):
        utils.log("INFO", "Running StatesWorker ...",('__runner',self))
        while self.__run:
            if not self.__states:
                utils.log("WARNING", "Empty states list.",('__runner',self))
                self.__run = False
                continue
            state = self.__states[self.__status]

            # Load modules on each round
            if self.__status == 0:
                try:
                    self.__load_modules()
                except Exception:
                    utils.log("WARNING", "Can't load states modules.",('__runner',self))
                    self.__send(send.statelog(init=self.__config['init'],
                                              version=self.__version,
                                              sid=state['id'],
                                              result=FAIL,
                                              comment="Can't load states modules.",
                                              out_log=None))
                    self.__run = False
                    continue

            # Run state
            p = Process(target=self.__run_state, args=(state))
            p.start()
            self.__executing = p.pid
            p.join()

            # Reset running values
            self.__waiting = False
            self.__executing = None
            del p

            # Transmit results
            if self.__run:
                utils.log("INFO", "Execution complete, reporting logs to backend.",('__runner',self))
                # send result to backend
                self.__send(send.statelog(init=self.__config['init'],
                                          version=self.__version,
                                          sid=state['id'],
                                          result=self.__results['result'],
                                          comment=self.__results['comment'],
                                          out_log=self.__results['out_log']))
                # state succeed
                if self.__results['result'] == SUCCESS:
                    # global status iteration
                    self.__status += 1
                    if self.__status >= len(self.__states):
                        utils.log("INFO", "All good, last state succeed! Back to first one.",('__runner',self))
                        # not terminating, wait before next round
                        if not self.__abort:
                            self.__recipe_delay()
                            self.__status = 0
                        # terminating ...
                        if self.__abort: # don't "else" as abort may happen during the delay
                            self.__run = False
                    else:
                        time.sleep(WAIT_STATE)
                        utils.log("INFO", "All good, switching to next state.",('__runner',self))
                # state failed
                else:
                    self.__status = 0
                    if self.__abort:
                        self.__run = False
                    else:
                        utils.log("WARNING", "Something went wrong, retrying current state in %s seconds"%(WAIT_STATE_RETRY),('__runner',self))
                        time.sleep(WAIT_STATE_RETRY)
            else:
                utils.log("WARNING", "Execution aborted.",('__runner',self))


    # Callback on start
    def run(self):
        while not self.__abort:
            self.__cv.acquire()
            try:
                if not self.__run and not self.__abort:
                    utils.log("INFO", "Waiting for recipes ...",('run',self))
                    self.__cv_wait = True
                    self.__cv.wait()
                    self.__cv_wait = False
                utils.log("DEBUG", "Ready to go ...",('run',self))
                self.__runner()
            except Exception as e:
                utils.log("ERROR", "Unexpected error: %s."%(e),('run',self))
            self.reset()
            self.__cv.release()
        utils.log("WARNING", "Exiting...",('run',self))
        if self.__manager:
            utils.log("INFO", "Stopping manager...",('run',self))
            self.__manager.stop()
            utils.log("INFO", "Manager stopped.",('run',self))
        utils.log("WARNING", "Terminated.",('run',self))
    ##
##
