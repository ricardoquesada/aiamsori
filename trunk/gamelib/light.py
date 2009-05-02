import random
from math import sin


from cocos.batch import BatchNode
from cocos.sprite import Sprite

def cap(value, min_v, max_v):
    return max(min(value, max_v), min_v)

class Light(BatchNode):
    def __init__(self, layer):
        super(Light, self).__init__()
        for c in layer.get_children():
            sp = Sprite(c.image)
            sp.source_position = c.position
            sp.position = c.position
            sp.scale = c.scale
            sp.source_scale = c.scale
            sp.rotation = c.rotation
            sp.opacity = c.opacity
            sp.dx = 0
            sp.dy = 0
            sp.dt = random.random()*3.15
            self.add( sp )
#        self.schedule(self.update)

    def update(self, dt):
        for c in self.get_children():
            c.dt += dt
            c.scale = c.source_scale + 0.05*sin(c.dt)
