#!/bin/bash
# OpsAgent Unit Tests

echo
echo "**** TESTS BEGIN ****"
echo

echo
echo "Requirements: ws4py, cherrypy"
echo

TEST_DIR="/tmp/visualops"

rm -rf $TEST_DIR
mkdir -p $TEST_DIR \
      $TEST_DIR/env/site-packages \
      $TEST_DIR/bootstrap/opsagent/scripts \
      $TEST_DIR/env/var/cache/pkg \
      $TEST_DIR/env/srv/salt \
      $TEST_DIR/env/var/cache/salt/minion/extmods \
      $TEST_DIR/env/var/cache/visualops \
      $TEST_DIR/log \
      $TEST_DIR/watch

echo -n "testtoken" > $TEST_DIR/opsagent.token

echo "Enter sudo password to create conf directory"
sudo mkdir -p /var/lib/visualops/opsagent

export PYTHONPATH=${PYTHONPATH}:$PWD/../sources:$TEST_DIR/env/site-packages

echo
echo "-----> Basic Unit Tests Begin <-----"
python checksum.py
CHECKSUM_RES=$?
python config.py
CONFIG_RES=$?
echo "-----> Basic Unit Tests End <-----"
echo

echo
echo "-----> Start Test Web Server <-----"
python ws_server.py &
sleep 6
echo "-----> Test Web Server Started <-----"
echo

echo
echo "-----> Manager Unit Tests Begin <-----"
python manager.py
MANAGER_RES=$?
echo "-----> Manager Unit Tests End <-----"
echo

echo
echo "-----> Stop Test Web Server <-----"
kill -9 $(ps x | sed -e 's/^[[:space:]]*//' | grep -i "python ws_server.py" | grep -v grep | cut -d ' ' -f 1)
sleep 1
echo "-----> Test Web Server Stopped <-----"
echo

echo "Run Worker Tests? [y/N]"
read RUN
WORKER_RES=-1
if [ "$RUN" = "y" ]; then
    echo
    echo "-----> Worker Unit Tests Begin <-----"
    sudo -E python worker.py
    WORKER_RES=$?
    echo "-----> Worker Unit Tests End <-----"
    echo
else
    echo "-- Not running Worker tests --"
fi


echo
echo "**** TESTS END ****"
echo

echo
echo "**** RESULTS ****"
echo
if [ $CHECKSUM_RES -eq 0 ]; then
    echo "Checksum test succeed!"
else
    echo "Checksum test failed!"
fi
if [ $CONFIG_RES -eq 0 ]; then
    echo "Config test succeed!"
else
    echo "Config test failed!"
fi
if [ $MANAGER_RES -eq 0 ]; then
    echo "Manager test succeed!"
else
    echo "Manager test failed!"
fi
if [ $WORKER_RES -eq 0 ]; then
    echo "Worker test succeed!"
elif [ $WORKER_RES -eq -1 ]; then
    echo "Worker test untested."
else
    echo "Worker test failed!"
fi
echo
echo "**** RESULTS END ****"
echo
