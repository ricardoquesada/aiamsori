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
import avbin

import cocos
from cocos.actions import Delay, CallFunc
from cocos.director import director
from cocos.batch import BatchNode
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import NotifierSprite, Sprite

from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
from tiless_editor.layers.collision import CollisionLayer, Ray
from tiless_editor.tiless_editor import LayersNode
from tiless_editor.tilesslayer import TilessLayer
from walls import create_wall_layer
import sound
import light
from gamecast import Agent, Father, Zombie, get_animation
from gamectrl import MouseGameCtrl, KeyGameCtrl

WIDTH, HEIGHT = 1024, 768
MAPFILE = 'data/map.json'
RETREAT_DELAY = 0.1

def main():
    # fix pyglet resource path
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()

    #Load avbin
    avbin.init_avbin()

    try:
        import cocos.gl_framebuffer_object as FG
        FG.FramebufferObject().check_status()
    except Exception:
        print 'ERROR: You should install your video card drivers.'
        print 'If you already have, your video card doesn\'t support this game\'s effects.'
        return

    # initialize cocos director
    #director.init(fullscreen=True)
    director.init(WIDTH, HEIGHT, resizable=True)
    sound.init()
    # create game scene
    game_layer = GameLayer(MAPFILE)
    game_layer.position = (400, 300)

    director.set_3d_projection()
#    director.set_2d_projection()

    main_scene = Scene()
    main_scene.add(game_layer)
    main_scene.add(KeyGameCtrl(game_layer))
    main_scene.add(MouseGameCtrl(game_layer))

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
        zombie_spawn = None

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
        agent = Father(get_animation('father_idle'), (0,0), self)        
        self.player = agent
        self.add(agent)
        collision_layer.add(agent, shape_name='circle', static=False, layers=1)

        if zombie_spawn:
            x, y = director.get_window_size()
            for c in zombie_spawn.get_children():
                z = Zombie(get_animation('zombie_idle'), self.player)
                z.x = c.x
                z.y = c.y
                z.position = z.x, z.y
                self.map_node.add(z)
                collision_layer.add(z, shape_name='circle', static=False,
                                    scale=.75, layers=1)

    def is_collide(self, origin, target):
        collision_layer = self.map_node.get('collision')
        radius = 0.5 * max(self.player.width, self.player.height) * self.player.scale
        ray = Ray(radius, origin, target)
        ray.layers = 6
        #print 'created ray between points.. origin: %s, target: %s' % (origin, target)
        #print 'ray.pos:  %s' % str(ray.position)
        #print 'ray.radius:  %s' % ray.radius
        #print 'ray.a:  %s' % str(ray.a)
        #print 'ray.b:  %s' % str(ray.b)
        #print 'ray.length:  %s' % ray.length
        collision_layer.space.add(ray)
        collision_layer.step()
        collision_layer.space.remove(ray)
        return ray.data['collided']

    def on_collision(self, shape_a, shape_b):
        #        collision_layer = self.map_node.get('collision')
        #        node = collision_layer._get_node(shape_a)
        #        other = collision_layer._get_node(shape_b)
        #        other.shape = shape_b
        #        if isinstance(node, (Agent, Zombie)):
        #            # reset agent position and set speed to zero
        #            node._on_collision(other)
        #
        #        node = collision_layer._get_node(shape_b)
        #        other = collision_layer._get_node(shape_a)
        #        other.shape = shape_a
        #        if isinstance(node, (Agent, Zombie)):
        #            # reset agent position and set speed to zero
        #            node._on_collision(other)
        collision_layer = self.map_node.get('collision')
        non_visual_shapes = (Ray,)
        agent_shapes = (Agent, Zombie)
        if isinstance(shape_a, non_visual_shapes):
            try:
                node = collision_layer._get_node(shape_b)
                if isinstance(node, agent_shapes):
                    node._on_collision()
            except AttributeError:
                # trying to collide two non-visual shapes... this should not happen
                print 'Colliding two non-visual shapes... this should not be happening.'
                print '-- shape_a: %s, shape_b: %s' % (shape_a, shape_b)
                pass
        elif isinstance(shape_b, non_visual_shapes):
            try:
                node = collision_layer._get_node(shape_a)
                if isinstance(node, agent_shapes):
                    node._on_collision()
            except AttributeError:
                # trying to collide two non-visual shapes... this should not happen
                print 'Colliding two non-visual shapes... this should not be happening.'
                print '-- shape_a: %s, shape_b: %s' % (shape_a, shape_b)
                pass
        else:
            node = collision_layer._get_node(shape_a)
            other = collision_layer._get_node(shape_b)
            other.shape = shape_b
            if isinstance(node, agent_shapes):
                # reset agent position and set speed to zero
                node._on_collision(other)

            node = collision_layer._get_node(shape_b)
            other = collision_layer._get_node(shape_a)
            other.shape = shape_a
            if isinstance(node, agent_shapes):
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
                collision_layer.add(collision_child, shape_name='square', static=True, layers=5)
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


if __name__ == '__main__':
    main()
