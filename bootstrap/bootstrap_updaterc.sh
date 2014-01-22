#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

# copy daemon file
update-rc.d opsagentd defaults
update-rc.d opsagentd enable
# EOF
