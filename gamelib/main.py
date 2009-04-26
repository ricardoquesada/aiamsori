'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "gamelib"
package.
'''

import os.path
import pyglet
import simplejson
import sys
import random
import geom

from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt

import cocos
from cocos.director import director
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import NotifierSprite, Sprite

from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
from tiless_editor.layers.collision import CollisionLayer
from tiless_editor.tiless_editor import LayersNode
from walls import create_wall_layer

from gamectrl import GameCtrl
from boids import merge, seek, cap, avoid_group

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

    director.set_3d_projection()

    main_scene = Scene()
    main_scene.add(game_layer)
    main_scene.add(GameCtrl(game_layer))

    director.run(main_scene)

class GameLayer(Layer):
    def __init__(self, mapfile):
        super(GameLayer, self).__init__()
        self.map_node = LayersNode()

        factory = SpriteLayerFactory()
        # get layers from map
        for_collision_layers = []
        walls_layers = []
        layers = simplejson.load(open(mapfile))['layers']
        for layer_data in layers:
            layer_type = layer_data['layer_type']
            layer_label = layer_data['label']
            if layer_type == 'sprite':
                sprite_layer = factory.dict_to_layer(layer_data['data'])
                if layer_label in ["floor"]:
                    self.map_node.add_layer(layer_data['label'], layer_data['z'],
                                       sprite_layer)
                if layer_label in ['walls']:
                    for_collision_layers.append(sprite_layer)
                if layer_label in ['walls', 'gates']:
                    walls_layers.append(sprite_layer)

        # create collision shapes
        collision_layer = self._create_collision_layer(for_collision_layers)
        self.map_node.add_layer('collision', 1000, collision_layer)
        self.map_node.add(create_wall_layer(walls_layers), z=10)
        # add scene map node to the main layer
        self.add(self.map_node)

        # create agents (players)
        self._create_agents()


    def _create_agents(self):
        # get collision layer
        collision_layer = self.map_node.get('collision')

        # create agent sprite
        agent = Agent('data/img/tipito.png', (0,0), self)
        self.player = agent
        self.add(agent)
        collision_layer.add(agent, shape_name='circle', static=False)

        x, y = director.get_window_size()
        for i in range(10):
            z = Zombie('data/img/zombie.png', self.player)
            z.x = random.randint(0, x)
            z.y = random.randint(0, y)
            z.position = z.x, z.y
            self.add(z)
            collision_layer.add(z, shape_name='circle', static=False)

    def on_collision(self, shape_a, shape_b):
        collision_layer = self.map_node.get('collision')
        for shape in (shape_a, shape_b):
            node = collision_layer._get_node(shape)
            if isinstance(node, (Agent, Zombie)):
                # reset agent position and set speed to zero
                node.on_collision()

    def _create_collision_layer(self, layers):
        collision_layer = CollisionLayer(self.on_collision)

        for layer in layers:
            for z, child in layer.children:
                img = {'filename': child.path, 'position': child.position,
                       'rotation': child.rotation, 'scale': child.scale,
                       'opacity': child.opacity, 'rect': child.rect}
                collision_child = self._create_child(img)
                collision_layer.add(collision_child, shape_name='circle')
        return collision_layer

    def _create_child(self, img):
        sprite = NotifierSprite(str(img['filename']),
                                img['position'], img['rotation'],
                                img['scale'], img['opacity'])
        sprite.label = img['label'] if "label" in img else None
        sprite.path = img['filename']
        sprite.rect = img['rect']
        return sprite


    def update(self, dt):
        x = (self.x + cos( radians(-self.player.rotation) ) * self.player.speed * -dt)
        y = (self.y + sin( radians(-self.player.rotation) ) * self.player.speed * -dt)
        self.position = (x, y)


class Agent(NotifierSprite):
    def __init__(self, img, position, game_layer):
        super(Agent, self).__init__(img, position)
        self._old_state = {'position': position}
        self.speed = 0
        self.position = position
        self.schedule(self.update)
        self.game_layer = game_layer
        self.acceleration = 0

    def on_collision(self):
        self.position = self._old_state['position']
        self.speed = 0

    def update(self, dt):
        # save old state
        self._old_state = {'position': self.position}

        # update speed
        if self.acceleration != 0 and abs(self.speed) < 100:
            self.speed += self.acceleration

        # update the position, based on the speed
        self.x = (self.x + cos( radians(-self.rotation) ) * self.speed * dt)
        self.y = (self.y + sin( radians(-self.rotation) ) * self.speed * dt)
        # FIXME: for some reason the x/y attributes don't update the position attribute correctly
        self.position = (self.x, self.y)

        # update layer position (center camera)
        self.game_layer.update(dt)

        # test for collisions
        collision_layer = self.parent
        collision_layer.step()

    def look_at(self, px, py):
        # translate mouse position to world
        px = px - self.game_layer.x
        py = py - self.game_layer.y
        self.target = (px, py)
        pl_x, pl_y = self.position[0], self.position[1]
        self.rotation = -(atan2(py - pl_y, px - pl_x) / pi * 180)


class Zombie(NotifierSprite):
    def __init__(self, img, player):
        super(Zombie, self).__init__(img)
        self._old_state = {}
        self.speed = 100
        self.schedule(self.update)
        self.player = player

    def on_collision(self):
        if self._old_state.has_key('position'):
            self.position = self._old_state['position']
        if self._old_state.has_key('rotation'):
            self.rotation = self._old_state['rotation']

    def update(self, dt):
        # save old position
        self._old_state = {'position': self.position, 'rotation': self.rotation}

        locals = []
        b = self
        goal = seek(b.x, b.y, self.player.x, self.player.y)
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
        max_r = 270
        delta = cap(delta, -max_r, max_r) * dt
        b.rotation += delta

        # update position
        a = -b.rotation
        b.x = (b.x + cos( radians(a) ) * b.speed * dt)
        b.y = (b.y + sin( radians(a) ) * b.speed * dt)
        # FIXME: for some reason the x/y attributes don't update the position attribute correctly
        b.position = (b.x, b.y)
        b.rotation = b.rotation % 360

        # test for collisions
        collision_layer = self.parent
        collision_layer.step()



if __name__ == '__main__':
    main()
