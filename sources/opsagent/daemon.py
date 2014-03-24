'''
VisualOps agent Daemoniser class
(c) 2014 - MadeiraCloud LTD.

@author: Thibault BRONCHAIN
'''


# System imports
import sys
import os
import time
import atexit
from signal import SIGTERM


# Daemon class
class Daemon():
    def __init__(self, config, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.sw = None
        self.config = config
        self.pidfile = config['global']['pidfile']
        self.haltfile = config['global']['haltfile']
        self.__stdin = stdin
        self.__stdout = stdout
        self.__stderr = stderr

    # delete pid file
    def __delpid(self):
        os.remove(self.pidfile)

    # make as daemon
    def __daemonize(self):
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
        # ensure file creation
        os.umask(0022)

        # second fork (linux daemon trick)
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
        atexit.register(self.__delpid)
        # get pid
        pid = str(os.getpid())
        # write pid to file
        file(self.pidfile,'w+').write("%s\n"%pid)
        os.chmod(self.pidfile, 0640)

    # start as daemon
    def start(self):
        # check if already running
        try:
            fd = file(self.pidfile,'r')
            pid = int(fd.read().strip())
            fd.close()
        except IOError:
            pid = None

        # if pid exists, daemon running, don't do anything
        if pid:
            pids = [int(tpid) for tpid in os.listdir(self.config['global']['proc']) if tpid.isdigit()]
            if pid in pids:
                sys.stderr.write("pidfile %s already exist. Daemon already running?\n"%(self.pidfile))
                sys.exit(1)
            else:
                os.remove(self.pidfile)

        # start the daemon
        self.__daemonize()
        self.run()

    # stop the daemon
    def stop(self, wait=False, end=False):
        # get pid from pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        # no file
        if not pid:
            sys.stderr.write("pidfile %s does not exist. Daemon not running?\n"%(self.pidfile))
            return

        # kill daemon
        try:
            if end:
                file(self.haltfile,'w+').write("end")
                os.chmod(self.haltfile, 0640)
            elif wait:
                file(self.haltfile,'w+').write("wait")
                os.chmod(self.haltfile, 0640)
            else:
                file(self.haltfile,'w+').write("kill")
                os.chmod(self.haltfile, 0640)
            while True:
                os.kill(pid, SIGTERM)
                time.sleep(1)
        except OSError, err:
            err = str(err)
            if err.find("No such process"):
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                sys.stderr.write("%s"%(err))
                sys.exit(1)

    # restart daemon
    def restart(self, wait=False, end=False):
        self.stop(wait, end)
        # don't go too fast ...
        time.sleep(1)
        self.start()

    # get daemon status
    def status(self):
        # get pid from pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            sys.stdout.write("OpsAgent not running\n")
            sys.exit(1)
        else:
            sys.stdout.write("OpsAgent running\n")
            sys.exit(0)

    # launcher
    def run(self):
        pass
