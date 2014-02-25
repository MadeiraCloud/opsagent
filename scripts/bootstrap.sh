#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# setup dependencies
if [ $(which apt-get 2>/dev/null) ]; then
    # install python
    echo "Platform: APT"
    apt-get -y -q install python2.7
    if [ $? -ne 0 ]; then
        echo "Failed to install python 2.7, trying with python 2.6 ..."
        apt-get -y -q install python2.6
    fi
    # install other dependencies
    apt-get -y -q install python-apt expect-dev
elif [ $(which yum 2>/dev/null) ]; then
    # install python
    echo "Platform: YUM"
    yum -y -q install python27
    if [ $? -ne 0 ]; then
        echo "Failed to install python 2.7, trying with python 2.6 ..."
        yum -y -q install python26
    fi
    # install other dependencies
    yum -y -q install expect yum-utils
fi
# define python version
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


# Generates config file
if [ ! -f ${OA_CONFIG_FILE} ]; then
    cat <<EOF > ${OA_CONFIG_FILE}
[global]
envroot=${OA_ENV_DIR}
package_path=${OA_ENV_DIR}/lib/${PYTHON}/site-packages
token=${OA_TOKEN}
watch=${OA_WATCH_DIR}
logfile=${OA_LOG_FILE}
[network]
ws_uri=${WS_URI}
app_id=${APP_ID}
[module]
root=${OA_BOOT_DIR}
name=${OA_SALT}
bootstrap=${SRC_SCRIPTS_DIR}/bootstrap.sh
mod_repo=
mod_tag=
EOF
fi
chown ${OA_USER}:root ${OA_CONFIG_FILE}
chmod 640 ${OA_CONFIG_FILE}


# create virtualenv
${PYTHON} ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/virtualenv/virtualenv.py ${OA_ENV_DIR}
# copy websocket libs
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/ws4py ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/
# copy salt dependencies
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/{msgpack,yaml,jinja2,markupsafe} ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/
# copy opsagent sources
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SOURCES_DIR}/opsagent ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/

# set ownership to right user
chown -R ${OA_USER}:root ${OA_ENV_DIR}

# Copy launch script editing shebang
sed -e "s|#!/usr/bin/python|#!${OA_ENV_DIR}/bin/python|g" < ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/opsagent > ${OA_ENV_DIR}/bin/opsagent
chown ${OA_USER}:root ${OA_ENV_DIR}/bin/opsagent
chmod 554 ${OA_ENV_DIR}/bin/opsagent

# create service
cp ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/daemon.sh /etc/init.d/opsagentd
if [ $(which chkconfig 2>/dev/null) ]; then
    echo "chkconfig based daemons platform"
    chkconfig --add opsagentd
    chkconfig --level 345 opsagentd on
elif [ $(which update-rc.d) ]; then
    echo "update-rc.d based daemons platform"
    update-rc.d opsagentd defaults
    update-rc.d opsagentd enable
else
    echo "Fatal: no service manager"
    exit 1
fi

# set service script rights
chown root:root /etc/init.d/opsagentd
chmod 554 /etc/init.d/opsagentd

##
# TMP (AGENT START)
# TODO: remove
MADEIRA_HOST=$(grep "api.madeiracloud.com" /etc/hosts | wc -l)
if [ ${MADEIRA_HOST} -eq 0 ]; then
    echo "211.98.26.9 api.madeiracloud.com" >> /etc/hosts
fi
##

# EOF
