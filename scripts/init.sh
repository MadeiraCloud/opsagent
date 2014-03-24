#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

OA_VERSION=""

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

# Packages cache directory
OA_PKG_CACHE_DIR=${OA_ENV_DIR}/var/cache/pkg
OA_EPEL_FILE="epel-release-6-8.noarch.rpm"

# OpsAgent files
OA_AGENT=opsagent
OA_SALT=salt

# Token
OA_TOKEN=${OA_CONF_DIR}/token

# Log file
OA_LOG_FILE=${OA_LOG_DIR}/agent.log

# var
OA_TMP_ROOT=/tmp/opsagent


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

# Setup git
if [ $(which apt-get 2>/dev/null) ]; then
    apt-get update
    apt-get -y -q install git
elif [ $(which yum 2>/dev/null) ]; then
    yum -y -q install git
fi

# Exit if no git
if [ ! $(which git 2>/dev/null) ]; then
    echo "FATAL: No git found! (can't install?)" >&2
    exit 1
fi


# setup dependencies
if [ $(which apt-get 2>/dev/null) ]; then
    # install python
    echo "Platform: APT"
    apt-get -y -q install python2.7 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Failed to install python 2.7, trying with python 2.6 ..." >&2
        apt-get -y -q install python2.6 2>/dev/null
    fi
    # install other dependencies
    apt-get -y -q install expect-dev python-dev libapt-pkg-dev g++
elif [ $(which yum 2>/dev/null) ]; then
    # install python
    echo "Platform: YUM"
    yum -y -q install python27 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Failed to install python 2.7, trying with python 2.6 ..." >&2
        yum -y -q install python26 2>/dev/null
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
    echo "FATAL: Python2 non installed! (can't install!)" >&2
    exit 1
fi


# Generates config file
#if [ ! -f ${OA_CONFIG_FILE} ]; then
cat <<EOF > ${OA_CONFIG_FILE}
[global]
envroot=${OA_ENV_DIR}
conf_path=${OA_CONF_DIR}
log_path=${OA_LOG_DIR}
package_path=${OA_ENV_DIR}/lib/${PYTHON}/site-packages
token=${OA_TOKEN}
watch=${OA_WATCH_DIR}
logfile=${OA_LOG_FILE}
[userdata]
ws_uri=${WS_URI}
app_id=${APP_ID}
version=${VERSION}
base_remote=${BASE_REMOTE}
gpg_key_uri=${GPG_KEY_URI}
[module]
root=${OA_BOOT_DIR}
name=${OA_SALT}
bootstrap=${SRC_SCRIPTS_DIR}/bootstrap.sh
mod_repo=
mod_tag=
EOF
#fi
chown ${OA_USER}:root ${OA_CONFIG_FILE}
chmod 640 ${OA_CONFIG_FILE}


# Sources update check
function update_sources() {
    RET=0
    if [ -f ${OA_BOOT_DIR}/${1}.tgz ]; then
        CUR_VERSION="$(cat ${OA_BOOT_DIR}/${1}.cksum)"
        RETVAL_CUR=$?
        LAST_VERSION="$(curl -sSL ${OA_REMOTE}/${1}.cksum)"
        RETVAL_LAST=$?
        VALID="$(echo ${LAST_VERSION} | grep ${1}.tgz | wc -l)"
        RETVAL_VALID=$?
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
    rm -f ${OA_BOOT_DIR}/${1}.tgz.gpg
    curl -sSL -o ${OA_BOOT_DIR}/${1}.tgz.gpg ${OA_REMOTE}/${1}.tgz.gpg
    curl -sSL -o ${OA_BOOT_DIR}/${1}.tgz.gpg.cksum ${OA_REMOTE}/${1}.tgz.gpg.cksum

    cd ${OA_BOOT_DIR}
    REF_CKSUM="$(cat ${OA_BOOT_DIR}/${1}.tgz.gpg.cksum)"
    CUR_CKSUM="$(cksum ${1}.tgz.gpg)"
    cd -
    if [ "$REF_CKSUM" != "$CUR_CKSUM" ]; then
        echo "FATAL: Checksum failed on ${1}" >&2
        exit 2
    fi

    chmod 640 ${OA_BOOT_DIR}/${1}.tgz.gpg

    gpg --import ${OA_GPG_KEY}
    rm -f ${OA_BOOT_DIR}/${1}.tgz
    gpg --verify ${OA_BOOT_DIR}/${1}.tgz.gpg
    if [ $? -eq 0 ]; then
        gpg --output ${OA_BOOT_DIR}/${1}.tgz --decrypt ${OA_BOOT_DIR}/${1}.tgz.gpg
        chmod 640 ${OA_BOOT_DIR}/${1}.tgz
    else
        echo "FATAL: couldn't get sources for ${1}" >&2
        exit 1
    fi

    if [ -d ${OA_BOOT_DIR}/${1} ]; then
        rm -rf ${OA_BOOT_DIR}/${1}
    fi
    mkdir -p ${OA_BOOT_DIR}/${1}
    cd ${OA_BOOT_DIR}/${1}
    tar xfz ../${1}.tgz
    cd - 2>&1 > /dev/null
    chown -R root:root ${OA_BOOT_DIR}/${1}
}


# check for updates (and fetch)
UPDATE_AGENT=$(update_sources ${OA_AGENT})
if [ ${UPDATE_AGENT} -ne 0 ]; then
    echo "update agent"
    get_sources ${OA_AGENT}
fi

# shudown agent
if [ ${UPDATE_AGENT} -ne 0 ] && [ -d ${OA_ENV_DIR} ]; then
    echo "shutdown agent"
    service opsagentd stop-end
    rm -rf ${OA_ENV_DIR}
fi

# bootstrap agent
if [ ! -d ${OA_ENV_DIR} ]; then
    if [ ${UPDATE_AGENT} -eq 0 ]; then
        UPDATE_AGENT=3
    fi
    echo "bootstrap agent"
    source ${OA_BOOT_DIR}/${OA_AGENT}/${SRC_SCRIPTS_DIR}/bootstrap.sh
fi

# load agent
if [ ${UPDATE_AGENT} -ne 0 ]; then
    echo "load agent after update"
    service opsagentd start
fi

# run check
service opsagentd status
if [ $? -ne 0 ]; then
    echo "agent not running, attempting to run ..."
    service opsagentd start
    if [ $? -ne 0 ]; then
        echo "FATAL: can't run agent" >&2
        exit 1
    fi
fi

# remove cron
(crontab -l | grep -v -e ${OA_CONF_DIR}/cron.sh -e ${OA_CONF_DIR}/update.sh) > ${OA_TMP_ROOT}.crontab
crontab -r
cat ${OA_TMP_ROOT}.crontab | crontab
#(cat /etc/crontab | grep -v ${OA_CONF_DIR}/cron.sh) > ${OA_TMP_ROOT}.crontab
#mv -f ${OA_TMP_ROOT}.crontab /etc/crontab

# EOF
