#!/bin/bash

OA_CONF_DIR=/var/lib/visualops/opsagent
OA_GPG_KEY="${OA_CONF_DIR}/madeira.gpg.public.key"

export WS_URI="ws://54.92.117.156:8963/agent/"
export APP_ID=$1
export VERSION="1.0"
export BASE_REMOTE="https://s3.amazonaws.com/opsagent"
export GPG_KEY_URI="https://s3.amazonaws.com/opsagent/madeira.gpg.public.key"
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

unset ${AGENT_UPDATE}

if [ $EXIT -eq 0 ]; then
    echo "Update succeed."
else
    echo "Update failed."
fi

exit $EXIT
#EOF
