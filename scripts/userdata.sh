#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##
#app_id=@{app_id}

# salt repo URI
#SALT_REPO_URI=@{salt_repo_uri}
#SALT_REPO_BRANCH=@{salt_repo_branch}
SALT_REPO_URI=https://github.com/MadeiraCloud/salt.git # TODO: remove
SALT_REPO_BRANCH=develop # TODO: remove

# opsagent config directory
OA_CONF_DIR=/etc/opsagent.d
# opsagent logs directory
OA_LOG_DIR=/var/log/madeira
# opsagent URI
OA_REMOTE=https://s3.amazonaws.com/visualops

# internal var
OA_EXEC_FILE=/tmp/opsagent.boot

mkdir -p {$OA_LOG_DIR,$OA_CONF_DIR}

# bootstrap
cat <<EOF > ${OA_CONF_DIR}/cron.sh
#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##
if [ -f ${OA_EXEC_FILE} ]; then
    echo "Bootstrap already running ..."
    exit 0
fi

SALT_REPO_URI=${SALT_REPO_URI}
SALT_REPO_BRANCH=${SALT_REPO_BRANCH}
OA_CONF_DIR=${OA_CONF_DIR}
OA_LOG_DIR=${OA_LOG_DIR}
OA_EXEC_FILE=${OA_EXEC_FILE}
OA_REMOTE=${OA_REMOTE}

touch ${OA_EXEC_FILE}
# Set bootstrap log with restrictive access rights
if [ ! -f ${OA_LOG_DIR}/bootstrap.log ]; then
    touch ${OA_LOG_DIR}/bootstrap.log
fi
chown root:root ${OA_LOG_DIR}/bootstrap.log
chmod 640 ${OA_LOG_DIR}/bootstrap.log
while true; do
    curl -sSL -o ${OA_CONF_DIR}/init.sh ${OA_REMOTE}/init.sh
    curl -sSL -o ${OA_CONF_DIR}/init.cksum ${OA_REMOTE}/init.cksum
    chmod 640 ${OA_CONF_DIR}/init.cksum
    chmod 750 ${OA_CONF_DIR}/init.sh
    REF_CRC="\$(cat ${OA_CONF_DIR}/init.cksum)"
    cd ${OA_CONF_DIR}
    CRC="\$(cksum init.sh)"
    cd -
    if [ "\${CRC}" = "\${REF_CRC}" ]; then
        break
    else
        echo "init checksum check failed, retryind in 1 second" >&2
        sleep 1
    fi
done
source ${OA_CONF_DIR}/init.sh
rm -f ${OA_EXEC_FILE}
EOF

# set cron
chown root:root ${OA_CONF_DIR}/cron.sh
chmod 540 ${OA_CONF_DIR}/cron.sh
CRON=$(crontab -l | grep ${OA_CONF_DIR}/cron.sh | wc -l)
if [ $CRON -eq 0 ]; then
    echo "*/1 * * * * ${OA_CONF_DIR}/cron.sh >> ${OA_LOG_DIR}/bootstrap.log 2>&1" | crontab
fi

exit 0
# EOF
