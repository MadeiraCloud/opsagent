#!/bin/sh

BASE_DIR=/opt/madeira/env/lib/python2.7/site-packages/opsagent/state
PY_BIN=/opt/madeira/env/bin/python
EXE_BIN=adaptor.py

echo ""
for line in `cat etc/module.lst | grep -v "#"`
do	
  echo `date '+%Y-%m-%d %H:%M:%S' `" - start test '${line}'"
  cp etc/json/${line}.json ../api.json
  cd ${BASE_DIR}
  ${PY_BIN} ${EXE_BIN} 1>test/rlt/${line}.out 2>test/rlt/${line}.err
  cd ${BASE_DIR}/test
done

echo ""
echo `date '+%Y-%m-%d %H:%M:%S' `" - all done"
echo ""
