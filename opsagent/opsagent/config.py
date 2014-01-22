'''
Madeira OpsAgent configuration manager class

@author: Thibault BRONCHAIN
'''


# System imports
import ConfigParser
from ConfigParser import SafeConfigParser
from copy import deepcopy
import sys

# Custon imports
import utils
from exception import *


# Config class
class Config():
    requiredKeys = {
#        'foo': {
#            'bar': "bar represents blablabla",
#            },
        }

    defaultValues = {
        'global': {
            'loglvl': 'WARNING',
            'proc': '/proc',
            'watch': '/tmp/opsagent/opsagent/watch',
            'pidfile': '/tmp/opsagentd.pid',
            'token': '/etc/opsagent.d/token'
            },
        'runtime': {
            'proc': False,
            },
        'network': {
            'ws_uri': "wss://api.madeiracloud.com/agent/",
            'instance_id': "http://169.254.169.254/latest/meta-data/instance-id",
            'user_data': "http://169.254.169.254/latest/user-data",
            },
        'salt': {
            'file_roots': '/opsagent/env/srv/salt',
            'extension_modules': '/opsagent/env/var/cache/salt/minion/extmods',
            'cachedir': '/opsagent/env/var/cache/madeira',
            'delay': 1,
            'timeout': 30,
            }
        }

    def __init__(self, file=None):
        self.__parser = SafeConfigParser(allow_no_value=True)
        self.__c = (deepcopy(Config.defaultValues)
                    if Config.defaultValues
                    else {})
        if file:
            self.__read_file(file)
            try:
                self.parse_file()
                self.check_required(Config.requiredKeys)
            except Exception as e:
                sys.stderr.write("ERROR: Invalid config file '%s': %s\n"%(file,e))
                raise ConfigFileException
            except ConfigFileFormatException:
                sys.stderr.write("ERROR: Invalid config file '%s'.\n"%(file))
                raise ConfigFileException
            else:
                sys.stdout.write("Config file loaded '%s'.\n"%(file))

    def __read_file(self, file):
        try:
            self.__parser.read(file)
        except ConfigParser.ParsingError as e:
            sys.stderr.write("ERROR: Can't load config file %s, %s.\n"%(file,e))
        else:
            sys.stdout.write("Config file parsed '%s'.\n"%(file))

    def parse_file(self, file=None):
        if file:
            self.__read_file(file)
        for name in self.__parser.sections():
            self.__c.setdefault(name, {})
            for key, value in self.__parser.items(name):
                self.__c[name][key] = value

    def check_required(self, required):
        valid = True
        for section in required:
            if section not in self.__c:
                sys.stderr.write("ERROR: Missing section '%s' in current configuration file.\n"%(section))
                valid = False
                continue
            for key in required[section]:
                if key not in self.__c[section]:
                    sys.stderr.write("ERROR: Missing key '%s' in section '%s' in current configuration file.\n"%(key,section))
                    valid = False
        if not valid:
            raise ConfigFileException

    def getConfig(self, copy=False):
        return (self.__c if not copy else deepcopy(self.__c))
