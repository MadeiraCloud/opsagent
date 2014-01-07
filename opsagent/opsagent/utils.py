'''
Madeira OpsAgent utilities

@author: Thibault BRONCHAIN
'''


# System imports
import logging
import time


# Logging defines
LOGGING_EQ = {
    "DEBUG"   : logging.debug,
    "INFO"    : logging.info,
    "WARNING" : logging.warning,
    "ERROR"   : logging.error
}


# Custom logging
def log(action, content, fc=None):
    if DEBUG_DELAY:
        time.sleep(DEBUG_DELAY)
    out = ""
    if fc and logging.getLogger().getEffectiveLevel() == logging.debug:
        (f,c) = fc
        c = (c.__class__.__name__ if type(c) is not str else c)
        out += ("%s.%s(): "%(c,f)
                if c
                else "%s(): "%(f))
    LOGGING_EQ[action]("%s%s"%(out,content))
