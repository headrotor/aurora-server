#!/usr/bin/python
import random
import sys
import numpy
import colorsys
import os
import PIL

PYGAME_OK = True
try:
    import pygame
except ImportError:
    PYGAME_OK = False

MATPLOT_OK = True
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors
except ImportError:
    MATPLOT_OK = False



# local classes:
import imagemunger

class Palettes():

    def __init__(self):
        self.qual_names = ['Accent', 'Dark2', 'hsv', 'Paired', 'Pastel1',
                             'Pastel2', 'Set1', 'Set2', 'Set3', 'spectral']

    def get_all(self):
        """ generate all palettes and return in a list"""
        pals = {}
        if MATPLOT_OK:
            pals['grayscale'] = self.grayscale()

            for name in self.qual_names:
                pals[name] = self.get_matplot_cmap(name)

        self.get_all_cmaps("/home/aurora/aurora-server/palettes/",pals)
            
        return pals

    def flame(self):
        gstep, bstep = 75, 150
        cmap = numpy.zeros((256, 3))
        cmap[:, 0] = numpy.minimum(numpy.arange(256) * 3, 255)
        cmap[gstep:, 1] = cmap[:-gstep, 0]
        cmap[bstep:, 2] = cmap[:-bstep, 0]
        return cmap  

    def get_matplot_cmap(self,cmap_name):
        cmap=plt.get_cmap(cmap_name)
        cmap = cmap(range(256))
        #print repr(cmap)
        sys.stdout.flush()
        return(255*cmap)


    def grayscale(self):
        """grayscale """
        segmentdata = { 'red': [(0.0, 0.0, 0.0),
                                (1.0, 255.0, 255.0)],
                        'green': [(0.0, 0.0, 0.0),
                                (1.0, 255.0, 255.0)],
                        'blue': [(0.0, 0.0, 0.0),
                                (1.0, 255.0, 255.0)]}


        cmap = matplotlib.colors.LinearSegmentedColormap('foo',segmentdata)
        return [ cmap(1.*i/256) for i in range(256)]

    def get_cmap_image(self, fname):
        img = imagemunger.ImageData(fname, 256)        
        row = img.getrow(0)
        cmap_out = []
        for c in row:
            #print repr(c)
            rgb = colorsys.hsv_to_rgb(c[0]/255.0,c[1]/255.0,c[2]/255.0)
            #print repr(rgb)
            cmap_out.append((int(rgb[0]*255),int(rgb[1]*255),int(rgb[2]*255)))
        return cmap_out


    def get_all_cmaps(self,imgdir,cmap_list): 
       
        for f in os.listdir(imgdir):
            fname = os.path.join(imgdir, f)
            print fname
            if os.path.isfile(fname):
                base, ext = os.path.splitext(os.path.basename(fname))
          #base = os.path.basename(fname)
                print " b: %s e: %s" % (base, ext)
                if ext.lower() == '.png':
                    cmap_list[base] = self.get_cmap_image(fname)
                    print "loading colormap from %s" % fname


class Colormorph():

    def __init__(self, size=(40, 40)):
        self.NX = size[0]
        self.NY = size[1]
        self.fireSurface = pygame.Surface(size, 0, 8 )      
        random.seed()
        self.vals = numpy.zeros((self.NX,self.NY))
        #self.fireSurface.set_palette(self.cmap1)
        self.count = 0

    def iter(self):
        for i in range(self.NX):
            for j in range(self.NY):
                self.vals[i][j] = (self.count + i*self.NX + j) % 255
        self.count = (self.count + 1) % 255


    def getFireSurface(self):
        self.iter()
        
        pygame.surfarray.blit_array(self.fireSurface, self.vals.astype('int'))
        return self.fireSurface


class Ripple():
    """Ripple out from inside to outside"""


    def __init__(self, size=(40, 15)):
        self.NX = size[0]
        self.NY = size[1]
        #self.fireSurface = pygame.Surface(size, 0, 8 )      
        #random.seed()
        #P = Palettes()
        #self.cmap1 = P.get_cmap('Pastel1')
        #print repr(self.cmap1)
        
        self.vals = numpy.zeros((self.NX,self.NY))
        self.smooth = 0.0
        #self.fireSurface.set_palette(self.cmap1)
        self.count = 0

    def iter(self):
        for i in range(self.NX):
            for j in range(self.NY):
                #if i == self.count: # roatate around
                if j == self.count: # inside out
                    self.vals[i,j] = 255
                else:
                    self.vals[i,j] = 0

        k = 0.25*numpy.ones((5))
        k[0] = 0.2
        k[1] = 0.5
        k[2] = 1.0
        k[3] = 0.5
        k[4] = 0.2
        k = k / 2.4
        
# smooth shift inside out
        for j in range(self.NY):
            sys.stdout.flush()
            foo= numpy.convolve(self.vals[:,j],k,'same')            
            self.vals[:,j] = foo



# smooth rotate
        # for j in range(self.NY):
        #     sys.stdout.flush()
        #     #print "before " + repr(self.vals[i,:])
        #     foo= numpy.convolve(self.vals[:,j],k,'same')            
        #     #print "after " + repr(foo)
        #     self.vals[:,j] = foo[:]


        self.count = (self.count + 1) 
        print self.count
        sys.stdout.flush()
        if self.count >= self.NY:
            self.count = 0

    def get_frame(self):
        #self.disturb()
        """ after an iteration, get the new matrix of color vals"""
        return(self.vals.tolist())

    def disturb(self):
        pass


    # def getFireSurface(self):
    #     self.iter()
        
    #     pygame.surfarray.blit_array(self.fireSurface, self.vals.astype('int'))
    #     return self.fireSurface



