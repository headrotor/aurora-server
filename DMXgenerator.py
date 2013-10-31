#!/usr/bin/python

# This child process is called by DMX server. It generatively creates DMX 
# patterns. If the server sends it a message from the web interface, it 
# responds with an appropriate pattern. 

from multiprocessing import Process, Pipe
import os
import sys
import time #For the timestamp and sleep function
import urlparse # decode the messages we are sent
from modDMXthread import DMXUniverse

import logging
logger = logging.getLogger(__name__)

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

    #info('function f')
    logger.info('DMX listener started, pid: %s',str(os.getppid()))
    univ0 = DMXUniverse('/dev/dmx0')
    #univ1 = DMXUniverse('/dev/dmx1')


    while(1):
        if myP.poll():
            msg = myP.recv()
            print 'DMX received "%s"' % str(msg)
            logger.debug('DMX received "%s"',str(msg))
            sys.stdout.flush()
            print msg
            #if msg == "foo":
            #    assert(False)
            func = msg['function'][0].strip("'")
            print "function: " + repr(func)
            if func == 'test':
              print "TEST! "
              val = int(msg['p1'][0])
              for i in range(256):
                univ0.set_chan_int(i, val)
                #univ1.set_chan_int(i, val)
                print "sent %d to %d" % (i,val)
            sys.stdout.flush()
            myP.send('DMX OK')
        # else:
        #     time.sleep(0.1)

        univ0.send_buffer()
        #univ1.send_buffer()
        time.sleep(0.04)

if __name__ == '__main__':
    info('main line')
    parentP, childP = Pipe()
    p = Process(target=f, args=(childP,"foo"))
    p.start()

    for i in range(10):
        parentP.send("message %d"  % i)
        time.sleep(1)
    #p.join()
