from multiprocessing import Process, Queue
import time

#import gevent

HEARTBEAT = 3

class NetworkConnector():
    def __init__(self):
        self.r = Queue()
        self.w = Queue()
        self.ri = Queue()
        self.ri.put(1)
        self.p = Process(target=self.loop, args=())
        self.p.start()

    def loop(self):
        timeout = HEARTBEAT
        while True:
            start = time.time()
            self.write()
            self.read()
            time.sleep(HEARTBEAT - (time.time()-start))

    #TODO
    def write(self):
        w = None
        try:
            w = self.w.get(False)
        except: pass
        print "write: %s\n"%(w)

    #TODO
    def read(self):
        s = self.ri.get()
        self.r.put("%s"%s)
        s += 1
        self.ri.put(s)

    def writeQueue(self, s):
        self.w.put(s)

    def readQueue(self):
        r = None
        try:
            r = self.r.get(False)
        except: pass
        return r

if __name__ == '__main__':
    n = NetworkConnector()
    i = 0
    while i < 5:
        n.writeQueue("test #%s"%(i))
        r = n.readQueue()
        print "read #%s: %s"%(i,r)
        time.sleep(1)
        i += 1
    while True:
        r = n.readQueue()
        print "read #%s: %s"%(i,r)
        time.sleep(1)
        i += 1
