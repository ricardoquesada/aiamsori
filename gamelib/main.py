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
import avbin

from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt

import cocos
from cocos.actions import Delay, CallFunc
from cocos.director import director
from cocos.batch import BatchNode
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import NotifierSprite, Sprite

from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
from tiless_editor.layers.collision import CollisionLayer
from tiless_editor.tiless_editor import LayersNode
from tiless_editor.tilesslayer import TilessLayer
from walls import create_wall_layer
import sound
import light
from gamectrl import MouseGameCtrl, KeyGameCtrl
from boids import merge, seek, cap, avoid_group

WIDTH, HEIGHT = 1024, 768
MAPFILE = 'data/map.json'
RETREAT_DELAY = 0.1

def main():
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()

    #Load avbin
    avbin.init_avbin()

    # initialize cocos director
#    director.init(WIDTH, HEIGHT, fullscreen=True)
    director.init(fullscreen=True)
    #director.init(resizable=True)
    sound.init()
    # create game scene
    game_layer = GameLayer(MAPFILE)
    game_layer.position = (400, 300)

    director.set_3d_projection()
#    director.set_2d_projection()

    main_scene = Scene()
    main_scene.add(game_layer)
    if False:
        main_scene.add(MouseGameCtrl(game_layer))
    else:
        main_scene.add(KeyGameCtrl(game_layer))

    director.run(main_scene)

class LightLayer(cocos.cocosnode.CocosNode):
    def __init__(self, main):
        super(LightLayer, self).__init__()
        self.main = main
        self.sprite = Sprite('light.png')

    def draw(self):
        pyglet.gl.glPushMatrix()
        self.transform()


        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_ZERO, pyglet.gl.GL_SRC_ALPHA)
        #pyglet.gl.glBlendEquation(pyglet.gl.GL_FUNC_ADD)

        self.sprite.image.blit(self.main.player.x, self.main.player.y)
        pyglet.gl.glPopMatrix()

        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        #pyglet.gl.glBlendEquation(pyglet.gl.GL_FUNC_ADD)

def make_sprites_layer(layer_data, atlas):
    def build_sprite(img):
        rect = img['rect']
#        s = NotifierSprite(str(img['filename']),
#                   img['position'], img['rotation'], img['scale'], img['opacity'])

        region = pyglet.image.TextureRegion( rect[0], rect[1], 0, rect[2], rect[3], atlas.texture )
        s = NotifierSprite(region,
                   img['position'], img['rotation'], img['scale'], img['opacity'])
        s.label = img['label'] if "label" in img else None
        s.path = img['filename']
        s.rect =img['rect']
        return s

    layer = BatchNode()
    for item in layer_data["sprites"]:
        sprite = build_sprite(item)
        layer.add(sprite)
    return layer

class GameLayer(Layer):
    is_event_handler = True

    def __init__(self, mapfile):
        super(GameLayer, self).__init__()
        self.map_node = LayersNode()

        # get layers from map
        for_collision_layers = []
        walls_layers = []
        zombie_spawm = None

        img = pyglet.image.load(  'data/atlas.png' )
        self.atlas = pyglet.image.atlas.TextureAtlas( img.width, img.height )
        self.atlas.texture = img.texture
        pyglet.gl.glTexParameteri( img.texture.target, pyglet.gl.GL_TEXTURE_WRAP_S, pyglet.gl.GL_CLAMP_TO_EDGE )
        pyglet.gl.glTexParameteri( img.texture.target, pyglet.gl.GL_TEXTURE_WRAP_T, pyglet.gl.GL_CLAMP_TO_EDGE )


        layers = simplejson.load(open(mapfile))['layers']
        for layer_data in layers:
            layer_type = layer_data['layer_type']
            layer_label = layer_data['label']
            if layer_type == 'sprite':
                sprite_layer = make_sprites_layer(layer_data['data'], self.atlas)
                if layer_label in ["piso"]:
                    self.map_node.add_layer(layer_data['label'], layer_data['z'],
                                       sprite_layer)
                if layer_label in ['walls']:
                    for_collision_layers.append(sprite_layer)
                if layer_label in ['walls', 'gates']:
                    walls_layers.append(sprite_layer)
                if layer_label in ['zombie_spawn']:
                    zombie_spawn = sprite_layer

        # create collision shapes
        collision_layer = self._create_collision_layer(for_collision_layers)
        self.map_node.add_layer('collision', 1000, collision_layer)
        self.map_node.add(create_wall_layer(walls_layers), z=10)
        # add scene map node to the main layer
        self.add(self.map_node)

        # create agents (players)
        self._create_agents(zombie_spawn)
        x, y = director.get_window_size()
        self.light = light.Light(x/2, y/2)

    def on_enter(self):
        super(GameLayer, self).on_enter()
        x, y = director.get_window_size()
        self.light.set_position(x/2, y/2)
        self.light.enable()

    def on_exit(self):
        super(GameLayer, self).on_exit()
        self.light.disable()

    def on_resize(self, w, h):
        x, y = director.get_window_size()
        self.light.set_position(w/2, h/2)



    def _create_agents(self, zombie_spawn):
        # get collision layer
        collision_layer = self.map_node.get('collision')

        # create agent sprite
        agent = UserAgent('data/img/tipito.png', (0,0), self)
        self.player = agent
        self.add(agent)
        collision_layer.add(agent, shape_name='circle', static=False)

        if zombie_spawn:
            x, y = director.get_window_size()
            for c in zombie_spawn.get_children():
                z = Zombie('data/img/zombie.png', self.player)
                z.x = c.x
                z.y = c.y
                z.position = z.x, z.y
                self.map_node.add(z)
                collision_layer.add(z, shape_name='circle', static=False,
                                    scale=.75)

    def on_collision(self, shape_a, shape_b):
        collision_layer = self.map_node.get('collision')
        node = collision_layer._get_node(shape_a)
        other = collision_layer._get_node(shape_b)
        other.shape = shape_b
        if isinstance(node, (Agent, Zombie)):
            # reset agent position and set speed to zero
            node._on_collision(other)

        node = collision_layer._get_node(shape_b)
        other = collision_layer._get_node(shape_a)
        other.shape = shape_a
        if isinstance(node, (Agent, Zombie)):
            # reset agent position and set speed to zero
            node._on_collision(other)


    def _create_collision_layer(self, layers):
        collision_layer = CollisionLayer(self.on_collision)

        for layer in layers:
            for z, child in layer.children:
                img = {'filename': child.path, 'position': child.position,
                       'rotation': child.rotation, 'scale': child.scale,
                       'opacity': child.opacity, 'rect': child.rect}
                collision_child = self._create_child(img)
                collision_layer.add(collision_child, shape_name='square', static=True)
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
        x, y = director.get_window_size()
        self.x = -self.player.x + x/2
        self.y = -self.player.y + y/2

