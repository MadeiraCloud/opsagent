#!/bin/bash
#app_id=@{app_id}
OA_USER="root"
OA_DIR="/etc/opsagent.d"
OA_LOG="/var/log/opsagent"
mkdir -p $OA_DIR
mkdir -p $OA_LOG
ssh-keygen -b 2048 -q -P '' -f $OA_DIR/token
rm -f $OA_DIR/token.pub
chown $OA_USER:root $OA_DIR/token
chmod 400 $OA_DIR/token
if [ ! -f ${OA_LOG}/bootstrap.log ]; then
    touch ${OA_LOG}/bootstrap.log
    chown root:root ${OA_LOG}/bootstrap.log
    chmod 640 ${OA_LOG}/bootstrap.log
fi
if [ ! -f ${OA_LOG}/agent.log ]; then
    touch ${OA_LOG}/agent.log
    chown ${OA_USER}:root ${OA_LOG}/agent.log
    chmod 640 ${OA_LOG}/agent.log
fi
echo 'curl -sSL https://s3.amazonaws.com/visualops/bootstrap.sh | bash' > $OA_DIR/bootstrap.sh
chown root:root $OA_DIR/bootstrap.sh
chmod 500 $OA_DIR/bootstrap.sh
echo "*/5 * * * * ${OA_DIR}/bootstrap.sh >> ${OA_LOG}/bootstrap.log 2>&1" | crontab
