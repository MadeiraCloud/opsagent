#!/usr/bin/env python

# using gevent for event loop and greenlet scheduling
import gevent
from gevent.threadpool import ThreadPool

# using salt for provisioning
from salt.state  import HighState, State
from salt.minion import SMinion

#for test only
import json

class StateRunException(Exception):
    pass

class StateRunner(object):

    DEFAULT_POOL_SIZE = 2

    def __init__(self, states = [], pool_size = DEFAULT_POOL_SIZE):
        self._pool = ThreadPool(pool_size)

        if not type(states) == list:
            raise StateRunException('No state list to run')

        self._states = states

        self.highstate = None
        self.state =None
        self._init_state()
        #print self.highstate.avail

    def run(self):
        for state in self._states:
            ret = self._pool.spawn(self.state.call_high, state)
            gevent.wait()

            print json.dumps(ret.get(), sort_keys=True,
                  indent=4, separators=(',', ': '))

    def _init_state(self):
        
        def init_state():
            salt_opts = {
                'file_client':       'local',
                'renderer':          'yaml_jinja',
                'failhard':          False,
                'state_top':         'salt://top.sls',
                'nodegroups':        {},
                'file_roots':        {'base': ['/srv/salt']},
                'state_auto_order':  False,
                'extension_modules': '/var/cache/salt/minion/extmods',
                'id':                '',
                'pillar_roots':      '',
                'cachedir':          '/code/OpsAgent/cache',
                'test':              False,
                }
            
            self.state = State(salt_opts)

            print json.dumps(salt_opts, sort_keys=True,
                  indent=4, separators=(',', ': '))

        self._pool.spawn(init_state)
        gevent.wait()

# codes for test
def main():
    predefine_states = {
        'mypackages' : {
            '__env__': 'base',
            '__sls__': 'madeira',
            'pkg' : [
                {
                    'pkgs': [
                        'cowsay',
                    ],
                },
                'installed',
                {
                    'order': 10000
                }
            ]
        },
    }

    clean_up_states = {
        'cleanpkgs' : {
            '__env__': 'base',
            '__sls__': 'madeira',
            'pkg' : [
                {
                    'pkgs': [
                        'cowsay',
                    ],
                },
                'purged',
                {
                    'order': 10000
                }
            ]
        }
    }

    runner = StateRunner([predefine_states, clean_up_states])
    runner.run()

if __name__ == '__main__':
    main()