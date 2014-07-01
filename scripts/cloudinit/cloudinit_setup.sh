#!/bin/bash
# Author: Thibault BRONCHAIN

USAGE="$0 [-yh]"
VERSION="6-8"

if [ "$1" = "-h" ]; then
    echo "syntax: $USAGE"
    exit 0
fi

# activate EPEL repo
curl -sSLO http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-${VERSION}.noarch.rpm
sudo rpm -Uvh epel-release-*.rpm

# install cloudinitd and its depencies
yum -y install python-devel gcc python-pip perl
pip install --upgrade cloudinitd

# place run userdata script
cp ec2-run-user-data /etc/init.d/ec2-run-user-data
chmod 755 /etc/init.d/ec2-run-user-data

# register service to startup
chkconfig ec2-run-user-data on

# start service
echo -n "Cloudinit has been correctly configured. Would you like to start the service now? [y/N] "
if [ "$1" = "-y" ]; then
    c_start="y"
    echo "y"
else
    read c_start
fi
if [ "$c_start" = "y" ]; then
    service ec2-run-user-data start
else
    echo "cloudinit service not started, please do it manually, or restart your instance."
fi

# done
echo "Cloudinit bootstrap done."
