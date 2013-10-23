# gevent
import gevent
# gevent monkey patch
from gevent import monkey
monkey.patch_all()

# patched imports
import time
import json
import urllib2

# global
URI = "https://api.madeiracloud.com/session/"
REQ = {
    'jsonrpc':  '2.0',
    'id':       '1728A6D7-7871-405D-BE74-2EA302F139F9',
    'method':   'login',
    'params':   ['thibaultbronchain','Superdry0']
    }

class call():
    def __init__(self):
        self.res=None

    def worker(self, url):
        time.sleep(2)

    def run(self):
        print "first"
        job = gevent.spawn(self.worker, URI)
        print "second"
        job.join()
        print "res=%s"%self.res
        print "last"

c = call()
c.run()
