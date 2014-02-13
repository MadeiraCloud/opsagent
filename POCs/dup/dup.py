
import subprocess
import os
import sys
import select
import datetime

class Stream():
    def __init__(self, name, fd):
        self.__name = name
        self.__fd = fd
        self.__buf = ''
        self.__rows = []
        self.__BUF_SIZE = 4096

    def name(self):
        return self.__name

    def rows(self):
        return self.__rows

    def fileno(self):
        return self.__fd.fileno()

    def read(self, end=False, i=0):
        while True:
            buf = os.read(self.fileno(), self.__BUF_SIZE)
            if not buf:
                break
            if '\n' in buf:
                buf = self.__buf + buf
                (tmp,s) = buf.rsplit('\n', 1)
                self.__buf = s
                now = datetime.datetime.now().isoformat()
                rows = tmp.split('\n')
                for r in rows:
                    self.__rows.append((i, now, self.__name, r))
                    i += 1
            else:
                self.__buf += buf
            if not end:
                break
        return i


class Popen(subprocess.Popen):
    def __init__(self, *args, **argv):
        self.__timeout = 0.1
        self.__merged = None
        self.__i=0

        subprocess.Popen.__init__(self, *args, **argv)

        self.__streams = [
            Stream('stdout', self.stdout),
            Stream('stderr', self.stderr)
            ]

    def communicate(self):
        def __select(end=False):
            fds = select.select(self.__streams, [], [], self.__timeout)
            for stream in fds[0]:
                self.__i=stream.read(end,i=self.__i)

        while self.returncode is None:
            self.poll()
            __select(end=False)
        __select(end=True)

        out = {}
        tmp = []
        for stream in self.__streams:
            rows = stream.rows()
            tmp += rows
            out[stream.name()] = [r[3] for r in rows]
        tmp.sort()
        self.__merged = ["%s %s: %s"%(r[2],r[1],r[3]) for r in tmp]

        return ('\n'.join(out.get('stdout')),'\n'.join(out.get('stderr')))

    def merged(self):
        return '\n'.join(self.__merged)


p = Popen(['bash', 'dup.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(out,err) = p.communicate()
merged = p.merged()

print "err=%s"%err
print "out=%s"%out
print "merged=%s"%merged
sys.exit(0)


"""
def my_popen(args, **kwargs):
    dup = kwargs['dup']
    del kwargs['dup']
    (r,w) = os.pipe()
    f = file("out.log", 'a+')
    p = subprocess.Popen(args, **kwargs)
    print "go"
    out2 = os.fdopen(sys.stdout.fileno(), 'w', 0)
#    out2 = os.dup(p.stdout.fileno())
#    os.dup2(f.fileno(), p.stdout.fileno())
#    os.dup2(f.fileno(), out2)
    os.dup2(w, out2.fileno())
    print "toto"
#    os.close(p.stdout.fileno())
    dup.append(os.fdopen(r))
    return p
"""
