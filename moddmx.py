#!/usr/bin/python
# -*- coding: utf-8 -*-

# modDMXthread.py for limux environments
# uses http://www.erwinrol.com/open-dmx-usb-linux-driver/
# you may have to rmmod ftdi_soi, which will bork any other usb-serial 
# unless you are more gifted in the kernel hacking department than me

import sys
import serial

# import struct

import time
import math
import colorsys
import Queue
import threading




ser = open("/dev/dmx0",'w')

nullstr = u'00 ' * 513  # must start with null byte
Ustr = u'00 ' * 513  # must start with null byte
buf = bytearray.fromhex(Ustr)


while(True):

    for i in range(255):
        buf[4] = i
        buf[5] = i
        buf[6] = i
        buf[7] = i
        # and send it
        ser.write(buf)
        ser.flush()
        #print "wrote val %d " % i
        #time.sleep(0.03)
        sys.stdout.flush()
    print "255 frames" + repr(len(buf))
    print repr(buf[4])
    sys.stdout.flush()
