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
import optparse
import avbin

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
from tiless_editor.atlas import SavedAtlas

from walls import create_wall_layer
import talk
import gamehud
import sound
import light
from gamecast import Agent, Father, Zombie, Boy, Girl, Mother, Wall, Bullet, Ray, get_animation
from gamectrl import MouseGameCtrl, KeyGameCtrl

#WIDTH, HEIGHT = 1024, 768
MAPFILE = 'data/map.json'
RETREAT_DELAY = 0.1

ZOMBIE_WAVE_COUNT = 5

options = None

def main():
    # make available options
    parser = optparse.OptionParser()
    parser = optparse.OptionParser()
    parser.add_option("-w", "--wpting",
                      action="store_true", dest="wpt_on", default=False,
                      help="waypointing mode on")
    parser.add_option("-x", "--width", type='int', dest="width", default='1024',
                      help="set window width", metavar="WIDTH")
    parser.add_option("-y", "--height", type="int", dest="height", default='768',
                      help="set window height", metavar="HEIGHT")
    # need no enemies while waypointing, and another on_key
    global options
    (options, args) = parser.parse_args()

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
    director.init(options.width, options.height, resizable=True)
    sound.init()
    # create game scene
    hud_layer = gamehud.HudLayer()
    game_layer = GameLayer(MAPFILE, hud_layer)
#    game_layer.position = (400, 300)

    director.set_3d_projection()
#    director.set_2d_projection()

    main_scene = Scene()
    main_scene.add(game_layer)
    main_scene.add(hud_layer, z = 1)
    if options.wpt_on:
        from gamectrl_wpt import MouseGameCtrl, KeyGameCtrl
    else:
        from gamectrl import MouseGameCtrl, KeyGameCtrl
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
    saved_atlas = SavedAtlas('data/atlas-fixed.png', 'data/atlas-coords.json')

    def build_sprite(img):
        rect = img['rect']
        region = saved_atlas[img['filename']]
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

    def __init__(self, mapfile, hud):
        super(GameLayer, self).__init__()
        self.map_node = LayersNode()
        self.bullets = []
        self.dead_items = set()

        # get layers from map
        for_collision_layers = []
        walls_layers = []
        zombie_spawn = None

        img = pyglet.image.load(  'data/atlas-fixed.png' )
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
                if layer_label in ["floor", "furninture"]:
                    self.map_node.add_layer(layer_data['label'], layer_data['z'],
                                       sprite_layer)
                if layer_label in ['walls', 'furninture']:
                    for_collision_layers.append(sprite_layer)
                if layer_label in ['walls', 'gates']:
                    walls_layers.append(sprite_layer)
                if layer_label in ['zombie_spawn']:
                    zombie_spawn = sprite_layer
                if layer_label in ['item_spawn']:
                    item_spawn = sprite_layer
                if layer_label in ['waypoints']:
                    waypoints = sprite_layer

        # create collision shapes
        collision_layer = self._create_collision_layer(for_collision_layers)
        self.map_node.add_layer('collision', 1000, collision_layer)
        self.map_node.add(create_wall_layer(walls_layers), z=10)
        # add scene map node to the main layer
        self.add(self.map_node)

        # create agents (player and NPCs)
        self._create_agents(zombie_spawn)
        self.setup_powerups(item_spawn)
        self.setup_waypoints(waypoints)

        x, y = director.get_window_size()
        #self.light = light.Light(x/2, y/2)

        # if waypoint editing mode, create waypoints
        if options.wpt_on:
            from wptlayer import WptLayer
            self.wptlayer = WptLayer(mapfile)
            self.map_node.add_layer('wptedit',1,self.wptlayer) # ?

        # talk queue
        self.hud = hud
        self.talk_layer = talk.TalkLayer()
        self.hud.add(self.talk_layer, z=10)
        self.talk("Dad", "hello hello hello"*5)
        self.talk("Dad", "hello hello hello"*5)
        self.talk("Bee", "Bye Bye"*5, transient=False, duration=2)

    def setup_waypoints(self, layer):
        for c in layer.get_children():
            print "waypoint", c.position
            
    def setup_powerups(self, layer):
        self.powerup_interval = 10
        self.item_spawn = []
        for c in layer.get_children():
            self.item_spawn.append( c.position )
        self.do( Delay(self.powerup_interval)+CallFunc(self.spawn_powerup))

    def spawn_powerup(self):
        position = random.choice(self.item_spawn)
        print "powerup position", position
        self.do( Delay(self.powerup_interval)+CallFunc(self.spawn_powerup))

    def talk(self, who, what, duration=5, transient=False):
        self.talk_layer.talk(who, what, duration=duration, transient=transient)

    def on_enter(self):
        super(GameLayer, self).on_enter()
        x, y = director.get_window_size()
        #self.light.set_position(x/2, y/2)
        #self.light.enable()

    def on_exit(self):
        super(GameLayer, self).on_exit()
        #self.light.disable()

    def on_resize(self, w, h):
        x, y = director.get_window_size()
        #self.light.set_position(w/2, h/2)

    def _create_agents(self, zombie_spawn):
        # get collision layer
        collision_layer = self.map_node.get('collision')

        # create agent sprite
        father = Father(get_animation('father_idle'), (0,-800), self)
        self.player = father
        self.add(father)
        collision_layer.add(father, static=father.shape.static)

        # any actor except father must be added into the if, else they
        # pester you when editing waypoints
        if not options.wpt_on:
            boy = Boy(get_animation('boy_idle'), (0,-800), self.player)
            self.add(boy)
            collision_layer.add(boy, static=boy.shape.static)

            girl = Girl(get_animation('girl_idle'), (0,-800), self.player)
            self.add(girl)
            collision_layer.add(girl, static=girl.shape.static)

            mother = Mother(get_animation('mother_idle'), (0,-800), self.player)
