#!/bin/bash
##
## @author: Thibault BRONCHAIN
## (c) 2014 MadeiraCloud LTD.
##
### BEGIN INIT INFO
# Provides: opsagent
# Required-Start:
# Should-Start:
# Required-Stop:
# Should-Stop:
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Opsagent Daemon
# Description: Runs opsagent
### END INIT INFO

OA_ROOT="/opt/visualops"

case "$1" in
    start)
        echo "Starting opsagent"
        ${OA_ROOT}/env/bin/opsagent -c /etc/opsagent.conf start
        ;;
    stop)
        echo "Stopping opsagent"
        ${OA_ROOT}/env/bin/opsagent stop
        ;;
    force-stop)
        echo "Killing opsagent..."
        for id in `ps aux | grep "${OA_ROOT}/env/bin/opsagent" | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
            kill -9 $id
        done
        ;;
    restart)
        echo "Restarting opsagent"
        ${OA_ROOT}/env/bin/opsagent -c /etc/opsagent.conf restart
        ;;
    force-restart)
        echo "Killing opsagent..."
        for id in `ps aux | grep "${OA_ROOT}/env/bin/opsagent" | sed -e 's/  */ /g' | cut -d ' ' -f 2`; do
            kill -9 $id
        done
        sleep 1
        ${OA_ROOT}/env/bin/opsagent -c /etc/opsagent.conf start
        ;;
    stop-wait)
        echo "Stopping opsagent waiting state end"
        ${OA_ROOT}/env/bin/opsagent stop-wait
        ;;
    restart-wait)
        echo "Restarting opsagent waiting state end"
        ${OA_ROOT}/env/bin/opsagent -c /etc/opsagent.conf restart-wait
        ;;
    stop-end)
        echo "Stopping opsagent waiting recipe end"
        ${OA_ROOT}/env/bin/opsagent stop-end
        ;;
    restart-end)
        echo "Restarting opsagent waiting recipe end"
        ${OA_ROOT}/env/bin/opsagent -c /etc/opsagent.conf restart-end
        ;;
    status)
        ${OA_ROOT}/env/bin/opsagent status
        exit $?
        ;;
    *)
        echo "Usage: $0 {start|stop|force-stop|restart|force-restart|stop-wait|restart-wait|stop-end|restart-end|status}"
        exit 1
        ;;
esac

exit 0
