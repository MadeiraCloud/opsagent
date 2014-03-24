#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

if [ "$1" != "update" ]; then
    # RW set variables
    APP_ID=@{app_id}
    WS_URI=@{ws_uri}
    VERSION=@{version}
    BASE_REMOTE=@{remote}
    GPG_KEY_URI=@{gpg_key_uri}
fi

# opsagent config directory
OA_CONF_DIR=/var/lib/visualops/opsagent
# ops agent watch files crc directory
OA_WATCH_DIR=${OA_CONF_DIR}/watch
# opsagent logs directory
OA_LOG_DIR=/var/log/visualops
# opsagent URI
#BASE_REMOTE=https://s3.amazonaws.com/visualops
OA_REMOTE="${BASE_REMOTE}/${VERSION}"
OA_GPG_KEY="${OA_CONF_DIR}/madeira.gpg.public.key"

# OpsAgent directories
OA_ROOT_DIR=/opt/visualops
OA_BOOT_DIR=${OA_ROOT_DIR}/bootstrap
OA_ENV_DIR=${OA_ROOT_DIR}/env

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

#ulimit -S -c 0

export OA_EXEC_FILE=${OA_EXEC_FILE}
export OA_LOG_DIR=${OA_LOG_DIR}

if [ \$(cat \${OA_LOG_DIR}/bootstrap.log | wc -l) -gt 1000 ]; then
    cp -f \${OA_LOG_DIR}/bootstrap.log \${OA_LOG_DIR}/bootstrap.log.old
    echo -n > \${OA_LOG_DIR}/bootstrap.log
    chown root:root \${OA_LOG_DIR}/bootstrap.log.old
    chmod 640 \${OA_LOG_DIR}/bootstrap.log.old
fi

if [ -f \${OA_EXEC_FILE} ]; then
    OLD_PID="\$(cat \${OA_EXEC_FILE})"
    if [ \$(ps -eo pid,comm | tr -d " " | grep \${OLD_PID} | wc -l) -ne 0 ]; then
        echo "Bootstrap already running ..."
        exit 0
    else
        rm -f \${OA_EXEC_FILE}
    fi
fi

export OA_CONF_DIR=${OA_CONF_DIR}
export OA_WATCH_DIR=${OA_WATCH_DIR}
export OA_REMOTE=${OA_REMOTE}

export OA_ROOT_DIR=${OA_ROOT_DIR}
export OA_BOOT_DIR=${OA_BOOT_DIR}
export OA_ENV_DIR=${OA_ENV_DIR}

export OA_GPG_KEY=${OA_GPG_KEY}

export APP_ID=${APP_ID}
export WS_URI=${WS_URI}
export VERSION=${VERSION}
export BASE_REMOTE=${BASE_REMOTE}
export GPG_KEY_URI=${GPG_KEY_URI}

# set working file
ps -eo "pid,comm" | tr -d " " | grep "^\$$" > \${OA_EXEC_FILE}

# Set bootstrap log with restrictive access rights
if [ ! -f \${OA_LOG_DIR}/bootstrap.log ]; then
    touch \${OA_LOG_DIR}/bootstrap.log
fi
chown root:root \${OA_LOG_DIR}/bootstrap.log
chmod 640 \${OA_LOG_DIR}/bootstrap.log

echo "Getting public key ..."
curl -sSL -o \${OA_GPG_KEY} \${GPG_KEY_URI}
if [ $? -eq 0 ]; then
    echo "Public key downloaded."
    chmod 440 \${OA_GPG_KEY}

    echo "Getting init script ..."
    curl -sSL -o \${OA_CONF_DIR}/init.sh.gpg \${OA_REMOTE}/init.sh.gpg
    curl -sSL -o \${OA_CONF_DIR}/init.sh.gpg.cksum \${OA_REMOTE}/init.sh.gpg.cksum
    cd \${OA_CONF_DIR}
    REF_CKSUM="$(cat \${OA_CONF_DIR}/init.sh.gpg.cksum)"
    CUR_CKSUM="$(cksum init.sh.gpg)"
    cd -
    if [ "$REF_CKSUM" = "$CUR_CKSUM" ]; then
        echo "Init script downloaded."
        chmod 640 \${OA_CONF_DIR}/init.sh.gpg
        gpg --import \${OA_GPG_KEY}
        rm -f \${OA_CONF_DIR}/init.sh
        gpg --output \${OA_CONF_DIR}/init.sh --decrypt \${OA_CONF_DIR}/init.sh.gpg

        if [ $? -eq 0 ]; then
            echo "Check succeed, running init script ..."
            chmod 750 \${OA_CONF_DIR}/init.sh
            bash \${OA_CONF_DIR}/init.sh
            EXIT=\$?
        else
            echo "FATAL: init checksum check failed." >&2
            EXIT=1
        fi
    else
        echo "FATAL: Can't download init script."
        EXIT=2
    fi
else
    echo "FATAL: Can't get public key."
    EXIT=3
fi

rm -f \${OA_EXEC_FILE}
exit \${EXIT}
EOF

# set cron
chown root:root ${OA_CONF_DIR}/cron.sh
chmod 540 ${OA_CONF_DIR}/cron.sh
CRON=$(grep ${OA_CONF_DIR}/cron.sh /etc/crontab | wc -l)
if [ $CRON -eq 0 ]; then
    echo "*/1 * * * * ${OA_CONF_DIR}/cron.sh >> ${OA_LOG_DIR}/bootstrap.log 2>&1" | crontab
fi

#((${OA_CONF_DIR}/cron.sh >> ${OA_LOG_DIR}/bootstrap.log 2>&1)&)&

# EOF
