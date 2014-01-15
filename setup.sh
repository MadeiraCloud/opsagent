#!/bin/bash
## @author: Thibault BRONCHAIN

apt-get install python2.7
apt-get install python-apt
cd /root
curl -O https://s3.amazonaws.com/visualops/agent.tgz
cd /
tar xfz /root/agent.tgz
python2.7 /madeira/bootstrap/virtualenv/virtualenv.py /madeira/env
cp -r /madeira/sources/ws4py /madeira/env/lib/python2.7/site-packages/
cp -r /madeira/sources/salt /madeira/env/lib/python2.7/site-packages/
cp -r /madeira/sources/yaml /madeira/env/lib/python2.7/site-packages/
cp -r /madeira/sources/opsagent /madeira/env/lib/python2.7/site-packages/
chown -R root:root /madeira

#/madeira/env/bin/opsagent -v c /madeira/env/etc/aws_test.cfg
