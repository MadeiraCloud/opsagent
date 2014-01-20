#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# copy daemon file
cp /madeira/bootstrap/daemon_updaterc.sh /etc/init.d/opsagentd
update-rc.d opsagentd defaults
update-rc.d opsagentd enable
# EOF
