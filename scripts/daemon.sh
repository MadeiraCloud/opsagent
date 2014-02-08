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
# Default-Start:  3 4 5
# Default-Stop:   0 6
# Short-Description: Opsagent Daemon
# Description: Runs opsagent
### END INIT INFO

OA_ROOT="/opt/madeira"

case "$1" in
  start)
    echo "Starting opsagent"
    ${OA_ROOT}/env/bin/opsagent -c /etc/opsagent.conf start
    ;;
  stop)
    echo "Stopping opsagent"
    ${OA_ROOT}/env/bin/opsagent stop
    ;;
  stop-wait)
    echo "Stopping opsagent waiting state end"
    ${OA_ROOT}/env/bin/opsagent stop-wait
    ;;
  restart-wait)
    echo "Restarting opsagent waiting state end"
    ${OA_ROOT}/env/bin/opsagent restart-wait
    ;;
  stop-end)
    echo "Stopping opsagent waiting recipe end"
    ${OA_ROOT}/env/bin/opsagent stop-end
    ;;
  restart-end)
    echo "Restarting opsagent waiting recipe end"
    ${OA_ROOT}/env/bin/opsagent restart-end
    ;;
  restart)
    echo "Restarting opsagent"
    ${OA_ROOT}/env/bin/opsagent /etc/opsagent.conf restart
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|stop-wait|restart-wait|stop-end|restart-end}"
    exit 1
    ;;
esac

exit 0