#            mother = Mother(get_animation('mother_idle'), (-350,-100), self.player)
            self.add(mother)
            collision_layer.add(mother, static=mother.shape.static)

            x, y = director.get_window_size()
            for i in range(ZOMBIE_WAVE_COUNT):
                for c in zombie_spawn.get_children():
                    z = Zombie(get_animation('zombie1_idle'), self.player)
                    z.x = c.x
                    z.y = c.y
                    z.position = z.x, z.y
                    #self.map_node.add(z)
                    self.add(z)
                    collision_layer.add(z, static=z.shape.static, scale=.75)

    def on_collision(self, shape_a, shape_b):
        node = shape_a.sprite
        other = shape_b.sprite
        if isinstance(node, Agent):
            node._on_collision(other)
        if isinstance(other, Agent):
            other._on_collision(node)


    def _create_collision_layer(self, layers):
        collision_layer = CollisionLayer(self.on_collision)
        # README: uncomment this to debug collision shapes
        #collision_layer.show_shapes = False

        for layer in layers:
            for z, child in layer.children:
                wall = Wall(child)
                collision_layer.add(wall, static=wall.shape.static)
        return collision_layer

    def update(self, dt):
        x, y = director.get_window_size()
        self.x = -self.player.x + x/2
        self.y = -self.player.y + y/2

        # clear out any non-collisioned bullets
        self._remove_bullets()

        # clear out any dead items
        self._remove_dead_items()

    def add_bullet(self, bullet):
        self.bullets.append(bullet)
        self.add(bullet)
        collision_layer = self.map_node.get('collision')
        collision_layer.add(bullet, static=bullet.shape.static)

    def remove_bullet(self, bullet):
        self.bullets.remove(bullet)
        # delay objects deletion until later, to avoid segfaults
        self.dead_items.add(bullet)

    def _remove_bullets(self):
        for bullet in self.bullets:
            self.remove_bullet(bullet)
        #print self.bullets

    def _remove_dead_items(self):
        collision_layer = self.map_node.get('collision')
        for item in self.dead_items:
            collision_layer.remove(item, static=item.shape.static)
            self.remove(item)
        self.dead_items.clear()

    def is_clear_path(self, origin, target):
        ray = Ray(self.player, target)
        collision_layer = self.map_node.get('collision')
        collision_layer.add(ray, static=ray.shape.static)
        collision_layer.step()
        collision_layer.remove(ray)
        return not ray.shape.data['collided']





if __name__ == '__main__':
    main()
