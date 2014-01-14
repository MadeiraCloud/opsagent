#!/usr/bin/python
'''
Madeira OpsAgent launcher script

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

# global defines
USAGE = 'usage: %prog [-hqvd] [-l logfile] [-c configfile]'
VERSION_NBR = '0.0.1a'
VERSION = '%prog '+VERSION_NBR


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


# TODO (use library?)
def daemonize(self):
    try:
        """ Ref:  http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012 """
        # Disable coredump
        #"ulimit -c 0"

	# First fork
        try:
            pid = os.fork()
            if pid > 0: 
                # Exit first parent
                sys.exit(0) 
        except OSError, e:
            # TODO
            self.logger.error("Cannot run Karajan in daemon mode: (%d) %s\n" % (e.errno, e.strerror))
            raise KarajanException
	
	# Decouple from parent environment.
        os.chdir("/")
        os.umask(0)
        os.setsid() #test id
	#suid/sgid

	# Second fork
        try:
            pid = os.fork()
            if pid > 0: 
                # Exit second parent.
                sys.exit(0)
        except OSError, e:
            # TODO
            self.logger.error("Cannot run Karajan in daemon mode: (%d) %s\n" % (e.errno, e.strerror))
            raise KarajanException
			
        # Open file descriptors and print start message
        si = file(Default.Forge.Karajan.stdin, 'r')
        so = file(Default.Forge.Karajan.stdout, 'a+')
        se = file(Default.Forge.Karajan.stderr, 'a+', 0)
        pid = os.getpid()
        sys.stderr.write("\nStarted Karajan with pid %i\n\n" % pid)
        sys.stderr.flush()
        if not os.path.exists(os.path.dirname(self.config.pidfile)):
            os.mkdir(os.path.dirname(self.config.pidfile))
        file(self.config.pidfile,'w+').write("%i\n" % pid)
		
        # Redirect standard file descriptors.
        os.close(sys.stdin.fileno())
        os.close(sys.stdout.fileno())
        os.close(sys.stderr.fileno())
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    except OSError, msg:
        self.logger.error("Cannot run Karajan in daemon mode: %s" % msg)
        raise KarajanException


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
    parser.add_option("-d", "--daemon", action="store_true", dest="daemon", default=False,
                      help="start in daemon mode"
                      )
    return parser.parse_args()


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
