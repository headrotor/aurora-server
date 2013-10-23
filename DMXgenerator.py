#!/usr/bin/python
from multiprocessing import Process, Pipe
import os
import sys
import time #For the timestamp and sleep function
import urlparse # decode the messages we are sent
if sys.platform == "win32":
  # On Windows, the best timer is time.clock()
  default_timer = time.clock
else:
  # On most other platforms, the best timer is time.time()
  default_timer = time.time


def info(title):
    print title
    print 'module name:', __name__
    if hasattr(os, 'getppid'):  # only available on Unix
        print 'parent process:', os.getppid()
    print 'process id:', os.getpid()

def listener(myP,foo):

    info('function f')
    while(1):
        if myP.poll():
            msg = myP.recv()
            print 'DMX received "%s"' % str(msg)
            sys.stdout.flush()
            print msg
            #if msg == "foo":
            #    assert(False)
            myP.send('DMX OK')
        else:
            time.sleep(0.1)

if __name__ == '__main__':
    info('main line')
    parentP, childP = Pipe()
    p = Process(target=f, args=(childP,"foo"))
    p.start()
    for i in range(10):
        parentP.send("message %d"  % i)
        time.sleep(1)
    #p.join()
