'''
Madeira OpsAgent utilities

@author: Thibault BRONCHAIN
'''


# System imports
import logging
import time

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
def uni2str(self, data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(self.__convert, data.iteritems()))
    # elif isinstance(data, collections.Iterable):
    # 	return type(data)(map(self.__convert, data))
    else:
        return data
