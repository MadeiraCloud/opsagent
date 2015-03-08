#!/bin/bash
# States Unit Tests bridge

TEST_DIR="/opt/visualops"
service opsagentd status
STATUS=$?
service opsagentd stop
cd ${TEST_DIR}/bootstrap/salt
git checkout develop
git stash
git pull
cd ${TEST_DIR}/bootstrap/salt/test
./run.sh 3
if [ $STATUS -eq 0 ]; then
    service opsagentd start
fi
