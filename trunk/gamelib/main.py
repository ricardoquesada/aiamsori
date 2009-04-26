'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "gamelib"
package.
'''

import os.path
import pyglet
import simplejson
import sys

from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt

from cocos.director import director
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import NotifierSprite

from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
from tiless_editor.layers.collision import CollisionLayer
from tiless_editor.tiless_editor import LayersNode

from gamectrl import GameCtrl

WIDTH, HEIGHT = 800, 600
MAPFILE = 'data/map.json'

def main():
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()

    # initialize cocos director
    director.init(WIDTH, HEIGHT)

    # create game scene
    game_layer = GameLayer(MAPFILE)
    game_layer.position = (400, 300)

    main_scene = Scene()
    main_scene.add(game_layer)
    main_scene.add(GameCtrl(game_layer))

    director.run(main_scene)


class GameLayer(Layer):
    def __init__(self, mapfile):
        super(GameLayer, self).__init__()
        map_node = LayersNode()

        factory = SpriteLayerFactory()
        # get layers from map
        sprite_layers = []
        layers = simplejson.load(open(mapfile))['layers']
        for layer_data in layers:
            layer_type = layer_data['layer_type']
            if layer_type == 'sprite':
                sprite_layer = factory.dict_to_layer(layer_data['data'])
                map_node.add_layer(layer_data['label'], layer_data['z'],
                                   sprite_layer)
                sprite_layers.append(sprite_layer)

        # create collision shapes
        collision_layer = self._create_collision_layer(sprite_layers)
        map_node.add_layer('collision', -1, collision_layer)

        # create agents (players)
        self._create_agent(map_node)

        self.add(map_node)

    def _create_agent(self, map_node):
        # get collision layer
        collision_layer = map_node.get('collision')

        # create agent sprite
        agent = Agent('data/img/tipito.png', (100, 100))
        self.player = agent
        self.add(agent)
        collision_layer.add(agent, shape_name='square', static=False)

    def on_collision(self, shape_a, shape_b):
        collision_layer = self.children[1][1].get('collision')
        for shape in (shape_a, shape_b):
            node = collision_layer._get_node(shape)
            if isinstance(node, Agent):
                # reset agent position and set speed to zero
                node.reset()

    def _create_collision_layer(self, layers):
        collision_layer = CollisionLayer(self.on_collision)

        for layer in layers:
            for z, child in layer.children:
                img = {'filename': child.path, 'position': child.position,
                       'rotation': child.rotation, 'scale': child.scale,
                       'opacity': child.opacity, 'rect': child.rect}
                collision_child = self._create_child(img)
                collision_layer.add(collision_child, shape_name='square')
        return collision_layer

    def _create_child(self, img):
        sprite = NotifierSprite(str(img['filename']),
                                img['position'], img['rotation'], 
                                img['scale'], img['opacity'])
        sprite.label = img['label'] if "label" in img else None
        sprite.path = img['filename']
        sprite.rect = img['rect']
        return sprite


class Agent(NotifierSprite):
    def __init__(self, image, position=(0, 0), speed=0):
        super(Agent, self).__init__(image, position)
        self._old_position = position
        self.speed = speed
        self.schedule(self.update)

    def reset(self):
        self.position = self._old_position
        self.speed = 0

    def update(self, dt):
        # save old position
        self._old_position = self.position
        # update the position, based on the speed
        b = self
        a = -b.rotation
        x = (b.x + cos( radians(a) ) * b.speed * dt)
        y = (b.y + sin( radians(a) ) * b.speed * dt)
        self.position = (x, y)
        # test for collisions
        collision_layer = self.parent
        collision_layer.step()

    def look_at(self, px, py):
        pl_x, pl_y = self.position
        self.rotation = -(atan2(py - pl_y, px - pl_x) / pi * 180)


if __name__ == '__main__':
    main()
