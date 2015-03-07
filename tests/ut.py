'''
VisualOps agent Unit Tests Framework
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def ut(func,f):
    print "==== %s UT starts ===="%f
    try:
        ret = func()
    except Exception as e:
        print "ERROR: %s"%e
        ret = -1
    print "--> test %s %s%s"%(colors.OKBLUE+f,
                              colors.OKGREEN+"SUCCEED" if not ret else colors.FAIL+"FAILED",
                              colors.ENDC)
    print "==== %s UT ends ===="%f
    return ret