class Agent(NotifierSprite):
    def update_position(self, position):
        # test for collisions
        old_position = self.position
        self.updating = True
        collision_layer = self.parent

        self.position = position
        self.collision = None
        collision_layer.step()
        if self.collision:
            self.on_collision(self.collision)
            f = getattr(self.collision, "on_collision", None)
            if f is not None:
                f(self)

            self.position = position[0], old_position[1]
            self.collision = None
            collision_layer.step()
            if self.collision:
                self.position = old_position[0], position[1]
                self.collision = None
                collision_layer.step()
                if self.collision:
                    self.position = old_position

    def _on_collision(self, other):
        # used internally for collision testing
        if not self.updating:
            return
        self.collision = other

    def on_collision(self, other):
        # called when we want to report a collision
        pass


class UserAgent(Agent):
    def __init__(self, img, position, game_layer):
        super(UserAgent, self).__init__(img, position)
        self._old_state = {'position': position}
        self.speed = 0
        self.position = position
        self.schedule(self.update)
        self.game_layer = game_layer
        self.acceleration = 0
        self.updating = False
        self.rotation_speed = 0
        self.collision = False

    def on_collision(self, other):
        if isinstance(self.collision, Agent):
            sound.play("player_punch")

    def update(self, dt):
        # update speed
        if self.acceleration != 0 and abs(self.speed) < 130:
            self.speed += self.acceleration*100*dt


        self.rotation += 110 * self.rotation_speed * dt
        # update the position, based on the speed
        nx = (self.x + cos( radians(-self.rotation) ) * self.speed * dt)
        ny = (self.y + sin( radians(-self.rotation) ) * self.speed * dt)
        # FIXME: for some reason the x/y attributes don't update the position attribute correctly
        new_position = (nx, ny)

        self.update_position(new_position)

        # update layer position (center camera)
        self.game_layer.update(dt)

    def look_at(self, px, py):
        # translate mouse position to world
        px = px - self.game_layer.x
        py = py - self.game_layer.y
        self.target = (px, py)
        pl_x, pl_y = self.position[0], self.position[1]
        self.rotation = -(atan2(py - pl_y, px - pl_x) / pi * 180)


class Zombie(Agent):
    def __init__(self, img, player):
        super(Zombie, self).__init__(img)
        self._old_state = {}
        self.speed = 100
        self.schedule(self.update)
        self.player = player
        self.updating = False

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

        # FIXME: for some reason the x/y attributes don't update the position attribute correctly
        b.position = (b.x, b.y)
        b.rotation = b.rotation % 360
        # update position
        a = -b.rotation
        nx = (b.x + cos( radians(a) ) * b.speed * dt)
        ny = (b.y + sin( radians(a) ) * b.speed * dt)

        self.update_position((nx, ny))



if __name__ == '__main__':
    main()
