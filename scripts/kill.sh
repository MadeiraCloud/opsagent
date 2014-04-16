#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##

for id in `ps aux | grep opsagent | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
    kill -9 $id
done

if [ "$1" = "restart" ]; then
    sleep 2
    service opsagentd start
fi
