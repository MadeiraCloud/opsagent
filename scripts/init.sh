#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# for crc

# Set path
PATH=${PATH}:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# OpsAgent run user
OA_USER=root

# OpsAgent remote location
OA_REMOTE=https://s3.amazonaws.com/visualops

# OpsAgent directories
OA_ROOT_DIR=/opt/madeira
OA_BOOT_DIR=${OA_ROOT_DIR}/bootstrap
OA_ENV_DIR=${OA_ROOT_DIR}/env

OA_CONF_DIR=/etc/opsagent.d
OA_LOG_DIR=/var/log/madeira

SRC_SCRIPTS_DIR=scripts
SRC_CONF_DIR=conf
SRC_LIBS_DIR=libs
SRC_SOURCES_DIR=sources

OA_CONFIG_FILE=/etc/opsagent.conf


# OpsAgent files
OA_AGENT=opsagent
OA_SALT=saltmodules

# Create main directories
mkdir -p ${OA_CONF_DIR}
mkdir -p ${OA_LOG_DIR}
mkdir -p ${OA_ROOT_DIR}
mkdir -p ${OA_BOOT_DIR}

# Generate token
if [ ! -f ${OA_CONF_DIR}/token ]; then
    ssh-keygen -b 2048 -q -P '' -f ${OA_CONF_DIR}/token
    rm -f ${OA_CONF_DIR}/token.pub
fi
chown ${OA_USER}:root ${OA_CONF_DIR}/token
chmod 400 ${OA_CONF_DIR}/token

# Set agent log with restrictive access rights
if [ ! -f ${OA_LOG_DIR}/agent.log ]; then
    touch ${OA_LOG_DIR}/agent.log
fi
chown ${OA_USER}:root ${OA_LOG_DIR}/agent.log
chmod 640 ${OA_LOG_DIR}/agent.log


# sources update check
function update_sources() {
    RET=0
    if [ -f ${OA_BOOT_DIR}/${1}.tgz ]; then
        CUR_VERSION="$(cat ${OA_BOOT_DIR}/${1}.cksum)"
        RETVAL_CUR=$?
        LAST_VERSION="$(curl -sSL ${OA_REMOTE}/${1}.cksum)"
        RETVAL_LAST=$?
        VALID="$(echo $LAST_VERSION | grep ${1}.tgz | wc -l)"
        RETVAL_VALID=$?
        echo "RETVAL_CUR=$RETVAL_CUR" 1>&2
        echo "RETVAL_LAST=$RETVAL_LAST" 1>&2
        echo "RETVAL_VALID=$RETVAL_VALID" 1>&2
        echo "VALID=$VALID" 1>&2
        echo "CUR_VERSION=$CUR_VERSION" 1>&2
        if ([ "$RETVAL_CUR" != "0" ]) \
            || \
            ([ "$RETVAL_LAST" = "0" ] && [ "$RETVAL_VALID" = "0" ] && [ "$VALID" = "1" ] && [ "$CUR_VERSION" != "$LAST_VERSION" ])
        then
            RET=1
        else
            RET=0
        fi
    else
        RET=2
    fi
    echo ${RET}
}

# sources update fetch
function get_sources() {
    while true; do
        curl -sSL -o ${OA_BOOT_DIR}/${1}.cksum ${OA_REMOTE}/${1}.cksum
        curl -sSL -o ${OA_BOOT_DIR}/${1}.tgz ${OA_REMOTE}/${1}.tgz
        chmod 640 ${OA_BOOT_DIR}/${1}.{cksum,tgz}
        REF_CRC="$(cat ${OA_BOOT_DIR}/${1}.cksum)"
        cd ${OA_BOOT_DIR}
        CRC="$(cksum ${1}.tgz)"
        cd -
        if [ "$CRC" = "$REF_CRC" ]; then
            break
        else
            echo "${1} checksum check failed, retryind in 1 second" >&2
            sleep 1
        fi
    done
    if [ -d ${OA_BOOT_DIR}/${1} ]; then
        rm -rf ${OA_BOOT_DIR}/${1}
    fi
    mkdir -p ${OA_BOOT_DIR}/${1}
    cd ${OA_BOOT_DIR}/${1}
    tar xfz ../${1}.tgz
    cd -
    chown -R root:root ${OA_BOOT_DIR}/${1}
}


# check for updates (and fetch)
UPDATE_AGENT=$(update_sources ${OA_AGENT})
echo "UPDATEAGENT=$UPDATE_AGENT"
if [ ${UPDATE_AGENT} -ne 0 ]; then
    echo "update agent"
    get_sources ${OA_AGENT}
else
    echo "don't update agent"
fi
UPDATE_SALT=$(update_sources ${OA_SALT})
echo "UPDATESALT=$UPDATE_SALT"
if [ ${UPDATE_SALT} -ne 0 ]; then
    echo "update salt"
    get_sources ${OA_SALT}
else
    echo "don't update agent"
fi

# shudown agent
if [ ${UPDATE_AGENT} -ne 0 ] && [ -d ${OA_ENV_DIR} ]; then
    echo "shutdown agent"
    service opsagentd stop-end
    rm -rf ${OA_ENV_DIR}
else
    echo "don't shutdown agent"
fi

# bootstrap agent
if [ ! -d ${OA_ENV_DIR} ]; then
    if [ ${UPDATE_AGENT} -eq 0 ]; then
        echo "change update_agent to 3"
        UPDATE_AGENT=3
    fi
    echo "bootstrap agent"
    source ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/bootstrap.sh
else
    echo "don't bootstrap agent"
fi

# patch salt
if [ ${UPDATE_AGENT} -ne 0 ] || [ ${UPDATE_SALT} -ne 0 ]; then
    if [ ${UPDATE_AGENT} -eq 0 ]; then
        echo "stop agent (update salt)"
        service opsagentd stop-end
    fi
    echo "patch salt"
    source ${OA_BOOT_DIR}/${OA_SALT}/${SRC_SCRIPTS_DIR}/bootstrap.sh
else
    echo "don't patch salt"
fi

# load agent
if [ ${UPDATE_AGENT} -ne 0 ] || [ ${UPDATE_SALT} -ne 0 ]; then
    echo "load agent"
    service opsagentd start
else
    echo "don't load agent"
fi

# EOF
