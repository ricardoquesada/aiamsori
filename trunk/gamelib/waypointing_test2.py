import cocos
from cocos.director import director
from cocos.sprite import Sprite
import os,pyglet
from math import cos,sin,radians
import geom

wps = [
    (0,3),   (1,3),  (2,3),  (3,3),
    (0,2),                   (3,2),
    (0,1),                   (3,1),
    (0,0),   (1,0),  (2,0),  (3,0),
    ]
scale = 100.0
radius = 1.0
center = (3/2.0, 3/2.0)

offset = 200.0
fstep = 0.25


class TestLayer(cocos.layer.Layer):
    is_event_handler = True
    def __init__(self):
        super( TestLayer, self ).__init__()
        psize = 5.0
        self.vnodes = []
        self.add_circle(center,radius)
        self.add_wpts(wps)
        self.add_line(wps[0],wps[1])
        
    def add_wpts(self,wpts):
        sprites = []
        for x,y in wps:
            b = Sprite('data/npoint.png')#,color=(140,140,140))
            b.x = x*scale+offset
            b.y = y*scale+offset
            b.scale = 1.0/8.0
            self.add(b,name='%s %s'%(x,y))
            sprites.append(b)
        return sprites

    def add_circle(self,center,radius):
        cx , cy = center
        sprites = []
        for a in xrange(0, 360, 8):
            b = Sprite('data/npoint.png')#,color=(140,140,140))
            b.x = (cx + radius*cos(radians(a)))*scale+offset
            b.y = (cy + radius*sin(radians(a)))*scale+offset
            b.scale = 1.0/16.0
            self.add(b)
            sprites.append(b)
        return sprites
            
    def add_named_line(self, p0,p1):#,color):
        step = int(fstep*scale)
        x0 , y0 = p0
        x1 , y1 = p1
        d = geom.dist(p0,p1)
        a = fstep
        sprites = []
        while a<d:
            b = Sprite('data/npoint.png')#,color=(140,140,140))
            b.x = (a*x0 + (1-a)*x1)*scale + offset
            b.y = (a*y0 + (1-a)*y1)*scale + offset
            b.scale = 1.0/16.0
            self.add(b)#,name=('L%s %s %s %s'%(int(b.x),int(b.y),x1,y1)))
            sprites.append(b)
            a += fstep
        return sprites
        
            
                     


print 'test building graph executed - Interactive test'

if __name__ == "__main__":
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=800, height=600)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)
