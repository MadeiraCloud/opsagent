#!/bin/bash
# OpsAgent Unit Tests

echo
echo "**** TESTS BEGIN ****"
echo

TEST_DIR="/tmp/visualops"

#rm -rf $TEST_DIR
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
python config.py
echo "-----> Basic Unit Tests End <-----"
echo

echo
echo "-----> Start Test Web Server <-----"
python ws_server.py &
#sleep 6
echo "-----> Test Web Server Started <-----"
echo

echo
echo "-----> Manager Unit Tests Begin <-----"
#python manager.py
echo "-----> Manager Unit Tests End <-----"
echo

echo
echo "-----> Stop Test Web Server <-----"
kill -9 $(ps | grep -i "python ws_server.py" | grep -v grep | cut -d ' ' -f 1)
sleep 1
echo "-----> Test Web Server Stopped <-----"
echo

echo "Run Worker Tests? [y/N]"
read RUN
if [ "$RUN" = "y" ]; then
    echo
    echo "-----> Worker Unit Tests Begin <-----"
    python worker.py
    echo "-----> Worker Unit Tests End <-----"
    echo
else
    echo "-- Not running Worker tests --"
fi

echo
echo "**** TESTS BEGIN ****"
echo
