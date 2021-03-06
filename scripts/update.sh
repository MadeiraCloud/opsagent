#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

OA_UPDATE_FILE=/tmp/opsagent.update

if [ -f ${OA_UPDATE_FILE} ]; then
    UP_PID="$(cat ${OA_UPDATE_FILE})"
    if [ $(ps -eo pid,comm | tr -d ' ' | grep ${UP_PID} | wc -l) -ne 0 ]; then
        echo "update.sh: Update already running ..." >&2
        exit 0
    else
        rm -f ${OA_UPDATE_FILE}
    fi
fi

echo "update starting ..."

# set working file
ps -eo pid,comm | tr -d ' ' | grep "^$$" > ${OA_UPDATE_FILE}

OA_CONF_DIR=/var/lib/visualops/opsagent
OA_GPG_KEY="${OA_CONF_DIR}/madeira.gpg.public.key"

export WS_URI=$1
export APP_ID=$2
export VERSION=$3
export BASE_REMOTE=$4
export GPG_KEY_URI=$5
export AGENT_UPDATE="update"

OA_REMOTE="${BASE_REMOTE}/${VERSION}"

wget -nv -O ${OA_CONF_DIR}/ud_init.sh.gpg ${OA_REMOTE}/ud_init.sh.gpg
wget -nv -O ${OA_CONF_DIR}/ud_init.sh.gpg.cksum ${OA_REMOTE}/ud_init.sh.gpg.cksum

cd ${OA_CONF_DIR}
REF_CKSUM="$(cat ${OA_CONF_DIR}/ud_init.sh.gpg.cksum)"
CUR_CKSUM="$(cksum ud_init.sh.gpg)"
cd -
if [ "$REF_CKSUM" = "$CUR_CKSUM" ]; then
    chmod 640 ${OA_CONF_DIR}/ud_init.sh.gpg

    gpg --no-tty --import ${OA_GPG_KEY}
    gpg --no-tty --verify ${OA_CONF_DIR}/ud_init.sh.gpg
    if [ $? -eq 0 ]; then
        gpg --no-tty --output ${OA_CONF_DIR}/ud_init.sh --decrypt ${OA_CONF_DIR}/ud_init.sh.gpg
        chmod 750 ${OA_CONF_DIR}/ud_init.sh
        bash ${OA_CONF_DIR}/ud_init.sh
        EXIT=$?
    else
        echo "update.sh: FATAL: ud_init GPG extraction failed." >&2
        EXIT=10
   fi
else
    echo "update.sh: FATAL: can't verify ud_init script." >&2
    EXIT=11
fi

rm -f ${OA_UPDATE_FILE}
unset ${AGENT_UPDATE}

if [ $EXIT -eq 0 ]; then
    echo "Update succeed."
else
    echo "Update failed."
fi

exit $EXIT
#EOF
