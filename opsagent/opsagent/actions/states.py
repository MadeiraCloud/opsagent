'''
Madeira OpsAgent States actions

@author: Thibault BRONCHAIN
'''


# Custom imports
import opsagent.utils
import askers


# Execute state
def addState(manager, data):
    # Ensure state validity
    def checkStateFormat(data):
        if data.get("state_id") == None:
            utils.log("ERROR", "Invalid state format: no ID found")
            raise ManagerInvalidStateFormatException
        elif data.get("content") == None:
            utils.log("ERROR", "Invalid state format: no content found")
            raise ManagerInvalidStateFormatException
        utils.log("DEBUG", "Valid state received",('__checkStateFormat','states'))

    checkStateFormat(data)
    id = data["state_id"]
    if id != manager.getCurentState():
        raise ManagerInvalidStateIdException
    utils.log("INFO", "Starting curent state '%s'"%(id))
    manager.setWorker(gevent.spawn(manager.startWorker, id, data["content"]))
