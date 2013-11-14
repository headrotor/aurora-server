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
import imagemunger # get tree colors repeatedly from image file
import generative # iteratively generate tree colours
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
ticks = default_timer()

tree = None


def info(title):
    print title
    print 'module name:', __name__
    if hasattr(os, 'getppid'):  # only available on Unix
        print 'parent process:', os.getppid()
    print 'process id:', os.getpid()


class OpTimer(object):
    """ Timer and timeout functions. Must call update() regularly!"""
    def __init__(self):
        self.time_remain = 0.0          # running  time remaining, seconds
        self.idle = True
        self.timeout = False            # timout flag, clear with stop()
        self.start_time = self.last_time = self.the_time()
        self.verbose = True

    def the_time(self):
        """Wrapper for time.clock or time.time which are os-dependent"""
        return default_timer()

    def update(self):
        """Update timer, must call this periodically from timer 
        callback 
        """
        now = self.the_time()
        delta_time = now - self.last_time
        if self.idle is False:
          self.time_remain -= delta_time
          if self.verbose:
            print "evt timer running at " + str(self.time_remain)
            sys.stdout.flush()
          if self.time_remain < 0:
            print "timer timeout"
            # set timout flag, clear/acknowledge with self.stop()
            self.timeout = True
          else:
            self.last_time = now   
        return delta_time

    def start(self,remain):
        """ Start the countdown timer for time seconds"""
        self.timeout = False
        self.idle = False
        self.time_remain = remain
        self.last_time = self.start_time = self.the_time()
        if self.verbose:
            print "start clock for %f secs" % float(remain)
            sys.stdout.flush()

    def stop(self):
      self.idle = True
      self.timeout = False

    def get_time_elapsed(self):
        if self.idle:
            return 0.0
        else:
            return self.the_time() - self.start_time


class activeTree(object):
  """ class for doing all the DMX generation stuff"""

  def __init__(self, auroratree):
    self.tree = auroratree
    self.state = "idle"
    self.cfg = ConfigParser.RawConfigParser()
    self.timer = OpTimer()

    # load all the images into an image dict
    self.imgs = self.load_images("/home/aurora/aurora-server/images")
    self.im_row = 0  # image row counter
    self.img_count = 1  # play images this many times before returning

    self.brightness = 0.5
    self.hue = 0.0              # hue offset
    self.saturation = 1.0

    self.cfgfile = "defaults.cfg"



    # instantiate iterative effect
    self.effects = []  # array of effects from  generative.py
    size = (22,15)
    self.effects.append(generative.Ripple(size))
    self.effects.append(generative.WaveEqn(size))

    P = generative.Palettes()
    # palettes are a dict, indexed by name
    self.palettes = P.get_all()

    print "avail palettes:"
    for key in self.palettes:
      print repr(key)

    print "avail images:"
    for key in self.imgs:
      print repr(key)

    self.mode = None
    self.cef = None
    self.current_pal = None
    self.interc = 0 # count for interpolation
    self.framec = None # if non-zero, interpolate new frame

    self.update_config() # read config options from file
    # set default mode, etc. from config file
    self.set_mode('default')
    
    # tree state machine: idle (dark), image, generative 
    self.old_frame = self.effects[0].get_frame()
    self.new_frame = self.effects[0].get_frame()



  def load_images(self, imgdir):
    """ scan image directory, load images """

    # make list of image files 
    self.imfiles = []
    imgs = {}
    for f in os.listdir(imgdir):
      fname = os.path.join(imgdir, f)
      print fname
      if os.path.isfile(fname):
          base, ext = os.path.splitext(os.path.basename(fname))
          #base = os.path.basename(fname)
          print " b: %s e: %s" % (base, ext)
          if ext.lower() == '.png':
            img = imagemunger.ImageData(fname, len(self.tree.branches))
            imgs[base] = img
            print 'loading image "%s"' % base 
    return imgs

  def set_image(self, key):
    if key in self.imgs:
      self.imd = self.imgs[key]
      print "setting image to " + key
      self.im_row = 0
    else:
      logger.info("Can't find image named %s" % key)
      print "Can't find image named %s" % key

  def set_palette(self, key):
    if key in self.palettes:
      self.current_pal = self.palettes[key]
      print "setting palette to " + key
    else:
      logger.info("Can't find palette named %s" % key)      

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

    self.timer.update()  
    if self.timer.timeout: # got timer flag
      print "got timeout flag"
      self.timer.stop()
      self.set_mode('default')

    if self.mode == 'image':
      self.update_image()
    elif self.mode == 'generate':
      self.update_iter()
    elif self.mode == 'test':
      pass



  def send_frame(self,frame): 
    """ send the following frame """
    i = 0
    for pod in self.tree.pods:
      for limb in pod.limbs:
        for j, br in enumerate(limb.branches):
          index = int(frame[i+1][j+1]) # skip borders used for padding
          c = self.current_pal[index]

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

  def update_image(self):
    """Get next row of image file, and do it """
    self.im_row = self.im_row + 1
    if self.im_row >= self.imd.y:
      self.im_row = 0

    r = self.im_row
    self.interc += 1
    if self.interc >= self.framec:
      self.interc = 0
      row = self.imd.getrow(r)
    else: # cross-fade from previous frame
      row = self.imd.getrowinterp(r,self.interc/float(self.framec))
              
    for b, pixel in enumerate(row):
              # set each branch to the corresponding pixel in this row
              #treeDMX.setBranchRGB(b,pixel)
      brindex = self.tree.branches[b].brindex
      self.tree.setBranchInt(brindex,pixel)
    self.tree.TreeSend()

  def update_iter(self):
    """ in generative mode, calc latest pattern and and do it..."""
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


  def set_mode(self,function,duration=None):
    """ named modes read mode from config file, set tree commands """

    if function != 'default':
      if duration is not None:
        self.timer.start(duration)

    newmode = None
    try:
      newmode = self.cfg.get(function,'mode')
    except ConfigParser.NoSectionError:
      logger.error("No config section named %s" % function)
      print "No config section named %s" % function
      return
    except ConfigParser.NoOptionError:
      logger.info("No config option named %s" % 'mode')
      print ("No config option named %s in section %s" % ('mode',function))
      return

    self.mode = newmode

    smooth = None
    if smooth is None:
      try:
        framec = self.cfg.getfloat(function,'framec')
      except ConfigParser.NoOptionError:
        logger.info("No config option for %s" % 'framec')
      else:
        self.interc = 0 # count for interpolation
        self.framec = framec # if non-zero, interpolate new frame
        print "new interp length = %d" % int(self.framec)
    else:
      self.interc = 0 # count for interpolation
      self.framec = int(smooth)
      print "new interp length = %d" % int(self.framec)

    try:
      self.hue = self.cfg.getfloat(function,'hue')
    except ConfigParser.NoOptionError:
      logger.info("No config option named %s" % 'hue')

    try:
      fcount = self.cfg.getint(function,'fcount')
    except ConfigParser.NoOptionError:
      logger.info("No config option %s" % 'fcount')
    else:
      self.fcount = fcount

    print "new mode %s hue %d" % (function, self.hue) 
    if self.mode == 'image':
      try:
        imname = self.cfg.get(function,'image')
      except ConfigParser.NoOptionError:
        logger.info("Error configuring image for mode %s" % self.mode)
        return

      self.set_image(imname)

      try:
        self.img_count = self.cfg.getint(function,'img_count')
      except ConfigParser.NoOptionError:
        pass
      else:
        print "new image %s count %d " % (imname, self.img_count)
        if self.img_count == 0:
          self.img_count = None #@ none means loop forever
    elif self.mode == 'generate':
      try:
        effect = self.cfg.getint(function,'effect_id')
        palette = self.cfg.get(function,'palette')
      except ConfigParser.NoOptionError:
        logger.info("Error configuring generator for mode %s" % self.mode)
        return
      self.cef = effect
      self.set_palette(palette)

