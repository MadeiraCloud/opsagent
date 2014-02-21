'''
Madeira OpsAgent configuration manager class

@author: Thibault BRONCHAIN
'''


# System imports
import ConfigParser
from ConfigParser import SafeConfigParser
from copy import deepcopy
import sys
import os

# Custon imports
from opsagent.exception import ConfigFileFormatException, ConfigFileException


# Config class
class Config():
    requiredKeys = {
        'global': {
            'envroot': "Virtual environment root",
            'token': "Unique identification file path",
            'watch': "Watched files checksum location",
            'logfile': "Log file location",
            },
        'network': {
            'ws_uri': "Backend connection URI",
            'app_id': "Application ID",
            },
        'module': {
            'root': "Salt modules repo root",
            'name': "Salt modules repo name",
            'bootstrap': "Salt modules bootstrap script",
            'mod_repo': "Salt modules repo URI",
            'mod_tag': "Salt modules repo tag",
            },
        }

    defaultValues = {
        'global': {
            'loglvl': 'WARNING',
            'proc': '/proc',
            'pidfile': '/tmp/opsagentd.pid',
            'haltfile': '/tmp/opsagentd.halt',
#            'watch': '/etc/opsagent.d/watch',
#            'token': '/etc/opsagent.d/token',
#            'logfile': '/var/log/madeira/agent.log',
            },
        'runtime': {
            'proc': False,
            'config_path': None,
            },
        'network': {
            'instance_id': "http://169.254.169.254/latest/meta-data/instance-id",
#            'ws_uri': "wss://api.madeiracloud.com/agent/",
#            'user_data': "http://169.254.169.254/latest/user-data",
            },
        'salt': {
#            'update_file': '/tmp/opsagent.salt.update',
            'srv_root': '/srv/salt',
            'extension_modules': '/var/cache/salt/minion/extmods',
            'cachedir': '/var/cache/madeira',
            'delay': '1',
            'timeout': '30',
            },
        'module': {
            },
        }

    chrootKeys = {
        'salt': ['srv_root','extension_modules','cachedir'],
        }

    def __init__(self, f=None):
        self.__parser = SafeConfigParser(allow_no_value=True)
        self.__c = (deepcopy(Config.defaultValues)
                    if Config.defaultValues
                    else {})
        if f:
            self.__read_file(f)
            try:
                self.parse_file()
                self.check_required(Config.requiredKeys)
                self.chroot(root=self.__c['global']['envroot'], mod=Config.chrootKeys)
            except ConfigFileFormatException:
                sys.stderr.write("ERROR: Invalid config file '%s'.\n"%(f))
                raise ConfigFileException
            except Exception as e:
                sys.stderr.write("ERROR: Invalid config file '%s': %s\n"%(f,e))
                raise ConfigFileException
            else:
                sys.stdout.write("Config file loaded '%s'.\n"%(f))

    def __read_file(self, f):
        try:
            self.__parser.read(f)
        except ConfigParser.ParsingError as e:
            sys.stderr.write("ERROR: Can't load config file %s, %s.\n"%(f,e))
        else:
            sys.stdout.write("Config file parsed '%s'.\n"%(f))

    def parse_file(self, f=None):
        if f:
            self.__read_file(f)
        for name in self.__parser.sections():
            if name is 'runtime': continue
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

    def chroot(self, root, mod):
        for section in mod:
            for key in mod[section]:
                if self.__c['section'].get(key):
                    self.__c['section'][key] = os.path.normpath(root+'/'+self.__c['section'][key])
