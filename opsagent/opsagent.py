#!/usr/bin/python
## CHANGE THIS
'''
Madeira OpsAgent launcher file

@author: Thibault BRONCHAIN
'''


from optparse import *
import logging


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


# option parser
def main_parse():
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
    options, args = main_parse()

    # set log level
    loglvl = 'INFO'
    if options.verbose: loglvl = 'DEBUG'
    elif options.quiet: loglvl = 'ERROR'
    __log(loglvl, options.log_file)

    # config parser
    config = Config(options.config_file).getConfig()

    # start daemon
    if options.daemon:
        loadAsDaemon()

    # start here
    # ..

if __name__ == '__main__':
    main()
