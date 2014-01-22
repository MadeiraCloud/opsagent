#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# copy daemon file
cp /madeira/bootstrap/daemon.sh /etc/init.d/opsagentd
chkconfig --add opsagentd
chkconfig --level 345 opsagentd on
# EOF
