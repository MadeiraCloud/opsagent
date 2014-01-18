#!/usr/bin/python
'''
Madeira OpsAgent daemon script

@author: Thibault BRONCHAIN
'''


# System imports
from optparse import *
import logging
import time


# Custom imports
from opsagent.config import Config
from opsagent import utils
from opsagent.exception import *
from opsagent.manager import Manager
from opsagent.state.statesworker import StatesWorker


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


def run(config, sw):
    utils.log("DEBUG", "Creating Network Manager ...",('run',None))
    manager = Manager(url=config['network']['ws_uri'], config=config, statesworker=sw)
    utils.log("DEBUG", "Network Manager created.",('run',None))
    try:
        utils.log("DEBUG", "Connecting manager to backend.",('run',None))
        manager.connect()
        utils.log("DEBUG", "Connection done, registering to StateWorker.",('run',None))
        sw.set_manager(manager)
        utils.log("DEBUG", "Registration done, running forever ...",('run',None))
        manager.run_forever()
        utils.log("DEBUG", "Network connection lost/aborted.",('run',None))
    except Exception as e:
        utils.log("ERROR", "Network error: '%s'"%(e),('run',None))
        if manager.connected():
            utils.log("INFO", "Connection not closed. Closing ...",('run',None))
            manager.close()
            utils.log("DEBUG", "Connection closed.",('run',None))
        else:
            utils.log("DEBUG", "Connection already closed.",('run',None))


def main():
    # options parsing
    options, args = optParse()

    # set log level
    loglvl = 'INFO'
    if options.verbose: loglvl = 'DEBUG'
    elif options.quiet: loglvl = 'ERROR'
    __log(loglvl, options.log_file)

    # config parser
    try:
        config = Config(options.config_file).getConfig()
    except ConfigFileException:
        config = Config().getConfig()
    except Exception as e:
        utils.log("ERROR", "Unknown fatal config exception: %s."%(e),('main',self))
        config = Config().getConfig()

    # start daemon
#    if options.daemon:
#        loadAsDaemon()

    # start
    sw = StatesWorker(config=config)
    sw.start()
    while True:
# TODO delete (DEBUG)
#    if True:
        try:
            run(config, sw)
        except Exception as e:
            utils.log("ERROR", "Unexpected error: '%s'"%(e),('main',None))
        time.sleep(0.1)
        utils.log("WARNING", "Conenction aborted, retrying ...",('main',None))


if __name__ == '__main__':
    main()
