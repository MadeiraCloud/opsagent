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


# terminating process
def handler(signum=None, frame=None):
    utils.log("WARNING", "Signal handler called with signal %s"%signum,('handler',None))
    ABORT=True


# logger settings
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
    def run_manager(self, config, sw):
        utils.log("DEBUG", "Creating Network Manager ...",('run_manager',None))
        manager = Manager(url=config['network']['ws_uri'], config=config, statesworker=sw)
        utils.log("DEBUG", "Network Manager created.",('run_manager',None))
        try:
            utils.log("DEBUG", "Connecting manager to backend.",('run_manager',None))
            manager.connect()
            utils.log("DEBUG", "Connection done, registering to StateWorker.",('run_manager',None))
            sw.set_manager(manager)
            utils.log("DEBUG", "Registration done, running forever ...",('run_manager',None))
            manager.run_forever()
            utils.log("DEBUG", "Network connection lost/aborted.",('run_manager',None))
        except Exception as e:
            utils.log("ERROR", "Network error: '%s'"%(e),('run_manager',None))
            if manager.connected():
                utils.log("INFO", "Connection not closed. Closing ...",('run_manager',None))
                manager.close()
                utils.log("DEBUG", "Connection closed.",('run_manager',None))
            else:
                utils.log("DEBUG", "Connection already closed.",('run_manager',None))

    def run(self, config):
        # start
        sw = StatesWorker(config=config)
        sw.start()
        while not ABORT:
            try:
                if not sw.is_alive():
                    del sw
                    sw = StatesWorker(config=config)
                    sw.start()
                self.run_manager(config, sw)
            except Exception as e:
                utils.log("ERROR", "Unexpected error: '%s'"%(e),('run',None))
                time.sleep(0.1)
                utils.log("WARNING", "Conenction aborted, retrying ...",('run',None))
        if sw.is_alive():
            sw.join()


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

    # global abort
    global ABORT
    ABORT=False

    # handle termination
    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
        try: signal.signal(sig, handler)
        except: pass #pass some signals if not POSIX

    # run
    runner = OpsAgentRunner(config['global']['pidfile'])
    command = sys.argv[-1:]
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
    else:
        runner.run(config)



if __name__ == '__main__':
    main()
