#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# create virtualenv
${PYTHON} ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/virtualenv/virtualenv.py ${OA_ENV_DIR}
if [ $(which apt-get 2>/dev/null) ]; then
    ${OA_ENV_DIR}/bin/pip install python-apt
fi
# set cache directory
mkdir -p ${OA_PKG_CACHE_DIR}
chown ${OA_USER}:root ${OA_PKG_CACHE_DIR}
chmod 755 ${OA_PKG_CACHE_DIR}
# copy EPEL rpm
ARCH=`uname -p`
cp -r ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_LIBS_DIR}/epel/${ARCH}/${OA_EPEL_FILE} ${OA_PKG_CACHE_DIR}/
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
    echo "Fatal: no service manager" >&2
    exit 1
fi

# set service script rights
chown root:root /etc/init.d/opsagentd
chmod 550 /etc/init.d/opsagentd

# set update script rights
chown root:root ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/update.sh
chmod 550 ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/update.sh

##
# TMP (AGENT START)
# TODO: remove
MADEIRA_HOST=$(grep "api.visualops.io" /etc/hosts | wc -l)
if [ ${MADEIRA_HOST} -eq 0 ]; then
    echo "211.98.26.8 api.visualops.io" >> /etc/hosts
fi
##

# EOF
