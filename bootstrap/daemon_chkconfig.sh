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
# Default-Stop:   0 1 2 6
# Short-Description: Opsagent Daemon
# Description: Runs opsagent
### END INIT INFO

case "$1" in
  start)
    echo "Starting opsagent"
    /madeira/env/bin/opsagent -c /etc/opsagent.conf start
    ;;
  stop)
    echo "Stopping opsagent"
    /madeira/env/bin/opsagent -c /etc/opsagent.conf stop
    ;;
  stop-wait)
    echo "Stopping opsagent"
    /madeira/env/bin/opsagent -c /etc/opsagent.conf stop-wait
    ;;
  restart-wait)
    echo "Restarting opsagent"
    /madeira/env/bin/opsagent -c /etc/opsagent.conf restart-wait
    ;;
  restart)
    echo "Restarting opsagent"
    /madeira/env/bin/opsagent -c /etc/opsagent.conf restart
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|stop-wait|restart-wait}"
    exit 1
    ;;
esac

exit 0
