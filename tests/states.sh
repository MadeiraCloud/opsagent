#!/bin/bash
# States Unit Tests bridge

TEST_DIR="/opt/visualops"
cd ${TEST_DIR}/bootstrap/salt
git checkout develop
git stash
git pull
cd test
./run.sh 3
