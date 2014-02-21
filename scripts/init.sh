#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# Set path
PATH=${PATH}:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# OpsAgent run user
OA_USER=root

# Source directories
SRC_SCRIPTS_DIR=scripts
SRC_CONF_DIR=conf
SRC_LIBS_DIR=libs
SRC_SOURCES_DIR=sources

# Config file destination
OA_CONFIG_FILE=/etc/opsagent.conf

## salt update trigger
#SALT_UPDATE_FILE=/tmp/opsagent.salt.update

# OpsAgent files
OA_AGENT=opsagent
OA_SALT=salt

# Token
OA_TOKEN=${OA_CONF_DIR}/token

# Log file
OA_LOG_FILE=${OA_LOG_DIR}/agent.log


# Create main directories
mkdir -p ${OA_CONF_DIR}
mkdir -p ${OA_LOG_DIR}
mkdir -p ${OA_ROOT_DIR}
mkdir -p ${OA_BOOT_DIR}

# Generate token
if [ ! -f ${OA_TOKEN} ]; then
    ssh-keygen -b 2048 -q -P '' -f ${OA_TOKEN}
    rm -f ${OA_TOKEN}.pub
fi
chown ${OA_USER}:root ${OA_TOKEN}
chmod 400 ${OA_TOKEN}

# Set agent log with restrictive access rights
if [ ! -f ${OA_LOG_FILE} ]; then
    touch ${OA_LOG_FILE}
fi
chown ${OA_USER}:root ${OA_LOG_FILE}
chmod 640 ${OA_LOG_FILE}

# Generates config file
if [ ! -f ${OA_CONFIG_FILE} ]; then
cat <<EOF > ${OA_CONFIG_FILE}
[global]
envroot=${OA_ENV_DIR}
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
chmod 440 ${OA_CONFIG_FILE}

# Setup git
if [ $(which apt-get) ]; then
    apt-get -y -q install git
elif [ $(which yum) ]; then
    yum -y -q install git
fi

# Sources update check
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
## get salt repo
#if [ ! -d ${OA_BOOT_DIR}/${OA_SALT} ]; then
#    git clone ${SALT_REPO_URI} ${OA_BOOT_DIR}/${OA_SALT}
#    cd ${OA_BOOT_DIR}/${OA_SALT}
#    git checkout ${SALT_REPO_BRANCH}
#    cd -
#    UPDATE_SALT=2
#elif [ -f ${SALT_UPDATE_FILE} ]; then
#    cd ${OA_BOOT_DIR}/${OA_SALT}
#    CHANGE=$(git fetch origin ${SALT_REPO_BRANCH} | grep "origin/${SALT_REPO_BRANCH}" | wc -l)
#    if [ ${CHANGE} -ne 0 ]; then
#        UPDATE_SALT=1
#    else
#        UPDATE_SALT=0
#        rm -f ${SALT_UPDATE_FILE}
#    fi
#    cd -
#else
#    UPDATE_SALT=0
#fi
#UPDATE_SALT=$(update_sources ${OA_SALT})
#echo "UPDATESALT=$UPDATE_SALT"
#if [ ${UPDATE_SALT} -ne 0 ]; then
#    echo "update salt"
#    get_sources ${OA_SALT}
#else
#    echo "don't update salt"
#fi

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

## bootstrap salt
#if [ ${UPDATE_AGENT} -ne 0 ] || [ ${UPDATE_SALT} -ne 0 ]; then
#    if [ ${UPDATE_AGENT} -eq 0 ]; then
#        echo "stop agent (bootstrap salt)"
#        service opsagentd stop-end
#    fi
#    echo "bootstrap salt"
#    if [ ${UPDATE_SALT} -eq 1 ]; then
#        cd ${OA_BOOT_DIR}/${OA_SALT}
#        git reset --hard FETCH_HEAD
#        git clean -df
#        rm -f ${SALT_UPDATE_FILE}
#        cd -
#    fi
#    source ${OA_BOOT_DIR}/${OA_SALT}/${SRC_SCRIPTS_DIR}/bootstrap.sh
#else
#    echo "don't bootstrap salt"
#fi

# load agent
#if [ ${UPDATE_AGENT} -ne 0 ] || [ ${UPDATE_SALT} -ne 0 ]; then
if [ ${UPDATE_AGENT} -ne 0 ]; then
    echo "load agent"
    service opsagentd start
else
    echo "don't load agent"
fi

# EOF
