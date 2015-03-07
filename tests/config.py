'''
VisualOps agent Configuration manager Unit Tests
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''

import ut

import opsagent
from opsagent.config import Config

c_test = {
    "global" : {
        "platform":"YUM",
        "envroot":"/tmp/visualops/env",
        "conf_path":"/var/lib/visualops/opsagent",
        "log_path":"/tmp/visualops/log",
        "package_path":"/tmp/visualops/env/site-packages",
        "scripts_path":"/tmp/visualops/bootstrap/opsagent/scripts",
        "token":"/tmp/visualops/opsagent.token",
        "user":"root",
        "watch":"/tmp/visualops/watch",
        "logfile":"/tmp/visualops/log/agent.log",
        'pidfile': '/tmp/opsagentd.pid',
        'haltfile': '/tmp/opsagentd.halt',
    },
    "userdata" : {
        "ws_uri":"ws://127.0.0.1:9000/agent/",
        "app_id":"app-id",
        "version":"1.0",
        "base_remote":"https://s3.amazonaws.com/opsagent",
        "gpg_key_uri":"https://s3.amazonaws.com/opsagent/madeira.gpg.public.key",
    },
    "module" : {
        "root":"/tmp/visualops/bootstrap",
        "name":"salt",
        "bootstrap":"scripts/bootstrap.sh",
        "mod_repo":"https://github.com/MadeiraCloud/salt.git",
        "mod_tag":"v2015-02-27",
    },
    'salt': {
        'pkg_cache': '/tmp/visualops/env/var/cache/pkg',
        'srv_root': '/tmp/visualops/env/srv/salt',
        'extension_modules': '/tmp/visualops/env/var/cache/salt/minion/extmods',
        'cachedir': '/tmp/visualops/env/var/cache/visualops',
    },
    'network': {
        'get_retry': '1'
    },
}

def run():
    c = Config("opsagent.conf")
    c.parse_file()
    f = c.getConfig()
    ref = dict(Config.defaultValues.items() + c_test.items())
    for cat in ref:
        print "Testing category '%s' ..."%cat
        if not f.get(cat):
            print "Invalid category '%s'"%(cat)
            return -1
        for key in ref[cat]:
            if f[cat].get(key) != ref[cat][key]:
                print "Invalid value (%s/%s), should be '%s', got '%s'"%(cat,key,ref[cat][key],f[cat].get(key))
                return -1
    return 0

if __name__ == '__main__':
    exit(ut.ut(run,__file__))
