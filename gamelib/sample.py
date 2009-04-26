
import simplejson
from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt

from cocos.director import director
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import NotifierSprite
from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
from tiless_editor.layers.collision import CollisionLayer
from tiless_editor.tiless_editor import LayersNode

from gamectrl import GameCtrl

def create_collision_layer(layer):
    def on_collision(self, shape_a, shape_b):
        # this is a default implementation for the callback
        # it shows the shapes that collided in a visual way
        print 'PIZZA'
        #self._alert(shape_a)
        #self._alert(shape_b)

    collision_layer = CollisionLayer(on_collision)
    for z, child in layer.children:
        img = {'filename': child.path,
               'position': child.position, 'rotation': child.rotation, 'scale': child.scale, 'opacity': child.opacity,
               'label': child.label, 'rect': child.rect}
        new_child = build_sprite(img)
        collision_layer.add(new_child, shape_name='square')
    return collision_layer

def load_scene(filename):
    layers_node = LayersNode()
    layers = simplejson.load(open(filename))['layers']
    for layer_data in layers:
        layer_type = layer_data['layer_type']

        sprite_layer = SpriteLayerFactory().dict_to_layer(layer_data['data'])
        layers_node.add_layer(layer_data['label'], layer_data['z'], sprite_layer)
#        layers_node.add_layer('collision', layer_data['z'], create_collision_layer(sprite_layer))

    scene = Scene()
    scene.add(layers_node)
    return scene

def build_sprite(img):
    s = NotifierSprite(str(img['filename']),
               img['position'], img['rotation'], img['scale'], img['opacity'])
    s.label = img['label'] if "label" in img else None
    s.path = img['filename']
    s.rect =img['rect']
    return s

def create_agent(scene):
    layers = scene.children[0][1]
#    collision_layer = layers.get('collision')
    agent_layer = scene.add(Layer())
#    img = {'filename': 'data/img/tipito.png', 'position': (100, 100), 'rotation': 0, 'scale': 1.0, 'opacity': 255,
#           'label': 'Agent', 'rect': [0, 0, 64, 64]}
    agent_sprite = Char('data/img/tipito.png')
    agent_sprite.position = (100, 100)
    agent_sprite.speed = 0
    agent_layer.add(agent_sprite)
#    collision_layer.add(agent_sprite, shape_name='square')
    return agent_sprite

class Char(NotifierSprite):

    def __init__(self, img):
        super(Char, self).__init__(img)
        self.speed = 0
        self.schedule(self.update)

    def update(self, dt):
        a = -self.rotation
#        print self.speed, dt, cos(radians(a)) * self.speed * dt
        self.x += cos(radians(a)) * self.speed * dt
        self.y += sin(radians(a)) * self.speed * dt

    def look_at(self, px, py):
        pl_x, pl_y = self.position[0], self.position[1]
        self.rotation = -(atan2(py - pl_y, px - pl_x) / pi * 180)


def main():
    import sys
    import pyglet
    import os.path

    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()

    director.init(800, 600)
    main_scene = load_scene(sys.argv[1])
    agent = create_agent(main_scene)

    main_layer = main_scene.children[0][1]
    main_layer.player = agent

    main_layer.position = (400,300)

    main_scene.add(GameCtrl(main_layer))

    director.run(main_scene)

if __name__ == '__main__':
    main()
