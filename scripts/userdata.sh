#!/bin/bash
## (c) 2014 MadeiraCloud LTD.

echo "$0: Bootstraping started"

export WS_URI=@{ws_uri}
export APP_ID=@{app_id}
export VERSION=@{version}
export BASE_REMOTE=@{remote}
export GPG_KEY_URI=@{gpg_key_uri}

python << ENDPYTHON
import os,sys,time,urllib2
def fork1():
    try:
        pid = os.fork()
        if pid > 0: sys.exit(0)
    except Exception as e: sys.exit(1)
fork1();os.chdir("/");os.setsid();os.umask(0);fork1()
while True:
    try: os.system(urllib2.urlopen('${BASE_REMOTE}/${VERSION}/ud_init.sh').read()); break
    except Exception as e: time.sleep(15)
ENDPYTHON

echo "$0: Bootstraping done."
