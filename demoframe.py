
'''

demoframe:
pygame based frame to display generative color patterns
based on FlameEffect by grayger http://www.grayger.com/
'''

import pygame
from pygame.locals import *
import sys

#from generative import Colormorph as FlameEffect
#from generative import Colormorph as FlameEffect
#from generative import CheeseFlame as FlameEffect
from generative import WaveEqn as FlameEffect

pygame.init()
screen = pygame.display.set_mode((320, 120), 0, 8 )
fireEffect = FlameEffect()

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_a and fireEffect.coolingFactor < 10:
                fireEffect.coolingFactor += 1
            elif event.key == K_z and fireEffect.coolingFactor > 1:
                fireEffect.coolingFactor -= 1

    fireSurface=fireEffect.getFireSurface()
    # draw the original fire image
    screen.blit(fireSurface, (0,0))    

    # draw the scaled and mirrored fire image
    pos = (0, 40)
    fireSurface = pygame.transform.scale(fireSurface, (80, 80))
    fireSurface2 = pygame.transform.flip(fireSurface, True, False)
    for i in range(0, 4, 2):
        screen.blit(fireSurface, (pos[0] + fireSurface.get_width()*i, pos[1]))
        screen.blit(fireSurface2, (pos[0] + fireSurface.get_width()*(i + 1), pos[1]))

    clock.tick(30)
    pygame.display.flip()

#######################################    
