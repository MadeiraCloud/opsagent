#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# define vendor
YUM_CMD=$(which yum)
APT_CMD=$(which apt-get)

# locate in root home directory
cd /root
# get agent
curl -sSLO https://s3.amazonaws.com/visualops-salt/agent.tgz
cd /
tar xfz /root/agent.tgz
# setup dependencies
if [ $APT_CMD ]; then
    source /madeira/bootstrap/bootstrap_apt.sh
elif [ $YUM_CMD ]; then
    source /madeira/bootstrap/bootstrap_yum.sh
fi
# create virtualenv
python2.7 /madeira/bootstrap/virtualenv/virtualenv.py /madeira/env
# copy websocket libs
cp -r /madeira/sources/ws4py /madeira/env/lib/python2.7/site-packages/
# copy salt libs
cp -r /madeira/sources/{msgpack,yaml,jinja2,markupsafe,salt} /madeira/env/lib/python2.7/site-packages/
# copy opsagent sources
cp -r /madeira/sources/opsagent /madeira/env/lib/python2.7/site-packages/
# set ownership to root
chown -R root:root /madeira


# TMP (AGENT START)
# TODO: remove
#MADEIRA_HOST=$(grep "api.madeiracloud.com" /etc/hosts | wc -l)
#if [ $MADEIRA_HOST -eq 0 ]; then
#    echo "211.98.26.9 api.madeiracloud.com" >> /etc/hosts
#fi
#cd /root
#nohup /madeira/env/bin/opsagent -v -c /madeira/env/etc/madeira_test.cfg &

# EOF
