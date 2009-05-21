import random
from math import cos, sin, radians, degrees

import cocos
from cocos.director import director
from cocos.sprite import Sprite
from cocos.euclid import Vector2
import pyglet


import geom

def merge(headings):
    # merge tuples of (heading, weight)
    tx = ty = 0
    for h, w in headings:
        tx += cos(radians(h))*w
        ty += sin(radians(h))*w
    angle = geom.vector_angle(tx, ty)
    return degrees(angle)

def cap(value, min_v, max_v):
    return max(min(value, max_v), min_v)

def seek(px, py, gx, gy):
    # returns a heading towars a goal
    gx = gx - px
    gy = py - gy
    angle = geom.vector_angle(gx, gy)
    return degrees(angle)

def avoid_group(px, py, group):
    # returns a heading that avoids a group of objects and a distance to
    # the closes object
    res = []
    fx = fy = 0.0
    mind = -1
    for l in group:
        hx = px - l.x
        hy = l.y - py
        v = Vector2(hx, hy).normalize()
        d = geom.dist((0,0), (hx, hy))
        if d < mind or mind < 0:
            mind = d
        res.append((v.x, v.y, d))

    if mind < 0:
        return 0, 10000000

    for hx, hy, d in res:
        p = float(mind)/d
        #print "ENEMY:", d, degrees(geom.vector_angle(hx, hy))
        fx += hx*p
        fy += hy*p
    #print "ESCAPE DIR", degrees(geom.vector_angle(fx, fy)), mind
    return degrees(geom.vector_angle(fx, fy)), mind

class TestLayer(cocos.layer.Layer):
    is_event_handler = True

    def __init__(self):
        super( TestLayer, self ).__init__()

        x,y = director.get_window_size()
        self.boids = []
        for i in range(20):
            b = Sprite('boid.png')
            b.x = random.randint(0, x)
            b.y = random.randint(0, y)
            b.rotation = 0 #random.randint(0, 360)
            b.speed = 26#200 #random.randint(0, 400)
            self.boids.append(b)
            self.add(b)
        self.mouse = cocos.cocosnode.CocosNode()
        self.schedule(self.update)

    def on_mouse_motion(self, px, py, dx, dy):
        self.mouse.x = px
        self.mouse.y = py


    def update(self, dt):
        x,y = director.get_window_size()


        n = 0
        for b in self.boids:
            locals = self.get_near(b, 200)
            goal = seek(b.x, b.y, self.mouse.x, self.mouse.y)
            #print "GOAL", goal
            escape, danger = avoid_group(b.x, b.y, locals)
            #print "danger", danger, escape
            if danger < 50:
                #print "escape"
                chosen = escape
            elif danger > 100:
                #print "goal"
                chosen = goal
            else:
                d = (danger-50)/50
                chosen = merge([(goal, d), (escape, 1-d)])

            delta = geom.angle_rotation(radians(b.rotation), radians(chosen))
            delta = degrees(delta)
            max_r = 180
            delta = cap(delta, -max_r, max_r) * dt
            b.rotation += delta

            # update position
            a = -b.rotation
            b.x = (b.x + cos( radians(a) ) * b.speed * dt) % x
            b.y = (b.y + sin( radians(a) ) * b.speed * dt) % y
            b.rotation = b.rotation % 360


    def get_near(self, s, distance):
        found = []
        for b in self.boids:
            if b == s: continue
            if geom.dist(b.position, s.position) < distance:
                found.append(b)
        return found

if __name__ == "__main__":
    director.init(width=1024, height=768)
    test_layer = TestLayer ()
    main_scene = cocos.scene.Scene (test_layer)
    director.run (main_scene)
