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
import colorsys
import ConfigParser


# local classes
from modDMXthread import DMXUniverse
#from generative import WaveEqn as IterEffect
import generative 
import aurora
import random

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
    self.cfg = ConfigParser.RawConfigParser()


    self.brightness = 0.5
    self.hue = 0.0              # hue offset
    self.saturation = 1.0
    self.cfgfile = "defaults.cfg"
    self.update_config() # read config options from file
    self.stop_timer() # put timer in known state
    # instantiate iterative effect
    self.effects = []  # array of effects from  generative.py
    size = (22,15)
    self.effects.append(generative.Ripple(size))
    self.effects.append(generative.WaveEqn(size))

    P = generative.Palettes()
    self.palletes = P.get_all()
    self.current_pal = 'grayscale'

    self.cef = 1 # current effect
    self.old_frame = self.effects[self.cef].get_frame()
    self.new_frame = self.effects[self.cef].get_frame()
    self.interc = 0 # count for interpolation
    self.framec = 3 # if non-zero, interpolate new frame

  def start_timer(self):
    """ Start a timer for time-limited operations"""
    self.clock = default_timer()

  def stop_timer(self):
    self.clock = None
    
  def time_elapsed(self):
    """ return time elapsed since we started the clock"""
    if self.clock is None:
      return 0.0
    return default_timer() - self.clock


  def tree_dark(self):
    """ Turn all branches this color"""
    for bri in range(len(self.tree.branches)):
      self.tree.setBranchInt(bri,(0,0,0))
      #print "sent %d to %s" % (bri,repr(colors))

  def do_test(self,colors,pd,lm,br):
    #   tree.uni0.set_chan_int(i+0, colors[0])
    #   tree.uni0.set_chan_int(i+1, colors[1])
    #   tree.uni0.set_chan_int(i+2, colors[2])
     #univ1.set_chan_int(i, val)
    self.state = "test"

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
      self.update_iter()

  def send_frame(self,frame): 
    """ send the following frame """
    i = 0
    for pod in self.tree.pods:
      for limb in pod.limbs:
        for j, br in enumerate(limb.branches):
          index = int(frame[i+1][j+1]) # skip borders used for padding
          p = self.palletes[self.current_pal]
          c = p[index]
          #hsv = list(colorsys.rgb_to_hsv(c[0],c[1],c[2]))
          
          #morph color here with brightness and hue shift
          #hsv[2] = self.brightness * 2.0
          #hsv[1] = self.saturation * hsv[1]

          #rhue = 0.05 * (random.random() + 0.5) 
          #hsv[0] = hsv[0] + self.hue + rhue
          #if hsv[0] > 1.0:
          #  hsv[0] -= 1.0

          #hsv[0] = self.hue
          #hsv[1] = 0.5
          #hsv[1] = 0.8
          
          #rgb = colorsys.hsv_to_rgb(hsv[0],hsv[1],hsv[2])
          #print repr(rgb)

          #color = (int(rgb[0]),int(rgb[1]),int(rgb[2]))
          color = (int(c[0]),int(c[1]),int(c[2]))

          #print "index %d, color %s" % (index, repr(color))
          #sys.stdout.flush()
          self.tree.setBranchInt(br.brindex,color)
          #if i == 10 and j == 2:
          #  print "index %d, color %s" % (index, repr(color))
        i += 1

  def update_iter(self):
    """ Get the latest frame from the pattern, and do it..."""
    self.interc += 1
    if self.interc >= self.framec:
      self.interc = 0
      self.effects[self.cef].iter()
      self.old_frame = self.new_frame
      self.new_frame = self.effects[self.cef].get_frame()
      #print repr(self.new_frame[1])


    frame = self.old_frame
    if self.framec > 0:
      frac = float(self.interc/float(self.framec))
      for i, row in enumerate(frame):
        for j, el in enumerate(row):
          frame[i][j] = int((1 - frac)*frame[i][j] + frac*(self.new_frame[i][j]))
    #print self.interc
    sys.stdout.flush()
    self.send_frame(frame)
    self.tree.TreeSend()
    

  def set_colormap(self,colormap):
    pass

  def update_config(self):
    """read (or reread) config file in case anything has changed"""
    self.cfg.read(self.cfgfile)
    logger.info('read config file ' + self.cfgfile)
    print 'read config file ' + self.cfgfile
    hue = None
    brightness = None
    try:
      brightness = self.cfg.getfloat('mod','mod_bright')
      hue = self.cfg.getfloat('mod','mod_hue')
    except AttributeError as e:
      logger.error("error reading config file " + self.cfgfile)
      logger.error(repr(e))
      print repr(e)

    if hue is not None:
      if self.hue != hue:
        self.hue = hue
        logger.info("Changing hue from %f to %f" % (self.hue,hue))
        print "Changing hue from %f to %f" % (self.hue,hue)

def listener(myP,foo):
  """ This is started by the parent, listens for commands coming in on 
  queue myP"""

  logger.info('DMX listener started, pid: %s',str(os.getppid()))
  # maps Aurora branch topology to DMX channels
  auroratree = aurora.AuroraDMX("mapDMX.cfg")
  # makes an interactive tree object
  tree = activeTree(auroratree)

  while(1):
    if myP.poll():
      tree.update_config() # read config options from file
      msg = myP.recv()
      print 'DMX received "%s"' % str(msg)
      logger.debug('DMX received "%s"',str(msg))
      sys.stdout.flush()

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

          #result = tree.do_test(colors,pd,lm,br)
          tree.cef = 1
          myP.send('changed')
        elif func == 'sparkle':
          tree.cef = 0
          cstr = msg['colors'][0].strip("'")
          c =  struct.unpack('BBB',cstr.decode('hex'))
          hue = colorsys.rgb_to_hsv(c[0]/255.0,c[1]/255.0,c[2]/255.0)
          tree.hue = hue[0]
          tree.speed = int(msg['speed'][0]) 
          tree.interc = 0
          tree.framec = int(tree.speed/5)
          myP.send("new hue %f" % tree.hue)
        #tree.uni0.send_buffer()
        # call this repeatedly to send the latest data
        elif func == 'winter':
          tree.current_pal = 'grayscale'
        elif func == 'summer':
          tree.current_pal = 'hsv'


    tree.update()        
        #univ1.send_buffer()
    time.sleep(0.02)


if __name__ == '__main__':
  
    parentP, childP = Pipe()
    p = Process(target=f, args=(childP,"foo"))
    p.start()
