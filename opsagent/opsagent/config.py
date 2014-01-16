'''
Madeira OpsAgent configuration manager class

@author: Thibault BRONCHAIN
'''


# System imports
import ConfigParser
from ConfigParser import SafeConfigParser
from copy import deepcopy


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
            'proc': '/proc',
            'watch': '/tmp/madeira/opsagent/watch',
            },
        'runtime': {
            'proc': False,
            },
        'toto': {
            'tata': "tutu",
            },
        'network': {
            'ws_uri': "ws://localhost:8964/agent/",
            'instance_id': "http://169.254.169.254/latest/meta-data/instance-id",
            'user_data': "http://169.254.169.254/latest/user-data",
            },
        'salt': {
            'file_roots': '/srv/salt',
            'extension_modules': '/var/cache/salt/minion/extmods',
            'cachedir': '/var/cache/madeira/',
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
                utils.log("ERROR", "Invalid config file '%s': %s"%(file,e),('__init__',self))
                raise ConfigFileException
            except ConfigFileFormatException:
                utils.log("ERROR", "Invalid config file '%s'."%(file),('__init__',self))
                raise ConfigFileException
            else:
                utils.log("INFO", "Config file loaded '%s'."%(file),('__init__',self))

    def __read_file(self, file):
        try:
            self.__parser.read(file)
        except ConfigParser.ParsingError as e:
            utils.log("ERROR", "Can't load config file %s, %s"%(file,e),('__readfile',self))
        else:
            utils.log("DEBUG", "Config file parsed %s."%(file),('__readfile',self))

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
                utils.log("ERROR", "Missing section '%s' in current configuration file."%(section),('check_required',self))
                valid = False
                continue
            for key in required[section]:
                if key not in self.__c[section]:
                    utils.log("ERROR", "Missing key '%s' in section '%s' in current configuration file."%(key,section),('check_required',self))
                    valid = False
                else:
                    utils.log("DEBUG", "Required key '%s' in section '%s' in current configuration file found."%(key,section),('check_required',self))
        if not valid:
            raise ConfigFileException

    def getConfig(self, copy=False):
        return (self.__c if not copy else deepcopy(self.__c))
