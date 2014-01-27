#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##
#app_id=@{app_id}
OA_CONF_DIR=/etc/opsagent.d
OA_LOG_DIR=/var/log/madeira
OA_EXEC_FILE=/tmp/opsagent.boot
# bootstrap
cat <<EOF > ${OA_CONF_DIR}/cron.sh
#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##
if [ -f $OA_EXEC_FILE ]; then
    echo "Bootstrap already running ..."
    exit 0
fi
touch $OA_EXEC_FILE
# Set bootstrap log with restrictive access rights
if [ ! -f ${OA_LOG_DIR}/bootstrap.log ]; then
    touch ${OA_LOG_DIR}/bootstrap.log
fi
chown root:root ${OA_LOG_DIR}/bootstrap.log
chmod 640 ${OA_LOG_DIR}/bootstrap.log
. ${OA_CONF_DIR}/init.sh
rm -f $OA_EXEC_FILE
EOF
chown root:root ${OA_CONF_DIR}/cron.sh
chmod 540 ${OA_CONF_DIR}/cron.sh
CRON=$(crontab -l | grep ${OA_CONF_DIR}/cron.sh | wc -l)
if [ $CRON -eq 0 ]; then
    echo "*/1 * * * * ${OA_CONF_DIR}/cron.sh >> ${OA_LOG_DIR}/bootstrap.log 2>&1" | crontab
fi
exit 0
# EOF
