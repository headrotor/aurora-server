#!/usr/bin/python

# This child process is called by DMX server. It generatively creates DMX 
# patterns. If the server sends it a message from the web interface, it 
# responds with an appropriate pattern. 

from multiprocessing import Process, Pipe
import os
import sys
import struct
import time #For the timestamp and sleep function
import urlparse # decode the messages we are sent


# local classes
from modDMXthread import DMXUniverse
import aurora

import logging
logger = logging.getLogger(__name__)

if sys.platform == "win32":
  # On Windows, the best timer is time.clock()
  default_timer = time.clock
else:
  # On most other platforms, the best timer is time.time()
  default_timer = time.time

# global vars
tree = None



def info(title):
    print title
    print 'module name:', __name__
    if hasattr(os, 'getppid'):  # only available on Unix
        print 'parent process:', os.getppid()
    print 'process id:', os.getpid()

class activeTree(object):
  """ class for doing all the DMX generation stuff"""

  def __init__(self, auroratree):
    self.tree = auroratree
    self.state = "idle"




  def do_test(self,colors,pd,lm,br):
    #   tree.uni0.set_chan_int(i+0, colors[0])
    #   tree.uni0.set_chan_int(i+1, colors[1])
    #   tree.uni0.set_chan_int(i+2, colors[2])
     #univ1.set_chan_int(i, val)
    self.state = "test"
    for bri in range(len(self.tree.branches)):
      self.tree.setBranchInt(bri,(0,0,0))
      #print "sent %d to %s" % (bri,repr(colors))

    if pd < 0 or br < 0 or lm < 0:
      return 'vals must be > 0'
    if pd >= len(self.tree.pods):
      return 'max pod is %d' % len(self.tree.pods) + 1
    pod = self.tree.pods[pd]
    if lm >= len(pod.limbs):
      return 'max limb is %d' % len(pod.limbs) + 1
    limb = pod.limbs[lm]
    if br >= len(limb.branches):
      return 'max branch is %d' 
    br = limb.branches[br]
    self.tree.setBranchInt(br.brindex,colors)
    return 'test OK'


  def update(self):
    """ call this repeatedly to generate new data and update things"""
    if self.state == "idle":
      self.idle()
    self.tree.TreeSend()


  def on_idle(self):
    # if we are not running a user pattern, then do this...


def listener(myP,foo):
  """ This is started by the parent to do all the things..."""

    #info('function f')
  logger.info('DMX listener started, pid: %s',str(os.getppid()))
    #univ0 = DMXUniverse('/dev/dmx0')
    #univ1 = DMXUniverse('/dev/dmx1')

    
  auroratree = aurora.AuroraDMX("mapDMX.cfg")
  tree = activeTree(auroratree)

  while(1):
    if myP.poll():
      msg = myP.recv()
      print 'DMX received "%s"' % str(msg)
      logger.debug('DMX received "%s"',str(msg))
      sys.stdout.flush()
      print msg
            #if msg == "foo":
            #    assert(False)
      try:
        func = msg['function'][0].strip("'")
      except KeyError:
        logger.debug("Badly formed URL, skipping")
        myP.send('Badly formed URL')
      else:
        print "function: " + repr(func)
        if func == 'test':
          cstr = msg['colors'][0].strip("'")
          colors =  struct.unpack('BBB',cstr.decode('hex'))

                #print repr(colors)
          pd = int(msg['p1'][0]) - 1
          lm = int(msg['p2'][0]) - 1
          br = int(msg['p3'][0]) - 1
          # for i in range(0,256,3):

          result = tree.do_test(colors,pd,lm,br)
          myP.send(result)

        #tree.uni0.send_buffer()
        # call this repeatedly to send the latest data
    tree.update()        
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
