#!/usr/bin/env python

# using gevent for event loop and greenlet scheduling
import gevent
from gevent.threadpool import ThreadPool

# using salt for provisioning
from salt.state  import State

class StateRunException(Exception):
    pass

class StateRunner(object):

    DEFAULT_POOL_SIZE = 2

    def __init__(self, opts, states = [], pool_size = DEFAULT_POOL_SIZE):
        self._pool = ThreadPool(pool_size)

        if not type(states) == list:
            raise StateRunException('No state list to run')

        self._opts   = opts
        self._states = states

        self.state =None
        self._init_state()

    def get_opts(self):
        return self._opts

    def set_states(self, states = []):
        if not type(states) == list:
            raise StateRunException('No state list to run')
        self._states = states

    def run(self):
        state_results = []
        for state in self._states:
            ret = self._pool.spawn(self.state.call_high, state)
            ret.wait()
            state_results.append(ret.get())
        return state_results

    def stop(self, timeout = None):
        pass

    def _init_state(self):
        ret = self._pool.spawn(lambda opts: State(opts), self._opts)
        ret.wait()
        self.state = ret.get()

# codes for test
def main():

    import json

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

    runner = StateRunner(salt_opts, [predefine_states, clean_up_states])
    print json.dumps(runner.get_opts(), sort_keys=True,
          indent=4, separators=(',', ': '))

    ret = runner.run()
    print json.dumps(ret, sort_keys=True,
          indent=4, separators=(',', ': '))

if __name__ == '__main__':
    main()