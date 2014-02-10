#!/bin/bash

BASE_DIR=/opt/madeira/env/lib/python2.7/site-packages/opsagent/state
PY_BIN=/opt/madeira/env/bin/python
EXE_BIN=adaptor.py
DATA_FILE=api.json

if [ ! -d "${BASE_DIR}/test/rlt" ]
then
 echo "create rlt dir"
 mkdir -p ${BASE_DIR}/test/rlt
fi

echo "---------------------------------------------------------------"
for line in `cat etc/module.lst | grep -Ev "^#|^$" | awk '{print $1}'`
do	
  echo -e -n `date '+%Y-%m-%d %H:%M:%S' `" - start test '${line}'\t- "
  START_TIME=`date '+%s'`
  cp etc/json/${line}.json ../${DATA_FILE}
  cd ${BASE_DIR}
  if [ ! -f ${BASE_DIR}/${DATA_FILE} ]
  then
    echo "[error] can not found ${BASE_DIR}/${DATA_FILE}, cancel"
    break
  fi
  ${PY_BIN} ${EXE_BIN} 1>test/rlt/${line}.out 2>test/rlt/${line}.err
  END_TIME=`date '+%s'`
  #check result
  OUT_=`cat test/rlt/${line}.out|wc -l`
  ERR_=`cat test/rlt/${line}.err|wc -l`
  echo -e `expr ${END_TIME} - ${START_TIME}`"s\tout: ${OUT_}\t  err: ${ERR_}"
  cd ${BASE_DIR}/test
done

echo "---------------------------------------------------------------"
echo `date '+%Y-%m-%d %H:%M:%S' `" - all done"
echo "see detail log in rlt dir"
echo ""

