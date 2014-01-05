'''
Madeira OpsAgent action selector

@author: Thibault BRONCHAIN
'''


# Custom imports
import metadata
import states


# Action selector
selector={
    "metadata": metadata.updateMetadata,
    "state": states.addState,
    }
