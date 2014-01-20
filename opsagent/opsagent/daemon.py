'''
Madeira OpsAgent Daemoniser class

@author: Thibault BRONCHAIN
'''


# System imports
import sys
import os
import time
import atexit
from signal import SIGTERM,SIGINT,SIGKILL


# Daemon class
class Daemon():
    def __init__(self, config, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.config = config
        self.__pidfile = config['global']['pidfile']
        self.__stdin = stdin
        self.__stdout = stdout
        self.__stderr = stderr

    # delete pid file
    def delpid(self):
        os.remove(self.__pidfile)

    # make as daemon
    def daemonize(self):
        # first fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit parent (child of child is daemon)
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("Can't fork, err#%s: %s\n"%(e.errno,e.strerror))
            sys.exit(1)

        # change root
        os.chdir("/")
        # get parent id
        os.setsid()
        # disable coredump
        os.umask(0)

        # second fork (linux trick)
        try:
            pid = os.fork()
            if pid > 0:
                # exit second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("Can't fork, err#%s: %s\n"%(e.errno,e.strerror))
            sys.exit(1)

        # redirect outputs
        sys.stdout.flush()
        sys.stderr.flush()
        sin = file(self.__stdin, 'r')
        sout = file(self.__stdout, 'a+')
        serr = file(self.__stderr, 'a+', 0)
        os.dup2(sin.fileno(), sys.stdin.fileno())
        os.dup2(sout.fileno(), sys.stdout.fileno())
        os.dup2(serr.fileno(), sys.stderr.fileno())

        # delete pid file when exit
        atexit.register(self.delpid)
        # get pid
        pid = str(os.getpid())
        # write pid to file
        file(self.__pidfile,'w+').write("%s\n"%pid)

    # start as daemon
    def start(self):
        # check if already running
        try:
            fd = file(self.__pidfile,'r')
            pid = int(fd.read().strip())
            fd.close()
        except IOError:
            pid = None

        # if pid exists, daemon running, don't do anything
        if pid:
            sys.stderr.write("pidfile %s already exist. Daemon already running?\n"%(self.__pidfile))
            sys.exit(1)

        # start the daemon
        self.daemonize()
        self.run()

    # stop the daemon
    def stop(self, wait=False):
        # get pid from pidfile
        try:
            pf = file(self.__pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        # no file
        if not pid:
            sys.stderr.write("pidfile %s does not exist. Daemon not running?\n"%(self.__pidfile))
            return

        # kill daemon
        try:
            sig = (SIGTERM if wait else SIGKILL)
            while True:
                os.kill(pid, sig)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process"):
                if os.path.exists(self.__pidfile):
                    os.remove(self.__pidfile)
            else:
                sys.stderr.write("%s"%(err))
                sys.exit(1)

    # restart daemon
    def restart(self, wait=False):
        self.stop(wait)
        # don't go too fast ...
        time.sleep(1)
        self.start()

    # launcher
    def run(self):
        pass
