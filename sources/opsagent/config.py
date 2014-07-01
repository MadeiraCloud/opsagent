'''
VisualOps agent configuration manager class
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''


# System imports
import ConfigParser
from ConfigParser import SafeConfigParser
from copy import deepcopy
import sys
import os
import re

# Custon imports
from opsagent.exception import ConfigFileFormatException, ConfigFileException


# Config class
class Config():
    requiredKeys = {
        'global': {
            'envroot': "Virtual environment root",
            'conf_path': "Configuration directory",
            'log_path': "Logs directory",
            'package_path': "Relative to envroot runtime package location",
            'scripts_path': "Scripts location",
            'token': "Unique identification file path",
            'watch': "Watched files checksum location",
            'logfile': "Log file location",
            },
        'userdata': {
            'ws_uri': "Backend connection URI",
            'app_id': "Application ID",
            'version': "Curent release version",
            'base_remote': "Base URL to fetch the sources",
            'gpg_key_uri': "Reference URI for GPG key",
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
            'loglvl': 'INFO',
#            'loglvl': 'DEBUG', #switch to debug
            'proc': '/proc',
            'pidfile': '/tmp/opsagentd.pid',
            'haltfile': '/tmp/opsagentd.halt',
            },
        'runtime': {
            'proc': False,
            'config_path': None,
            'clone': False,
            'tag': False,
            'compat': False,
            },
        'network': {
            'instance_id': "http://169.254.169.254/latest/meta-data/instance-id",
            'userdata': "http://169.254.169.254/latest/user-data",
            },
        'salt': {
            'pkg_cache': '/var/cache/pkg',
            'srv_root': '/srv/salt',
            'extension_modules': '/var/cache/salt/minion/extmods',
            'cachedir': '/var/cache/visualops',
            # delay between each round
            'delay': '10',
            # command timeout (deprecated)
            'timeout': '30',
            },
        'module': {
            # Locations relatives to modules directory (default /opt/visualops/env/lib/python-*/sites-package)
            'dst_adaptor': 'opsagent/state/adaptor.py',
            # Locations relatives to salt repository (default /opt/visualops/boostrap/salt)
            'src_salt': 'sources/salt',
            'src_adaptor': 'sources/adaptor.py',
            # Compatibility file relative to salt repository (default /opt/visualops/boostrap/salt)
            'compat': 'compat.txt',
            },
        }

    chrootKeys = {
        # 'Chrooted' to curent environment (default /opt/visualops/env)
        'salt': ['pkg_cache','srv_root','extension_modules','cachedir'],
        }

    def __init__(self, f=None):
        self.__parser = SafeConfigParser()
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
                if self.__c[section].get(key):
                    self.__c[section][key] = os.path.normpath(root+'/'+self.__c[section][key])
