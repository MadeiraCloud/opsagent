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
    /madeira/env/bin/opsagent start
    ;;
  stop)
    echo "Stopping opsagent"
    /madeira/env/bin/opsagent stop
    ;;
  stop-wait)
    echo "Stopping opsagent"
    /madeira/env/bin/opsagent stop-wait
    ;;
  restart-wait)
    echo "Restarting opsagent"
    /madeira/env/bin/opsagent restart-wait
    ;;
  restart)
    echo "Restarting opsagent"
    /madeira/env/bin/opsagent restart
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|stop-wait|restart-wait}"
    exit 1
    ;;
esac

exit 0