def waitrate(frate):
  """ Wait for 1/framerate of a second since the last time we called"""
  global ticks
  delay = float(1/float(frate))
  elapsed = default_timer() - ticks
  sleeptime = delay - elapsed
  if sleeptime > 0:
    time.sleep(sleeptime)

  ticks = default_timer()

############################ message handler, where the interactivity happens
# two classes of patterns: generative and images
# generative patterns run forever, images run for self.img_count of 
# iterations or forever if self.img_count is None


def handle_message(msg,tree):
  """got a message, deal with it"""
  try:
    func = msg['function'][0].strip("'")
  except KeyError:
    logger.debug("Badly formed URL, skipping")
    return 'Badly formed URL'
  
  print "function: " + repr(func)
  if func == 'test':
    tree.mode = 'test'
    cstr = msg['colors'][0].strip("'")
    colors =  struct.unpack('BBB',cstr.decode('hex'))

                #print repr(colors)
    pd = int(msg['p1'][0]) - 1
    lm = int(msg['p2'][0]) - 1
    br = int(msg['p3'][0]) - 1
          # for i in range(0,256,3):

          #result = tree.do_test(colors,pd,lm,br)
    tree.cef = 1
    return 'test OK'
  elif func == 'sparkle':
    tree.mode = 'generate'
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
    smoothparam = int(msg['smooth'][0]) 
    print "got smoothparam %d" % smoothparam
    tree.set_mode('winter',duration=10)

  elif func == 'crash':
    # crash the server to test restart
    logging.info("Test crash!")
    assert(False)

  elif func == 'spring':
    tree.set_mode('spring')
  elif func == 'summer':
    tree.set_mode('summer')
          #tree.current_pal = 'grayscale'
  elif func == 'autumn':
    tree.set_mode('autumn')
          #tree.current_pal = 'hsv'
  return "OK"




### listener: main loop and respond to commands
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

      #if tree.mode == 'image':
      #  myP.send('Sorry, busy, try again!')
      if tree.mode == 'test':
        myP.send('Sorry, tree is being tested')
      else:
        result = handle_message(msg,tree)
        myP.send(result)


    tree.update()        
        #univ1.send_buffer()
    waitrate(20.0)
    #time.sleep(0.02)


if __name__ == '__main__':
  
    parentP, childP = Pipe()
    p = Process(target=f, args=(childP,"foo"))
    p.start()
