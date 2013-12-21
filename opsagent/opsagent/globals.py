'''
@author: Thibault BRONCHAIN
'''

# global
def init():
    global REQ
    REQ = {
        'jsonrpc':  '2.0',
        'id':       '1728A6D7-7871-405D-BE74-2EA302F139F9',
        'method':   'login',
        'params':   ['thibaultbronchain','Superdry0'],
        # REAL
        'instance_id'    : None,
        'states_version' : None,
        'current_states' : [],
        'wait_states'    : [],
        }
