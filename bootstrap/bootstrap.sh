#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# define variables
OA_HOME="/root"
OA_USER="root"
OA_ROOT="/opsagent"

if [ -d "$OA_ROOT" ]; then
    # TODO remove
    echo "$OA_ROOT exists"
    exit 0
fi

# define vendor
YUM_CMD=$(which yum)
APT_CMD=$(which apt-get)
# define service utility
UPDATERC_CMD=$(which update-rc.d)
CHKCONFIG_CMD=$(which chkconfig)


# locate in home directory
cd $OA_HOME
# get agent
CRC=""
while true; do
    curl -sSLO https://s3.amazonaws.com/visualops/agent.cksum
    curl -sSLO https://s3.amazonaws.com/visualops/agent.tgz
    REF_CRC="$(cat agent.cksum)"
    CRC="$(cksum agent.tgz)"
    if [ "$CRC" = "$REF_CRC" ]; then
        break
    else
        echo "Checksum check failed, retryind in 1 second" >&2
        sleep 1
    fi
done
cd /
tar xfz $OA_HOME/agent.tgz
# setup dependencies
if [ $APT_CMD ]; then
    source $OA_ROOT/bootstrap/bootstrap_apt.sh
elif [ $YUM_CMD ]; then
    source $OA_ROOT/bootstrap/bootstrap_yum.sh
fi
# create virtualenv
python2.7 $OA_ROOT/bootstrap/virtualenv/virtualenv.py $OA_ROOT/env
# copy websocket libs
cp -r $OA_ROOT/sources/ws4py $OA_ROOT/env/lib/python2.7/site-packages/
# copy salt libs
cp -r $OA_ROOT/sources/{msgpack,yaml,jinja2,markupsafe,salt} $OA_ROOT/env/lib/python2.7/site-packages/
# copy opsagent sources
cp -r $OA_ROOT/sources/opsagent $OA_ROOT/env/lib/python2.7/site-packages/
# set ownership to root
chown -R $OA_USER:root $OA_ROOT
# link config file
if [ -f "/etc/opsagent.conf" ]; then
    mv /etc/opsagent.conf /etc/opsagent.old.conf
fi
ln -s $OA_ROOT/env/etc/opsagent.conf /etc/opsagent.conf

# create service
if [ $CHKCONFIG_CMD ]; then
    source $OA_ROOT/bootstrap/bootstrap_chkconfig.sh
elif [ $UPDATERC_CMD ]; then
    source $OA_ROOT/bootstrap/bootstrap_updaterc.sh
fi


# TMP (AGENT START)
# TODO: remove
MADEIRA_HOST=$(grep "api.madeiracloud.com" /etc/hosts | wc -l)
if [ $MADEIRA_HOST -eq 0 ]; then
    echo "211.98.26.9 api.madeiracloud.com" >> /etc/hosts
fi


# start service
chown root:root /etc/init.d/opsagentd
chmod 554 /etc/init.d/opsagentd
service opsagentd start

exit 0

# EOF
