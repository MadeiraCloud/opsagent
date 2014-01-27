#!/usr/bin/python
'''
Madeira OpsAgent launcher script

@author: Thibault BRONCHAIN
'''


# System imports
from optparse import *
import logging
import time
import sys
import signal
import re
import threading, Queue

# Custom imports
from opsagent.daemon import Daemon
from opsagent.config import Config
from opsagent import utils
from opsagent.exception import *
from opsagent.manager import Manager
from opsagent.state.statesworker import StatesWorker


# general defines
USAGE = 'usage: %prog [-hqv] [-l logfile] [-c configfile] (start|stop|restart|stop-wait|restart-wait)'
VERSION_NBR = '0.0.1a'
VERSION = '%prog '+VERSION_NBR


# logger settings
LOGLVL_VALUES=['DEBUG','INFO','WARNING','ERROR']
LOG_FORMAT = '[%(levelname)s]-%(asctime)s: %(message)s'
def __log(lvl, file=None):
    level = logging.getLevelName(lvl)
    formatter = logging.Formatter(LOG_FORMAT)
    handler = (logging.FileHandler(file) if file else logging.StreamHandler())
    logger = logging.getLogger()
    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)


# OpsAgent safe runner
class OpsAgentRunner(Daemon):
    def run_manager(self):
        utils.log("DEBUG", "Creating Network Manager ...",('run_manager','OpsAgentRunner'))
        manager = Manager(url=self.config['network']['ws_uri'], config=self.config, statesworker=self.__sw)
        utils.log("DEBUG", "Network Manager created.",('run_manager','OpsAgentRunner'))
        try:
            utils.log("DEBUG", "Connecting manager to backend.",('run_manager','OpsAgentRunner'))
            manager.connect()
            utils.log("DEBUG", "Connection done, registering to StateWorker.",('run_manager','OpsAgentRunner'))
            self.__sw.set_manager(manager)
            utils.log("DEBUG", "Registration done, running forever ...",('run_manager','OpsAgentRunner'))
            manager.run_forever()
            utils.log("DEBUG", "Network connection lost/aborted.",('run_manager','OpsAgentRunner'))
        except Exception as e:
            utils.log("ERROR", "Network error: '%s'"%(e),('run_manager','OpsAgentRunner'))
            if manager.connected():
                utils.log("INFO", "Connection not closed. Closing ...",('run_manager','OpsAgentRunner'))
                manager.close()
                utils.log("DEBUG", "Connection closed.",('run_manager','OpsAgentRunner'))
            else:
                utils.log("DEBUG", "Connection already closed.",('run_manager','OpsAgentRunner'))

    def run(self):
        # init
        self.__sw = StatesWorker(config=self.config)

        # terminating process
        def handler(signum=None, frame=None):
            utils.log("WARNING", "Signal handler called with signal %s"%signum,('handler','OpsAgentRunner'))
            try:
                fd = file(self.__haltfile,'r')
                halt = int(fd.read().strip())
                fd.close()
            except IOError:
                halt = None
            if halt:
                if halt is "wait":
                    self.__sw.abort()
                    return
                elif halt is "end":
                    self.__sw.abort(end=True)
                    return
            utils.log("WARNING", "No soft arguent set, exiting now...",('handler','OpsAgentRunner'))
            sys.exit(0)

        # handle termination
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            try: signal.signal(sig, handler)
            except: pass #pass some signals if not POSIX

        # start
        self.__sw.start()

        # run forever
        while not self.__sw.aborted():
            try:
#                # states worker dead
#                if not sw.is_alive():
#                    del sw
#                    sw = StatesWorker(config=config)
#                    sw.start()
                # run manager
                self.run_manager()
            except Exception as e:
                utils.log("ERROR", "Unexpected error: '%s'"%(e),('run','OpsAgentRunner'))
                time.sleep(0.1)
                utils.log("WARNING", "Conenction aborted, retrying ...",('run','OpsAgentRunner'))

        # end properly
        if self.__sw.is_alive():
            self.__sw.join()
        self.__sw = None


# option parser
def optParse():
    parser = OptionParser(usage=USAGE, version=VERSION)
    parser.add_option("-c", "--config-file", action="store", dest="config_file",
                      help="specify config file"
                      )
    parser.add_option("-l", "--log-file", action="store", dest="log_file",
                      help="specify log file"
                      )
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False,
                      help="operate quietly (log minimal info)"
                      )
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="verbose mode (log debug -all- info)"
                      )
    return parser.parse_args()


def main():
    # options parsing
    options, args = optParse()

    # config parser
    try:
        config = Config(options.config_file).getConfig()
    except ConfigFileException:
        config = Config().getConfig()
    except Exception as e:
        sys.stderr.write("ERROR: Unknown fatal config exception: %s, loading default.\n"%(e),('main',self))
        config = Config().getConfig()

    # set log level
    loglvl = config['global']['loglvl']
    if loglvl and loglvl not in LOGLVL_VALUES:
        sys.stderr.write("WARNING: Wrong loglvl '%s' (check config file). Loading in default mode (INFO).\n"%(loglvl),('main',self))
        loglvl = 'INFO'
    if options.verbose: loglvl = 'DEBUG'
    elif options.quiet: loglvl = 'ERROR'
    __log(loglvl,
          (options.log_file if options.log_file else config['global'].get('logfile')))

    # run
    runner = OpsAgentRunner(config)
    command = sys.argv[-1]
    if command == "start":
        runner.start()
    elif command == "stop":
        runner.stop()
    elif command == "restart":
        runner.restart()
    elif command == "stop-wait":
        runner.stop(wait=True)
    elif command == "restart-wait":
        runner.restart(wait=True)
    elif command == "stop-end":
        runner.stop(end=True)
    elif command == "restart-end":
        runner.restart(end=True)
    else:
        runner.run()



if __name__ == '__main__':
    main()