class WaveEqn():

    def __init__(self, size=(40, 40)):
        self.imcount = 0
        self.NX = size[0]
        self.NY = size[1]
        self.vold = 0
        self.old = 1
        self.new = 2
        self.damp = 0.999
        self.depth = 3
        self.max = 255
        self.coolingFactor = 10


        # make 3d array
        self.vals = numpy.zeros((self.depth,self.NX,self.NY))
        #for d in range(self.depth):
        #    self.vals.append([[0.0 for x in xrange(nx)] for y in xrange(ny)])


        #self.fireSurface = pygame.Surface(size, 0, 8 )      
        #P = Palettes()
        #self.cmap1 = P.get_cmap('Pastel1')
        #self.fireSurface.set_palette(self.cmap1)
        random.seed()

    def iter(self):
        """compute one iterationof the wave equation"""
        old = self.old # last iteration
        for x in range(1,self.NX-1):
            for y in range(1,self.NY-1):
                n =  0.1*(self.vals[old][x-1][y] + self.vals[old][x+1][y] + \
                              self.vals[old][x][y-1] + self.vals[old][x][y+1] - \
                              4*self.vals[old][x][y])
                n += 2*self.vals[old][x][y]

               #this is actual t-2 term
                n -= self.vals[self.vold][x][y];
      

                # bound to +/- 1 *
                if n >= self.max:
                    n = self.max
                elif n <= 0:
                    n = 0.0
                self.vals[self.new][x][y] = n * self.damp;
  
            # enforce boundary conditions */
            #done by default as vals[*][*][0] are unmolested and stay zero */
  
  # swap indices */
        self.vold = old
        self.old = self.new
        self.new = self.new + 1
        if(self.new >= self.depth):
            self.new = 0

        #print "Just computed new frame %d from frame %d\n" % (self.new,self.old)
        sys.stdout.flush()
  #if(opt->verbose &0) printf("vals[5][5] = %f\n",vals[old][5][5]);


    # def printvals(self):
    #     """Print the latest calculation to screen"""
    #     print repr(self.vals[self.old])


    # def writeimg(self):
        
    #     """Print the latest calculation to screen"""
    #    print repr(self.vals[self.old][1])
    #     cm = plt.get_cmap('gist_earth')
    #     im = Image.fromarray(cm(self.vals[self.old], bytes=True))
    #     im.save("foo%d.png" % self.imcount)
    #     self.imcount += 1

    def disturb_x(self):
        x = self.old
        for i in range(self.NX):
            self.vals[x][i][0] += random.randint(-self.max/2,self.max/2)
            if self.vals[x][i][0] > 255:
                self.vals[x][i][0] = 255
            if self.vals[x][i][0] < 1:
                self.vals[x][i][0] = 0
            #self.vals[x][i][1] = self.vals[x][i][0]
            #self.vals[x][i][2] = self.vals[x][i][0]

    def disturb_y(self):
        x = self.old
        for j in range(self.NY):
            self.vals[x][0][j] += random.randint(-self.max/2,self.max/2)
            if self.vals[x][0][j] > 255:
                self.vals[x][0][j] = 255
            if self.vals[x][0][j] < 1:
                self.vals[x][0][j] = 0
            #self.vals[x][1][j] = self.vals[x][0][j]

    def get_frame(self):
        self.disturb_x()
        """ after an iteration, get the new matrix of color vals"""
        return(self.vals[self.old].tolist())

    def getFireSurface(self):
        self.disturb()
        self.iter()
        
        pygame.surfarray.blit_array(self.fireSurface, self.vals[self.old].astype('int'))
        return self.fireSurface


class CheeseFlame:
    def __init__(self, size=(40, 40), coolingFactor=5, fuelRange=(-31, 32)):
        self.__width, self.__height = size
        self.coolingFactor = coolingFactor
        self.fuelRange = fuelRange

        self.__array = numpy.zeros((self.__width, self.__height))
        self.__fireSurface = pygame.Surface((self.__width, self.__height), 0, 8)
        P = Palettes()
        self.cmap1 = P.get_cmap('Pastel1')
        self.__fireSurface.set_palette(self.cmap1)

        random.seed()

    def getFireSurface(self):
        tempArray = numpy.zeros(self.__array.shape)
        for r in range(0, self.__width):
            for c in range(0, self.__height):
                tempArray[r, max(0, c - 1)] = min(255, max(0, (int(self.__array[max(0, r - 1), c]) + int(self.__array[min(self.__width - 1, r + 1), c]) + int(self.__array[r, max(0, c - 1)]) + int(self.__array[r, min(self.__height - 1, c + 1)])) / 4 - self.coolingFactor))

        for r in range (0, self.__width, 2):
            fuel = min(255, max(0, self.__array[r, self.__height - 1] + random.randint(*self.fuelRange)))

            tempArray[r, self.__height - 1] = fuel
            tempArray[r + 1, self.__height - 1] = fuel

        self.__array = tempArray
        pygame.surfarray.blit_array(self.__fireSurface, self.__array.astype('int'))
        return self.__fireSurface

#######################################
