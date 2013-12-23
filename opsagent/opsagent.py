#!/usr/bin/python
## TODO CHANGE THIS
'''
Madeira OpsAgent launcher file

@author: Thibault BRONCHAIN
'''


# System imports
from optparse import *
import logging


# Custom imports
from opsagent import utils
from opsagent import exception
from opsagent import config
from opsagent.manager import Manager

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


def main():
    # options parsing
    options, args = optParse()

    # set log level
    loglvl = 'INFO'
    if options.verbose: loglvl = 'DEBUG'
    elif options.quiet: loglvl = 'ERROR'
    __log(loglvl, options.log_file)

    # config parser
    config = Config(options.config_file).getConfig()

    # start daemon
#    if options.daemon:
#        loadAsDaemon()

    # start
    manager = Manager(config)
    manager.run()

if __name__ == '__main__':
    main()
