'''
Madeira OpsAgent network objects

@author: Thibault BRONCHAIN
'''


# State request object
stateRequest = {
    "type": "getstate",
    "content": {
        "state_req": None,
        "state_end": None,
	}
    }

# Meta request object
metaRequest = {
    "type": "getmeta",
    "content": None,
    }
