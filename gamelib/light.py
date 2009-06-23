import random
from math import sin


from cocos.batch import BatchNode
from cocos.sprite import Sprite

def cap(value, min_v, max_v):
    return max(min(value, max_v), min_v)

class LightGroup(BatchNode):
    def __init__(self):
        super(LightGroup, self).__init__()

    def add_lights(self,layer,cls):
        for c in layer.get_children():
            sp = cls(c.image)
            sp.label = c.label
            sp.position = c.position
            sp.scale = c.scale
            sp.source_scale = c.scale
            sp.rotation = c.rotation
            sp.opacity = c.opacity
            self.add( sp )
        
