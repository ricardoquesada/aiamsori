import math
screen = None
import pygame

fe = 1.0e-4
def create_ray_to_wall_collision(wallmask, tilesize):
    def ray_to_wall_collision((x0,y0),(hx,hy)):
        #(hx,hy)direction.
        # asumes the initial position is free
        # asumes wallmask raises KeyError when out of the map
        scale = float(tilesize)
        x0 = x0/scale
        y0 = y0/scale
        hx = hx/scale
        hy = hy/scale
        hitpoint = None

        if abs(hx)<fe:
            # near horizontal
            xe = math.floor(x0)
            ye = math.floor(y0)
            if hx>0:
                dx = 1
            else:
                dx = -1
            try:
                while 1:
                    xe += dx
                    if wallmask[xe,ye]:
                        break
            except KeyError:
                return None
            # ignores the y displacement
            if dx<0:
                xe = xe+1
            hitpoint = xe*scale, y0*scale
            #tambien se puede entregar que cara del wall si necesario
            return hitpoint

        if abs(hy)<fe:
            # near vertical
            xe = math.floor(x0)
            ye = math.floor(y0)
            if hy>0:
                dy = 1
            else:
                dy = -1                
            try:
                while 1:
                    ye += dy
                    if wallmask[xe,ye]:
                        break
            except KeyError:
                return None
            # ignores the y displacement
            if dy<0:
                ye +=1 
            hitpoint = x0*scale, ye*scale
            #tambien se puede entregar que cara del wall si necesario
            return hitpoint

        # oblique case
        xe = math.floor(x0)
        if hx>0:
            dx = 1
        else:
            dx = -1
        tx = (xe+dx-x0)/hx # next t for wich the x coord will be int
        assert(tx>=0.0)
        
        ye = math.floor(y0)
        if hy>0:
            dy = 1
        else:
            dy = -1
        ty = (ye+dy-y0)/hy # next t for wich the y coord will be int
        assert(ty>=0.0)
        
        while 1:
            # advances to the next time we cross a frontier
            if abs(tx-ty)<fe:
                # pasing near a corner, sample all neighboors
                hit = False
                try:
                    hit = hit or wallmask(xe,ye+dy)
                except KeyError:
                    pass
                try:
                    hit = hit or wallmask(xe+dx,ye)
                except KeyError:
                    pass
                try:
                    hit = hit or wallmask(xe+dx,ye+dy)
                except KeyError:
                    pass
                if hit:
                    # declare hit, hitpoint the corner (rescaled)
                    x = (xe+dx)*scale
                    y = (ye+dy)*scale
                    hitpoint = x, y
                    return hitpoint
                else:
                    xe += dx
                    tx = (xe+dx-x0)/hx
                    ye += dy
                    ty = (ye+dy-y0)/hy

            else:
                # sample at t=(tx+ty)/2
                t = (tx+ty)/2.0
                x = x0 + t*hx
                y = y0 + t*hy
                try:
                    hit = wallmask[int(x),int(y)]
                except KeyError:
                    # out of map, no hit
                    return None
                if hit:
                    # hit , hitpoint the point at t=min(tx,ty), rescaled
                    t = min(tx,ty)
                    x = (x0 + t*hx)*scale
                    y = (y0 + t*hy)*scale
                    hitpoint = x,y
                    return hitpoint
                else:
                    if tx<ty:
                        xe += dx
                        tx = (xe+dx-x0)/hx
                    else:
                        ye += dy
                        ty = (ye+dy-y0)/hy
                        
    return ray_to_wall_collision

def wait_keypress():
    bRun = True
    while bRun:
        pygame.event.pump()
        for ev in pygame.event.get():
            if (ev.type == pygame.KEYDOWN
                and ev.key == pygame.K_ESCAPE):
                bRun = False
    pygame.display.update()

def test_create_ray_to_wall_collision():
    import pygame
    global screen
    
    wallmask = {}
    for i in xrange(10):
        for j in xrange(10):
            wallmask[i,j] = 0
    i = 0
    for j in xrange(10):
        wallmask[i,j] = 1
    i = 9
    for j in xrange(10):
        wallmask[i,j] = 1
    j = 0
    for i in xrange(10):
        wallmask[i,j] = 1
    j = 9
    for i in xrange(10):
        wallmask[i,j] = 1
 
    pygame.init()
    tilesize = 60
    screen = pygame.display.set_mode((800,600))
    screen.fill((220,220,220))
    for i in xrange(10):
        for j in xrange(10):
            if wallmask[i,j]:
                pygame.draw.rect(screen, (46,80,46), (i*tilesize,j*tilesize,tilesize,tilesize))
    fn_ray_collide = create_ray_to_wall_collision(wallmask, tilesize)

    x0 = tilesize*10/3
    y0 = tilesize*10/3

    for a in xrange(0,360,30):
        hx = math.cos(math.radians(a))
        hy = math.sin(math.radians(a))
        print hx,hy

        hitpoint = fn_ray_collide((x0,y0),(hx,hy))
        print hitpoint
        
        if hitpoint is None:
            pygame.draw.line(screen,(255,0,0),(x0,y0),(x0+200*hx,y0+200*hy))
        else:
            #pygame.draw.line(screen,(0,255,0),(x0,y0),(x0+800*hx,y0+800*hy))
            pygame.draw.line(screen,(0,0,0),(x0,y0),(int(hitpoint[0]), int(hitpoint[1])))

    pygame.display.update()

    bRun = True
    while bRun:
        pygame.event.pump()
        for ev in pygame.event.get():
            if (ev.type == pygame.KEYDOWN
                and ev.key == pygame.K_ESCAPE):
                bRun = False
    pygame.quit()

if __name__ == '__main__':
    test_create_ray_to_wall_collision()
    
                             
    

    
