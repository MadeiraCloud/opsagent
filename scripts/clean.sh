#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

OA_CONF_FILE=/etc/opsagent.conf
OA_CONF_DIR=/etc/opsagent.d
OA_LOG_DIR=/var/log/madeira
OA_SRC_DIR=/opt/madeira
OA_TMP_ROOT=/tmp/opsagent
OA_REMOTE=https://s3.amazonaws.com/visualops
OA_SALT_DIR=/opt/madeira/bootstrap/salt

(crontab -l | grep -v ${OA_CONF_DIR}/cron.sh) > /tmp/opsagent.crontab
crontab -r
cat /tmp/opsagent.crontab | crontab
service opsagentd stop
for id in `ps aux | grep opsagent | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
    kill -9 $id
done

rm -rf ${OA_CONF_FILE}
rm -rf ${OA_CONF_DIR}
rm -rf ${OA_LOG_DIR}
rm -rf ${OA_SRC_DIR}
rm -rf ${OA_TMP_ROOT}*

if [ "$1" = "reinstall" ]; then
    curl -sSL ${OA_REMOTE}/userdata.sh | bash
fi

if [ "$2" = "debug" ]; then
    (crontab -l | grep -v ${OA_CONF_DIR}/cron.sh) > ${OA_TMP_ROOT}.crontab
    crontab -r
    cat ${OA_TMP_ROOT}.crontab | crontab
    . ${OA_CONF_DIR}/cron.sh
    service opsagentd stop
    for id in `ps aux | grep opsagent | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
        kill -9 $id
    done
    rm -rf ${OA_TMP_ROOT}*
    if [ $(which chkconfig) ]; then
        chkconfig --del opsagentd
    elif [ $(which update-rc.d) ]; then
        update-rc.d opsagentd disable
    else
        echo "Fatal: no service manager"
        exit 1
    fi
fi


exit 0
# EOF
