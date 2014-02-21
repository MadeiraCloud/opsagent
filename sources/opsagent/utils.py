'''
Madeira OpsAgent utilities

@author: Thibault BRONCHAIN
'''

# System imports
import logging
import time
import collections
import subprocess
import os

# Custom imports
from opsagent.exception import ManagerInvalidStatesRepoException

# Defines
DEBUG_DELAY=0.1
DEBUG=10
COLOR=True

# Logging defines
LOGGING_EQ = {
    "DEBUG"   : logging.debug,
    "INFO"    : logging.info,
    "WARNING" : logging.warning,
    "ERROR"   : logging.error
    }

# Colors defines
COLORS_EQ = {
    "DEBUG"   : ("\x1b[38;5;6m","\x1b[0m"),
    "INFO"    : ("\x1b[38;5;15m","\x1b[0m"),
    "WARNING" : ("\x1b[38;5;3m","\x1b[0m"),
    "ERROR"   : ("\x1b[38;5;1m","\x1b[0m"),
    }


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
def clone_repo(path, name, uri):
    try:
        subprocess.check_output(("git clone %s %s"%(uri,name)).split(),cmd=path)
    except Exception as e:
        log("ERROR", "Can't clone %s repo from %s: %s"%(name,uri,e),('clone_repo','utils'))
        raise ManagerInvalidStatesRepoException
    return True

# clone a git branch/tag
def checkout_repo(path, name, tag, uri, n=0):
    commands = [
        "git reset --hard FETCH_HEAD",
        "git clean -df",
        "git pull",
        "git checkout %s"%(tag),
        "git pull",
        ]
    path = os.path.normpath(path+'/'+name)
    for cmd in commands:
        try:
            subprocess.check_output(cmd.split(),cmd=path)
        except Exception as e:
            log("WARNING", "Can't update %s repo on %s tag: %s"%(name,tag,e),('checkout_repo','utils'))
            clone_repo(path, name, uri)
            if n == 0:
                checkout_repo(path, name, tag, uri, n+1)
            else:
                log("ERROR", "Can't switch to requested after cloning clean repo, aborting.",('checkout_repo','utils'))
                raise ManagerInvalidStatesRepoException
            break
