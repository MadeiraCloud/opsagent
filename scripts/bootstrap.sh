#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# setup dependencies
if [ $(which apt-get) ]; then
    # install python
    apt-get -y -q install python2.7
    if [ $? -ne 0 ]; then
        apt-get -y -q install python2.6
    fi
    # install other dependencies
    apt-get -y -q install git python-apt expect-dev
elif [ $(which yum) ]; then
    # install python
    yum -y -q install python27
    if [ $? -ne 0 ]; then
        yum -y -q install python26
    fi
    # install other dependencies
    yum -y -q install git expect
fi
# define python version
if [ $(which python2.7) ]; then
    PYTHON="python2.7"
elif [ $(which python2.6) ]; then
    PYTHON="python2.6"
else
    echo "Fatal: Python2 non installed"
    exit 1
fi

# create virtualenv
${PYTHON} ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/virtualenv/virtualenv.py ${OA_ENV_DIR}
# copy websocket libs
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/ws4py ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/
# copy salt dependencies
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/{msgpack,yaml,jinja2,markupsafe} ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/
# copy opsagent sources
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SOURCES_DIR}/opsagent ${OA_ENV_DIR}/lib/${PYTHON}/site-packages/
# copy config files
mkdir -p ${OA_ENV_DIR}/etc
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_CONF_DIR}/* ${OA_ENV_DIR}/etc/
chmod -R 640 ${OA_ENV_DIR}/etc/*
# set ownership to right user
chown -R ${OA_USER}:root ${OA_ENV_DIR}

# link config file
if [ ! -f ${OA_CONFIG_FILE} ]; then
    ln -s ${OA_ENV_DIR}/etc/opsagent.conf ${OA_CONFIG_FILE}
fi

# Copy launch script editing shebang
sed -e "s|#!/usr/bin/python|#!/${OA_ENV_DIR}/bin/python|g" < ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/opsagent > ${OA_ENV_DIR}/bin/opsagent
chown ${OA_USER}:root ${OA_ENV_DIR}/bin/opsagent
chmod 554 ${OA_ENV_DIR}/bin/opsagent

# create service
cp ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/daemon.sh /etc/init.d/opsagentd
if [ $(which chkconfig) ]; then
    chkconfig --add opsagentd
    chkconfig --level 345 opsagentd on
elif [ $(which update-rc.d) ]; then
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
