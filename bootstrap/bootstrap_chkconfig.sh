#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# copy daemon file
chkconfig --add opsagentd
chkconfig --level 345 opsagentd on
# EOF
