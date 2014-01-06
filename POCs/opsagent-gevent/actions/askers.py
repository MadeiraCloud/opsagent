'''
Madeira OpsAgent askers actions

@author: Thibault BRONCHAIN
'''


# System imports
import copy

# Custom imports
import opsagent.utils
from opsagent.network.objects import *


# Ask new state
def askState(socket, done, state):
    utils.log("INFO", "Reporting end of state %s, asking for states %s"%(done,state))
    object = copy.deepcopy(stateRequest)
    object["content"]["state_req"] = state
    object["content"]["state_end"] = done
    socket.send(object)

# Ask for metadatas
def askMeta(socket):
    utils.log("INFO", "Asking for metadatas")
    object = copy.deepcopy(metaRequest)
    socket.send(object)
