#!/bin/bash
# States Unit Tests bridge

TEST_DIR="/opt/visualops"
O_PWD=$PWD
service opsagentd status
STATUS=$?
service opsagentd stop
cd ${TEST_DIR}/bootstrap/salt
git checkout develop
git stash
if [ $? -ne 0 ]; then
    git config --global user.email "root@localhost"
    git config --global user.name "root"
fi
git pull
cd ${TEST_DIR}/bootstrap/salt/tests
./run.sh 1
./run.sh 3
./run.sh 2
cd $O_PWD
rm -f ${TEST_DIR}/bootstrap/salt/tests
ln -s ${TEST_DIR}/bootstrap/salt/tests tests
chmod 777 tests
if [ $STATUS -eq 0 ]; then
    service opsagentd start
fi
