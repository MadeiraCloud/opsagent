'''
Madeira OpsAgent utilities

@author: Thibault BRONCHAIN
'''

# System imports
import logging
import time
import subprocess
import os
import shutil
import collections

# Custom imports
from opsagent.exception import ManagerInvalidStatesRepoException


# Defines
DEBUG_DELAY=0
DEBUG=10
COLOR=True

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
          if not COLOR
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

# clone a git repository
def clone_repo(config, path, name, uri):
    try:
        try:
            shutil.rmtree(os.path.join(path,name))
        except Exception as e:
            log("DEBUG", "Exception while removing directory %s: %s"%(os.path.normpath(path+'/'+name),e),('clone_repo','utils'))
        r = subprocess.check_call(("git clone %s %s"%(uri,name)).split(),cwd=path)
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
        "git checkout master",
        "git pull",
        "git checkout %s"%(tag),
        ]
    spath = os.path.join(path,name)
    for cmd in commands:
        try:
            r = subprocess.check_call(cmd.split(),cwd=spath)
            log("INFO", "Command succeed %s: %s"%(cmd,r),('checkout_repo','utils'))
        except Exception as e:
            log("WARNING", "Can't update %s repo on %s tag: %s"%(name,tag,e),('checkout_repo','utils'))
            clone_repo(config, path, name, uri)
            if n == 0:
                checkout_repo(config, path, name, tag, uri, n+1)
            else:
                log("ERROR", "Can't switch to requested tag after cloning clean repo, aborting.",('checkout_repo','utils'))
                raise ManagerInvalidStatesRepoException
            break
    if n == 0:
        log("INFO", "Repo %s in %s successfully checkout at %s tag."%(name,spath,tag),('checkout_repo','utils'))
