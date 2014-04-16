'''
VisualOps agent requests objects
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''


# Protocol defines import
from opsagent.objects import codes


# Handshake request
def handshake(config, errors):
    init = config.get('init')
    version = (config['userdata'].get('version') if config.get('userdata') else None)
    if type(init) is not dict: init={}
    return ({
        "code"             :   codes.HANDSHAKE,
        "instance_id"      :   init.get('instance_id'),
        "app_id"           :   init.get('app_id'),
        "agent_version"    :   version,
        "protocol_version" :   codes.PROTOCOL_VERSION,
        "instance_token"   :   init.get('instance_token'),
        "init_errors"      :   ("; ".join(errors) if errors else None),
    })


# Statelog request
def statelog(init, version, sid, result, comment, out_log):
    return ({
            "code"           :   codes.STATELOG,
            "instance_id"    :   init.get('instance_id'),
            "app_id"         :   init.get('app_id'),
            "recipe_version" :   version,
            "id"             :   sid,
            "state_result"   :   result,
            "state_comment"  :   comment,
            "state_stdout"   :   out_log
            })
