'''
Madeira OpsAgent Metadata actions

@author: Thibault BRONCHAIN
'''


# Custom imports
import opsagent.utils
import askers


# Update curent metadatas
def updateMetadata(manager, data):
    # Ensure format
    def checkMetaFormat(data):
        if not data:
            utils.log("ERROR", "Server error, no metadata.")
            raise ManagerInvalidMetaFormatException
        elif not data.get("states_version"):
            utils.log("ERROR", "Server error, disformed data, version missing: '%s'"%(data))
            raise ManagerInvalidMetaFormatException
        utils.log("DEBUG", "Valid metadata received",('__checkMetaFormat','metadata'))

    checkMetaFormat(data)
    version = data["states_version"]
    
    # Update states
    if manager.getMeta() is None or (manager.getMeta().get("states_version") != version):
        old = (None if not manager.getMeta() else manager.getMeta()['version'])
        utils.log("INFO", "Curent version is %s, received version is %s, updating..."%(old,version))
        manager.interruptWorker()
        manager.setMeta(data)
        if manager.getMeta().get('current_states'):
            utils.log("DEBUG", "States found",('__updateMetadata','metadata'))
            askers.askState(manager.getSocket(), None, manager.updateCurentState())
    # States up to date
    else:
        utils.log("INFO", "States version already up to date, updating waiting states ...")
        beforeWait = manager.getMeta().get('wait_states')
        manager.setMeta(data,['wait_states'])
        utils.log("DEBUG", "Waiting states updated from '%s' to '%s'"%(beforeWait,manager.getMeta().get('wait_states')),("updateMetadata",'metadata'))
