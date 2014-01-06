import threading
import time

def thread_one(event):
    print "1: start"
    print "1: wait condition"
    event.wait()
    print "1: wait success"
    print "1: clear event"
    event.clear()
    print "1: exit"


def thread_two(cond_var):
    print "2: start"
    print "2: sleep 3sec"
    time.sleep(3)
    print "2: notify"
    cond_var.notify()
    print "2: done"


if __name__ == "__main__":
    event=threading.Event()
    t1 = threading.Thread(target=thread_one, kwargs={"event":event})
    print "running thread"
    t1.start()
    print "sleep 3sec"
    time.sleep(3)
    print "notify event"
    event.set()
    t1.join()
    print "all good"
