#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

DOA_CONF_FILE=/etc/opsagent.conf
DOA_CONF_DIR=/var/lib/visualops/opsagent
DOA_LOG_DIR=/var/log/visualops
DOA_TMP_ROOT=/tmp/opsagent
DOA_ROOT_DIR=/opt/visualops
DOA_BASE_REMOTE=https://s3.amazonaws.com/visualops
#DOA_VERSION=""
#DOA_REMOTE="${DOA_BASE_REMOTE}/${DOA_VERSION}"
EXIT=0

# DEBUG
DOA_SALT_DIR=/opt/visualops/bootstrap
DOA_SALT_REPO=https://github.com/MadeiraCloud/salt.git
DOA_SALT_BRANCH=develop
DOA_ENV_DIR=$DOA_ROOT_DIR/env
DOA_BOOT_DIR=$DOA_ROOT_DIR/bootstrap
DOA_SALT=salt

(crontab -l | grep -v ${DOA_CONF_DIR}) > /tmp/opsagent.crontab
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

if [ $(which chkconfig) ]; then
    chkconfig --del opsagentd
elif [ $(which update-rc.d) ]; then
    update-rc.d opsagentd disable
else
    echo "no service manager" >&2
fi

if [ "$1" = "reinstall" ]; then
    curl -sSL "http://169.254.169.254/latest/user-data" -o /tmp/userdata.sh
    if [ $? -ne 0 ]; then
        curl -sSL ${DOA_REMOTE}/userdata.sh -o /tmp/userdata.sh
    fi

    bash /tmp/userdata.sh
    EXIT=$?
    if [ $EXIT -eq 0 ] && [ "$2" = "debug" ]; then
        if [ $(which python2.7 2>/dev/null) ]; then
            echo "python 2.7 found"
            D_PYTHON="python2.7"
        elif [ $(which python2.6 2>/dev/null) ]; then
            echo "python 2.6 found"
            D_PYTHON="python2.6"
        else
            echo "Fatal: Python2 non installed" >&2
            exit 1
        fi

        (crontab -l | grep -v ${DOA_CONF_DIR}) > /tmp/opsagent.crontab
        crontab -r
        cat /tmp/opsagent.crontab | crontab
        bash ${DOA_CONF_DIR}/cron.sh
        EXIT=$?

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
            echo "no service manager" >&2
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
fi


exit $EXIT
# EOF
