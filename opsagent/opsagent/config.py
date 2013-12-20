'''
Madeira OpsAgent configuration manager class

@author: Thibault BRONCHAIN
'''


# System imports
import ConfigParser
from ConfigParser import RawConfigParser
from copy import deepcopy


# Custon imports
import utils
import exception


# Config class
class Config():
    requiredKeys = {
        'foo': {
            'bar': "bar represents blablabla",
            },
        }

    defaultValues = {
        'toto': {
            'tata': "tutu",
            },
        }

    def __init__(self, file=None):
        self.__parser = SafeConfigParser(allow_no_value=True)
        self.__c = (deepcopy(defaultValues)
                    if defaultValues
                    else {})
        if file:
            self.__readFile(file)
            try:
                self.__parseFile()
                self.__checkRequired(requiredKeys)
            except Exception as e:
                utils.log("ERROR", "Invalid config file '%s': %s"%(file,e))
                raise ConfigFileException
            except ConfigFileFormatException:
                utils.log("ERROR", "Invalid config file '%s'."%(file))
                raise ConfigFileException
            else:
                utils.log("INFO", "Config file loaded '%s'."%(file))

    def __readFile(self, file):
        try:
            self.__parser.read(file)
        except ConfigParser.ParsingError as e:
            utils.log("ERROR", "Can't load config file %s, %s"%(file,e))
        else:
            utils.log("DEBUG", "Config file parsed %s."%(file),('__readfile',self))

    def parseFile(self, file=None):
        if file:
            self.__readFile(file)
        for name in parser.sections():
            self.__c.setdefault(name, {})
            for key, value in parser.items(name):
                self.__c[name][key] = value

    def checkRequired(self, required):
        valid = True
        for section in required:
            if section not in self.__c:
                utils.log("ERROR", "Missing section '%s' in current configuration file."%(section))
                valid = False
                continue
            for key in required[section]:
                if key not in self.__c[section]:
                    utils.log("ERROR", "Missing key '%s' in section '%s' in current configuration file."%(key,section))
                    valid = False
                else:
                    utils.log("DEBUG", "Required key '%s' in section '%s' in current configuration file found."%(key,section),('checkRequired',self))
        if not valid:
            raise ConfigFileException

    def getConfig(self, copy=False):
        return (self.__c if not copy else deepcopy(self.__c))
