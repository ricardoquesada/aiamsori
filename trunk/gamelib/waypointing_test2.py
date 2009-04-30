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
        super( cocos.layer.Layer, self ).__init__()
        self.named_grps = {} # contains list of sprites (or iterable)
        
    def add_wpts(self,wpts):
        sprites = []
        for x,y in wps:
            b = Sprite('data/npoint.png')#,color=(140,140,140))
            b.x = x*scale+offset
            b.y = y*scale+offset
            b.scale = 1.0/8.0
            self.add(b)
            self.add_named('P%s %s'%(x,y),[b])
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

    def add_named_node(self,name,p0,color=(255,255,255)):
        x,y = p0
        b = Sprite('data/npoint.png',color=color)
        b.x = x*scale+offset
        b.y = y*scale+offset
        b.scale = 1.0/8.0
        self.add(b)
        self.add_named('P%s %s',[b])
        
    def remove_named(self,name):
        li = self.named_grps[name]
        for e in li:
            self.remove(e)
        del self.named_grps[name]

    def add_named(self,name,iterable): # the iterable deliver sprites
        self.named_grps[name] = iterable
        
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
            self.build_stage()
                
        def on_key_press(self,k,m):
            self.stage = (self.stage + 1 )%len(wps)
            self.build_stage()
            return True

        def build_stage(self):
            for e in self.named_grps:
                self.remove_named(e)
            fn_visibles = visiblesball_factory(V2(center[0],center[1]),radius)
            p0 = V2(wps[self.stage][0],wps[self.stage][1])
            for p1 in wps:
                if p1!=p0:
                    if fn_visibles(p0,p1):
                        s = self.add_line(p0,V2(p1[0],p1[1]),color=(0,255,0))
                        self.add_named('LG%d %d'%(i,j),s)
                    else:
                        s = self.add_line(p0,V2(p1[0],p1[1]),color=(255,0,0))
                        self.add_named('LR%d %d'%(i,j),s)

                
            

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
            for r,s in zip(wps,self.wpnav.points):
                assert(geom.dist(r,s)<1.0e-4)
            print 'self.wpnav.adj[0]:',self.wpnav.adj[0]
            self.last_i = 0
            self.last_j = 0

            #add all arcs
            wpnav = WaypointNav(wps,fn_visibles)
            points = wpnav.points
            for i,adj_i in enumerate(wpnav.adj):
                for j in adj_i:
                    sprites = self.add_line(points[i],points[j])
                    self.add_named('L%d %d'%(i,j),sprites)
            
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=800, height=600)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)

def test_inpection_short_paths():
    print 'WS move start(red point), arrows move dest(blue point)'
    class TestLayer(TestBedLayer):
        is_event_handler = True
        def __init__(self):
            super( TestLayer, self ).__init__()
            self.add_circle(center,radius)
            self.add_wpts(list(wps))
            fn_visibles = visiblesball_factory(V2(center[0],center[1]),radius)
            self.wpnav = WaypointNav(wps,fn_visibles)
            for r,s in zip(wps,self.wpnav.points):
                assert(geom.dist(r,s)<1.0e-4)
            print 'self.wpnav.adj[0]:',self.wpnav.adj[0]
            self.last_i = 0
            self.last_j = 0

            #add all arcs
            wpnav = WaypointNav(wps,fn_visibles)
            points = wpnav.points
            for i,adj_i in enumerate(wpnav.adj):
                for j in adj_i:
                    sprites = self.add_line(points[i],points[j])
                    self.add_named('L%d %d'%(i,j),sprites)

            self.old_start_i = -1
            self.old_dest_i = -1
            self.start_i = 0
            self.dest_i = 1
            self.colored_paths = set()
            self.update_best_path()

        def update_best_path(self):
            #build new best path, adding along the colored segments
            print '** update best path' 
            new_colored = set()
            a = self.start_i
            dest = self.dest_i
            points = self.wpnav.points
            while 1:
                b = self.wpnav._next_waypoint(a,dest)
                new_colored.add((a,b))
                a = b
                if a==self.dest_i:
                    break
            new_colored = new_colored - self.colored_paths
            toGrey = self.colored_paths - new_colored
            for a,b in new_colored:
                self.remove_named('L%s %s'%(a,b))
                sprites = self.add_line(points[a], points[b], color=(255,0,0))
                self.add_named('LC%s %s'%(a,b),sprites)

            for a,b in toGrey:
                self.remove_named('LC%s %s'%(a,b))
                sprites = self.add_line(points[a], points[b], color=(255,0,0))
                self.add_named('L%s %s'%(a,b),sprites)

            self.colored_paths = (self.colored_paths - toGrey).update(new_colored)

            #update endpoints
            if self.start_i!=self.old_start_i:
                if self.old_start_i>=0:
                    self.remove_named('PS%d %d'%tuple(points[self.old_start_i]))
                    self.add_named_node('P%d %d'%tuple(points[self.old_start_i]),
                                        points[self.old_start_i])
                self.remove_named('P%d %d'%tuple(points[self.start_i]))
                self.old_start_i = self.start_i
                self.add_named_node('PS%d %d'%tuple(points[self.start_i]),
                                    points[self.start_i],color=(255,0,0))
                
            if self.dest_i!=self.old_dest_i:
                if self.old_dest_i>=0:
                    self.remove_named('PD%d %d'%tuple(points[self.old_dest_i]))
                    self.add_named_node('P%d %d'%tuple(points[self.old_dest_i]),
                                        points[self.old_dest_i])
                self.remove_named('P%d %d'%tuple(points[self.dest_i]))
                self.add_named_node('PD%d %d'%tuple(points[self.dest_i]),
                                    points[self.dest_i],color=(0,0,255))
                self.old_dest_i = self.dest_i

        def on_key_release(self, k, m):
            print '<< on key release'
            want = -1
            if k==key.W:
                want = (self.start_i + 1)%len(self.wpnav.points)
            elif k==key.S:
                want = (self.start_i - 1)%len(self.wpnav.points)
            if want>=0 and want!=self.dest_i:
                self.start_i = want
                self.update_best_path()
                return True
                
            if k==key.UP:
                want = (self.dest_i + 1)%len(self.wpnav.points)
            elif k==key.DOWN:
                want = (self.dest_i - 1)%len(self.wpnav.points)
            if want>=0 and want!=self.start_i:
                self.dest_i = want
                self.update_best_path()
                return True

    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=800, height=600)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)
    


def test_arcs_walkables():
    fn_visibles = visiblesball_factory(V2(center[0],center[1]),radius)
    wpnav = WaypointNav(wps,fn_visibles)
    points = wpnav.points

    # test arcs are walkables, ie the endpoints have direct line of sight
    for i,adj_i in enumerate(wpnav.adj):
        for j in adj_i:
            assert(fn_visibles(points[i],points[j]))
    print 'test arcs navigables ok'
            
                   
        
    

if __name__ == "__main__":
    #test_testbed_layer()
    #test_testbed_layer2()
    #test_visibles()
    #test_graph_build()
    test_inpection_short_paths()
    #test_arcs_walkables()
