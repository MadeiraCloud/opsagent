'''
Madeira OpsAgent exceptions

@author: Thibault BRONCHAIN
'''


# Custom imports
from opsagent import utils


# Configuration Parser exceptions
class ConfigFileFormatException(Exception): pass
class ConfigFileException(Exception): pass

# Network exceptions
class NetworkConnectionException(Exception): pass

# AWS exception
class AWSNotFoundException(Exception): pass

# Manager exceptions
class ManagerInvalidStateFormatException(Exception): pass
class ManagerInvalidWaitFormatException(Exception): pass
class ManagerInitDirDeniedException(Exception): pass

# StatesWorker exceptions
class SWWaitFormatException(Exception): pass
class SWNoManagerException(Exception): pass
class SWNoWaitFileException(Exception): pass

# State exceptions
class StateException(Exception): pass

# General Exception
class OpsAgentException(Exception): pass


# Decorators
def GeneralException(func):
    def __action_with_decorator(self, *args, **kwargs):
        try:
            class_name = self.__class__.__name__
            func_name = func.__name__
            return func(self, *args, **kwargs)
        except Exception as e:
            utils.log("ERROR", "Uncaught error '%s'"%(str(e)),(func_name,class_name))
            raise OpsAgentException, e
    return __action_with_decorator

def ThrowNoException(func):
    def __action_with_decorator(self, *args, **kwargs):
        try:
            class_name = self.__class__.__name__
            func_name = func.__name__
            return func(self, *args, **kwargs)
        except Exception as e:
            utils.log("ERROR", "Uncaught error '%s'"%(str(e)),(func_name,class_name))
    return __action_with_decorator
