#!/usr/bin/env python
#import time

# using gevent for event loop and greenlet scheduling
#import gevent
from gevent import Greenlet 
from gevent.event import Event
#from gevent import monkey; monkey.patch_time()
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

        self._idle = Event()
        self._idle.set()

        self._stop = False

        self.state = None
        self._greenlet = None
        self._init_state()

    def get_opts(self):
        return self._opts

    def set_states(self, states = [], timeout = None):
        if not type(states) == list:
            raise StateRunException('No state list to run')
        if not self._idle().wait(timeout): 
            # Timeout -> set failed
            return False

        self._states = states
        return True

    def run(self):
        self._stop = False
        state_results = []
        
        for state in self._states:
            #state_results.append("run state! " + time.strftime('%H:%M:%S')) 
            ret = self._pool.spawn(self.state.call_high, state)
            state_results.append(ret.get())
            #state_results.append("get result " + time.strftime('%H:%M:%S')) 

            if self._stop:
                break

        
        return state_results

    def spawn(self):
        self._idle.wait()
        self._idle.clear()
        self._greenlet = Greenlet(self.run)
        self._greenlet.start()

    def wait(self):
        if self._idle.is_set():
            if self._greenlet.ready():
                return self._greenlet.value
            else:
                return None

        ret = self._greenlet.get()
        self._idle.set()
        return ret

    def stop(self, timeout = None):
        self._stop = True
        if not self._idle.wait(timeout):
            self._greenlet.kill(block=False)
            self._idle.set()
            return False
        return True

    def _init_state(self):
        ret = self._pool.spawn(lambda opts: State(opts), self._opts)
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
                    'refresh': False,
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

    runner.spawn()
    ret = runner.wait()
    #ret = runner.run()
    if ret:
        print json.dumps(ret, sort_keys=True,
              indent=4, separators=(',', ': '))
    else:
        print "wait failed"

if __name__ == '__main__':
    main()
