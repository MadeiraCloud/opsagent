#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

OA_CONF_FILE=/etc/opsagent.conf
OA_CONF_DIR=/etc/opsagent.d
OA_LOG_DIR=/var/log/madeira
OA_TMP_ROOT=/tmp/opsagent
OA_ROOT_DIR=/opt/madeira
OA_REMOTE=https://s3.amazonaws.com/visualops

# DEBUG
OA_SALT_DIR=/opt/madeira/bootstrap
OA_SALT_REPO=https://github.com/MadeiraCloud/salt.git
OA_SALT_BRANCH=develop
OA_ENV_DIR=$OA_ROOT_DIR/env
OA_BOOT_DIR=$OA_ROOT_DIR/bootstrap
OA_SALT=salt

if [ $(which python2.7 2>/dev/null) ]; then
    echo "python 2.7 found"
    PYTHON="python2.7"
elif [ $(which python2.6 2>/dev/null) ]; then
    echo "python 2.6 found"
    PYTHON="python2.6"
else
    echo "Fatal: Python2 non installed"
    exit 1
fi

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
rm -rf ${OA_ROOT_DIR}
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

    cd $OA_SALT_DIR
    rm -rf $OA_SALT
    git clone $OA_SALT_REPO $OA_SALT
    cd $OA_SALT
    git checkout $OA_SALT_BRANCH
    rm -f ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/salt
    ln -s ${OA_BOOT_DIR}/${OA_SALT}/sources/salt ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/salt
    rm -f ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/opsagent/state/adaptor.py
    ln -s ${OA_BOOT_DIR}/${OA_SALT}/sources/adaptor.py ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/opsagent/state/adaptor.py
fi


exit 0
# EOF
