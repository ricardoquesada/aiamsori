import cocos
from cocos.director import director
from cocos.sprite import Sprite
import os,pyglet
from math import cos,sin,radians
import geom
from waypointing import WaypointNav
from waypointing_test import visiblesball_factory
from cocos.euclid import Vector2 as V2
from pyglet.window import key
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


class TestBedLayer(cocos.layer.Layer):
    is_event_handler = True
    def __init__(self):
        super( TestLayer, self ).__init__()
        
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
            
    def add_line(self,p0,p1,color=(255,255,255)):
        step = int(fstep*scale)
        x0 , y0 = p0
        x1 , y1 = p1
        d = float(geom.dist(p0,p1))
        a = fstep
        sprites = []
        while a<d:
            b = Sprite('data/npoint.png', color=color)
            b.x = (a*x0 + (d-a)*x1)*scale/d + offset
            b.y = (a*y0 + (d-a)*y1)*scale/d + offset
            b.scale = 1.0/16.0
            self.add(b)
            sprites.append(b)
            a += fstep
        return sprites
        
def test_testbed_layer():
    class TestLayer(TestBedLayer):
        is_event_handler = True
        def __init__(self):
            super( TestBedLayer, self ).__init__()
            self.add_circle(center,radius)
            self.add_wpts(wps)
            self.add_line(wps[0],wps[1],color=(255,0,0))
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=800, height=600)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)
    
def test_testbed_layer2():
    class TestLayer(TestBedLayer):
        is_event_handler = True
        def __init__(self):
            super( TestBedLayer, self ).__init__()
            self.add_circle(center,radius)
            self.add_wpts(wps)
            p0 = wps[0]
            for p1 in wps:
                if p1!=p0:
                    self.add_line(p0,p1,color=(255,0,0))
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=800, height=600)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)

def test_visibles():
    class TestLayer(TestBedLayer):
        is_event_handler = True
        def __init__(self):
            super( TestBedLayer, self ).__init__()
            self.add_circle(center,radius)
            self.add_wpts(wps)
            fn_visibles = visiblesball_factory(V2(center[0],center[1]),radius)
            self.stage = 0
            self.objs = {}
            self.build_stage()
                
        def on_key_press(self,k,m):
            self.stage = (self.stage + 1 )%4
            self.build_stage()
            return True

        def build_stage(self):
            for k in self.objs:
                for e in self.objs[k]:
                    self.remove(e)
            self.objs = {} # vaild because the other objs where not registered
            fn_visibles = visiblesball_factory(V2(center[0],center[1]),radius)
            p0 = V2(wps[self.stage][0],wps[self.stage][1])
            for p1 in wps:
                if p1!=p0:
                    if fn_visibles(p0,p1):
                        s = self.add_line(p0,V2(p1[0],p1[1]),color=(0,255,0))
                    else:
                        s = self.add_line(p0,V2(p1[0],p1[1]),color=(255,0,0))
                    self.objs['L %d %s %s'%(self.stage,p1[0],p1[1])]=s
                
            

    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=800, height=600)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)


def test_graph_build():                     
    class TestLayer(TestBedLayer):
        is_event_handler = True
        def __init__(self):
            super( TestBedLayer, self ).__init__()
            self.vnodes = []
            self.add_circle(center,radius)
            self.add_wpts(list(wps))
            fn_visibles = visiblesball_factory(V2(center[0],center[1]),radius)
            self.wpnav = WaypointNav(wps,fn_visibles)
            self.objs = {}
            for r,s in zip(wps,self.wpnav.points):
                assert(geom.dist(r,s)<1.0e-4)
            print 'self.wpnav.adj[0]:',self.wpnav.adj[0]
            self.last_i = 0
            self.last_j = 0

##            #add all arcs
##            wpnav = self.wpnav
##            points = wpnav.points
##            objs = self.objs
##            for i in xrange(len(points)):
##                p0 = points[i]
##                #print '\n## i , adj_i:',i,wpnav.adj[i]
##                for j in wpnav.adj[i]:
##                    sprites = self.add_line(p0,points[j])
##                    objs['L%d %j'%(i,j)] = sprites

        def on_key_press(self,k,m):
            if k in [key.UP]:
                self.fill_slow()
                return True

        def fill_slow(self):
            wpnav = self.wpnav
            points = wpnav.points
            objs = self.objs
            if self.last_i>=len(wpnav.adj):
                return
            if self.last_j>=len(wpnav.adj[self.last_i]):
                self.last_i += 1
                self.last_j = 0
                print '\n*** begin new adj point:'
                return
            sprites = self.add_line(points[self.last_i],points[self.last_j])
            objs['L%d %j'%(i,j)] = sprites
            self.last_j += 1
    
            
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=800, height=600)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)


if __name__ == "__main__":
    #test_testbed_layer()
    #test_testbed_layer2()
    test_visibles()
    #test_graph_build() #fallando
