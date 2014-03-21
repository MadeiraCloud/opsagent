#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

OA_UPDATE_FILE=/tmp/opsagent.update

if [ -f ${OA_UPDATE_FILE} ]; then
    UP_PID="$(cat ${OA_UPDATE_FILE})"
    if [ $(ps -eo pid,comm | tr -d ' ' | grep ${UP_PID} | wc -l) -ne 0 ]; then
        echo "Update  already running ..."
        exit 0
    else
        rm -f ${OA_UPDATE_FILE}
    fi
fi

# set working file
ps -eo pid,comm | tr -d ' ' | grep "^$$" > ${OA_UPDATE_FILE}

OA_CONF_DIR=/var/lib/madeira/opsagent
OA_GPG_KEY="${OA_CONF_DIR}/madeira.gpg.public.key"

export WS_URI=$1
export APP_ID=$2
export VERSION=$3
export BASE_REMOTE=$4
export GPG_KEY_URI=$5

OA_REMOTE="${BASE_REMOTE}/${VERSION}"

curl -sSL -o ${OA_CONF_DIR}/userdata.sh.gpg ${OA_REMOTE}/userdata.sh.gpg
chmod 640 ${OA_CONF_DIR}/userdata.sh.gpg

gpg --import ${OA_GPG_KEY}
gpg --output ${OA_CONF_DIR}/userdata.sh --decrypt ${OA_CONF_DIR}/userdata.sh.gpg

if [ $? -eq 0 ]; then
    chmod 750 ${OA_CONF_DIR}/userdata.sh
    bash ${OA_CONF_DIR}/userdata.sh "update"
    EXIT=$?
else
    echo "userdata GPG check failed, exiting ..." >&2
    EXIT=10
fi

rm -f ${OA_UPDATE_FILE}
exit $EXIT
#EOF
