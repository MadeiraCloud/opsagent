#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

OA_CONF_DIR=/etc/opsagent.d
OA_LOG_DIR=/var/log/madeira
OA_TMP_ROOT=/tmp/opsagent
OA_REMOTE=https://s3.amazonaws.com/visualops

(crontab -l | grep -v ${OA_CONF_DIR}/cron.sh) > /tmp/opsagent.crontab
crontab -r
cat /tmp/opsagent.crontab | crontab
service opsagentd stop
for id in `ps aux | grep opsagent | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
    kill -9 $id
done

rm -rf ${OA_CONF_DIR}
rm -rf ${OA_LOG_DIR}
rm -rf ${OA_TMP_ROOT}*

if [ "$2" = "reinstall" ]; then
    curl -sSL ${OA_REMOTE}/userdata.sh | bash
fi

exit 0
# EOF
