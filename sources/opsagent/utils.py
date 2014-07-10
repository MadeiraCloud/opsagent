'''
VisualOps agent utilities
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

# System imports
import logging
import time
import subprocess
import os
import os.path
import shutil
import collections
import re

# Custom imports
from opsagent.exception import ManagerInvalidStatesRepoException


# Defines
DEBUG_DELAY=0.1
DEBUG=10
COLOR=False

# Logging defines
LOGGING_EQ = {
    "DEBUG"    : logging.debug,
    "INFO"     : logging.info,
    "WARNING"  : logging.warning,
    "ERROR"    : logging.error,
    "CRITICAL" : logging.critical,
    }

# Colors defines
COLORS_EQ = {
    "DEBUG"    : ("\x1b[38;5;6m","\x1b[0m"),
    "INFO"     : ("\x1b[38;5;15m","\x1b[0m"),
    "WARNING"  : ("\x1b[38;5;3m","\x1b[0m"),
    "ERROR"    : ("\x1b[38;5;1m","\x1b[0m"),
    "CRITICAL" : ("\x1b[38;5;1m","\x1b[0m"),
    }

# Piped subprocess
def my_subprocess(commands):
    ps = {}
    i = 0
    for c in commands:
        if i:
            log("INFO", "executing piped command #%s '%s'"%(i,c), ('my_subprocess', 'utils'))
            ps[i] = subprocess.Popen(c, stdin=ps[i-1].stdout, stdout=subprocess.PIPE)
        else:
            log("INFO", "executing command '%s'"%(c), ('my_subprocess', 'utils'))
            ps[i] = subprocess.Popen(c, stdout=subprocess.PIPE)
        i += 1
    i = 0
    while i < len(ps)-1:
        ps[i].stdout.close()
        i += 1
    output,err = ps[i].communicate()
    if err: log("WARNING", "command error:\n%s"%(err), ('my_subprocess', 'utils'))
    if not output: return ""
    return (output[:len(output)-1] if output[len(output)-1] == '\n' else output)

# Custom logging
def log(action, content, fc=None):
    out = ""
    if logging.getLogger().getEffectiveLevel() == DEBUG:
        time.sleep(DEBUG_DELAY)
    if fc and logging.getLogger().getEffectiveLevel() == DEBUG:
        (f,c) = fc
        c = (c.__class__.__name__ if ((type(c) is not str) and c) else c)
        out += ("%s.%s(): "%(c,f)
                if c
                else "%s(): "%(f))
    pt = ("%s%s"%(out,content)
          if not COLOR and (logging.getLogger().getEffectiveLevel() is not DEBUG)
          else "%s%s%s%s"%(COLORS_EQ[action][0],out,content,COLORS_EQ[action][1]))
    LOGGING_EQ[action](pt)

# convert data from unicode to string
def uni2str(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(uni2str, data.iteritems()))
    elif isinstance(data, collections.Iterable):
    	return type(data)(map(uni2str, data))
    else:
        return data

# bootstrap modules config
def bootstrap_mod(config):
    bootstrap = os.path.join(config["module"]["root"],config["module"]["name"],config["module"]["bootstrap"])
    if not os.path.isfile(bootstrap):
        log("INFO", "No bootstrap script for modules in %s"%(bootstrap),('bootstrap_mod','utils'))
        return
    try:
        c_path = (config["runtime"]["config_path"] if config["runtime"].get("config_path") else "")
        r = subprocess.check_call("bash {0} {1}".format(bootstrap,c_path).split(" "))
        log("INFO", "Modules bootstrap succeed (%s): %s"%(bootstrap,r),('bootstrap_mod','utils'))
    except Exception as e:
        log("WARNING", "Can't bootstrap modules (%s): %s"%(bootstrap,r),('bootstrap_mod','utils'))

# clone a git repository
def clone_repo(config, path, name, uri):
    try:
        try:
            shutil.rmtree(os.path.join(path,name))
        except Exception as e:
            log("DEBUG", "Exception while removing directory %s: %s"%(os.path.normpath(path+'/'+name),e),('clone_repo','utils'))
        r = subprocess.check_call(["git","clone",uri,name],cwd=path)
        log("INFO", "repo %s from %s successfully cloned in %s: %s"%(name,uri,path,r),('clone_repo','utils'))
        try:
            os.unlink(os.path.join(config['global']['package_path'],config['module']['name']))
        except Exception as e:
            log("DEBUG", "Exception while unlinking %s: %s"%(os.path.join(config['global']['package_path'],config['module']['name']),e),('clone_repo','utils'))
        os.symlink(os.path.join(path,name,config['module']['src_salt']),os.path.join(config['global']['package_path'],config['module']['name']))
        try:
            os.unlink(os.path.join(config['global']['package_path'],config['module']['dst_adaptor']))
        except Exception as e:
            log("DEBUG", "Exception while unlinking %s: %s"%(os.path.join(config['global']['package_path'],config['module']['dst_adaptor']),e),('clone_repo','utils'))
        os.symlink(os.path.join(path,name,config['module']['src_adaptor']),os.path.join(config['global']['package_path'],config['module']['dst_adaptor']))
    except Exception as e:
        log("ERROR", "Can't clone %s repo from %s: %s"%(name,uri,e),('clone_repo','utils'))
        raise ManagerInvalidStatesRepoException
    return True

# clone a git branch/tag
def checkout_repo(config, path, name, tag, uri, n=0):
    commands = [
        ["git","checkout","master"],
        ["git","pull"],
        ["git","checkout",tag],
        ]
    spath = os.path.join(path,name)
    for cmd in commands:
        try:
            r = subprocess.check_call(cmd,cwd=spath)
            log("INFO", "Command succeed %s: %s"%(" ".join(cmd),r),('checkout_repo','utils'))
        except Exception as e:
            log("WARNING", "Can't update %s repo on %s tag: %s"%(name,tag,e),('checkout_repo','utils'))
            clone_repo(config, path, name, uri)
            if n == 0:
                checkout_repo(config, path, name, tag, uri, n+1)
            else:
                log("ERROR", "Can't switch to requested tag after cloning clean repo, aborting",('checkout_repo','utils'))
                raise ManagerInvalidStatesRepoException
            break
    if n == 0:
        log("INFO", "Repo %s in %s successfully checkout at %s tag"%(name,spath,tag),('checkout_repo','utils'))
    return True


# ensure states compatibility
class CompatMatrix():
    def __init__(self):
        self.__m = {}
        self.__map = {
            '>': self.gt,
            '>=': self.ge,
            '<=': self.le,
            '<': self.lt,
            '==': self.eq,
            '!=': self.ne,
            }

    def add(self, sign, version):
        if self.__map.get(sign):
            self.__map[sign](version)

    def gt(self, version):
        self.__m.setdefault(version,{})
        self.__m[version]['gt'] = True

    def ge(self, version):
        self.__m.setdefault(version,{})
        self.__m[version]['gt'] = True
        self.__m[version]['eq'] = True

    def le(self, version):
        self.__m.setdefault(version,{})
        self.__m[version]['lt'] = True
        self.__m[version]['eq'] = True

    def lt(self, version):
        self.__m.setdefault(version,{})
        self.__m[version]['lt'] = True

    def eq(self, version):
        self.__m.setdefault(version,{})
        self.__m[version]['eq'] = True

    def ne(self, version):
        self.__m.setdefault(version,{})
        self.__m[version]['ne'] = True

    def check(self, version):
        if self.__m.get(version):
            if self.__m[version].get('ne'):
                return False
            elif self.__m[version].get('eq'):
                return True
        for item in self.__m:
            if item < version:
                if self.__m[item].get('lt'): return False
            elif item > version:
                if self.__m[item].get('gt'): return False
        for item in self.__m:
            if item < version:
                if self.__m[item].get('gt'): return True
            elif item > version:
                if self.__m[item].get('lt'): return True
        return False


def compat_checker(version, compat):
    m = CompatMatrix()
    try:
        f = file(compat,'r')
        for l in f:
            l = l.strip()
            if not l:
                continue
            l = l.split()
            m.add(l[0],l[1])
    except Exception as e:
        log("WARNING", "can't read compatibily file %s: %s"%(compat,e),('compat_checker','utils'))
        return False
    res = m.check(version)
    if res:
        log("INFO", "Curent version %s compatible with states"%(version),('compat_checker','utils'))
    else:
        log("WARNING", "Curent version %s NOT compatible with states"%(version),('compat_checker','utils'))
    return res

# update config file value
def update_config_file(config, key, value):
    try:
        with open(config['runtime']['config_path'], 'r+') as f:
            content = re.sub(r"%s=(.*)\n"%(key),"%s=%s\n"%(key,value),f.read())
            f.seek(0)
            f.write(content)
    except Exception as e:
        log("WARNING",
            "Can't save %s in config file '%s': %e"%(key,config['runtime']['config_path'],e),('update_config_file','utils'))
        return False
    return True

# reset token file
def reset_token(config):
    commands = [
        ["rm","-f",config['global']['token']],
        ["ssh-keygen","-b","2048","-q","-P","","-f",config['global']['token']],
        ["rm","-f","%s.pub"%(config['global']['token'])],
        ["chown","%s:root"%(config['global']['user']),config['global']['token']],
        ["chmod","400",config['global']['token']],
    ]
    for cmd in commands:
        try:
            r = subprocess.check_call(cmd)
            log("INFO", "Command succeed %s: %s"%(" ".join(cmd),r),('reset_token','utils'))
        except Exception as e:
            log("WARNING", "Can't run command '%s': %s"%(cmd,e),('reset_token','utils'))
            return False
    log("INFO", "Token updated",('reset_token','utils'))
    return True
