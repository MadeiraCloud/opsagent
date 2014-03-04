#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

DOA_CONF_FILE=/etc/opsagent.conf
DOA_CONF_DIR=/var/lib/madeira/opsagent
DOA_LOG_DIR=/var/log/madeira
DOA_TMP_ROOT=/tmp/opsagent
DOA_ROOT_DIR=/opt/madeira
DOA_REMOTE=https://s3.amazonaws.com/visualops

# DEBUG
DOA_SALT_DIR=/opt/madeira/bootstrap
DOA_SALT_REPO=https://github.com/MadeiraCloud/salt.git
DOA_SALT_BRANCH=develop
DOA_ENV_DIR=$DOA_ROOT_DIR/env
DOA_BOOT_DIR=$DOA_ROOT_DIR/bootstrap
DOA_SALT=salt

if [ $(which python2.7 2>/dev/null) ]; then
    echo "python 2.7 found"
    D_PYTHON="python2.7"
elif [ $(which python2.6 2>/dev/null) ]; then
    echo "python 2.6 found"
    D_PYTHON="python2.6"
else
    echo "Fatal: Python2 non installed"
    exit 1
fi

(crontab -l | grep -v ${DOA_CONF_DIR}/cron.sh) > /tmp/opsagent.crontab
crontab -r
cat /tmp/opsagent.crontab | crontab
service opsagentd stop
for id in `ps aux | grep opsagent | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
    kill -9 $id
done

rm -rf ${DOA_CONF_FILE}
rm -rf ${DOA_CONF_DIR}
rm -rf ${DOA_LOG_DIR}
rm -rf ${DOA_ROOT_DIR}
rm -rf ${DOA_TMP_ROOT}*

if [ "$1" = "reinstall" ]; then
    curl -sSL ${DOA_REMOTE}/userdata.sh | bash
fi

if [ "$2" = "debug" ]; then
    (crontab -l | grep -v ${DOA_CONF_DIR}/cron.sh) > ${DOA_TMP_ROOT}.crontab
    crontab -r
    cat ${DOA_TMP_ROOT}.crontab | crontab
    . ${DOA_CONF_DIR}/cron.sh
    service opsagentd stop
    for id in `ps aux | grep opsagent | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
        kill -9 $id
    done
    rm -rf ${DOA_TMP_ROOT}*
    if [ $(which chkconfig) ]; then
        chkconfig --del opsagentd
    elif [ $(which update-rc.d) ]; then
        update-rc.d opsagentd disable
    else
        echo "Fatal: no service manager"
        exit 1
    fi

    cd $DOA_SALT_DIR
    rm -rf $DOA_SALT
    git clone $DOA_SALT_REPO $DOA_SALT
    cd $DOA_SALT
    git checkout $DOA_SALT_BRANCH
    rm -f ${DOA_ENV_DIR}/lib/${D_PYTHON}/site-packages/salt
    ln -s ${DOA_BOOT_DIR}/${DOA_SALT}/sources/salt ${DOA_ENV_DIR}/lib/${D_PYTHON}/site-packages/salt
    rm -f ${DOA_ENV_DIR}/lib/${D_PYTHON}/site-packages/opsagent/state/adaptor.py
    ln -s ${DOA_BOOT_DIR}/${DOA_SALT}/sources/adaptor.py ${DOA_ENV_DIR}/lib/${D_PYTHON}/site-packages/opsagent/state/adaptor.py
fi


exit 0
# EOF
