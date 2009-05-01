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

from shapes import Bullet, Ray
from shapes import Wall, COLLISION_GROUP_AGENT, COLLISION_GROUP_ZOMBIE
from walls import create_wall_layer
import sound
import light
from gamecast import Agent, Father, Zombie, Boy, Girl, Mother, get_animation
from gamectrl import MouseGameCtrl, KeyGameCtrl

#WIDTH, HEIGHT = 1024, 768
MAPFILE = 'data/map.json'
RETREAT_DELAY = 0.1

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
    hud_layer = cocos.layer.Layer()
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

        # create collision shapes
        collision_layer = self._create_collision_layer(for_collision_layers)
        self.map_node.add_layer('collision', 1000, collision_layer)
        self.map_node.add(create_wall_layer(walls_layers), z=10)
        # add scene map node to the main layer
        self.add(self.map_node)

        # create agents (player and NPCs)
        self._create_agents(zombie_spawn)
        x, y = director.get_window_size()
        #self.light = light.Light(x/2, y/2)

        # if waypoint editing mode, create waypoints
        if options.wpt_on:
            from wptlayer import WptLayer
            self.wptlayer = WptLayer(mapfile)
            self.map_node.add_layer('wptedit',1,self.wptlayer) # ?

        # talk queue
        self.hud = hud
        self.talking = []
        self.talk_layer = cocos.layer.Layer()
        self.hud.add(self.talk_layer, z=10)
        self.talk("Dad", "hello hello hello"*5)
        self.talk("Dad", "hello hello hello"*5)
        self.talk("Bee", "Bye Bye"*5, False)

    def talk(self, who, message, transient=True):
        # transient messages get discarded if we are talking
        # non transient messages are queued.
        if transient and self.talking:
                return
        if self.talking:
            self.talking.append((who, message))
        else:
            self.talking.append((who, message))
            self.update_talk()

    def end_talking(self):
        self.talking = self.talking[1:]
        ch = list(self.talk_layer.get_children())
        for c in ch:
            self.talk_layer.remove(c)
        self.update_talk()

    def update_talk(self):
        if not self.talking:
            return
        who, text = self.talking[0]
        x, y = director.get_window_size()

        face = Sprite('faces/%s.png'%who)
        self.talk_layer.add(face)
        face.position = face.image.width*face.scale/2, y - face.image.height * face.scale/2

        balloon_l = Sprite('faces/balloon-left.png')
        balloon_r = Sprite('faces/balloon-right.png')
        balloon_c = Sprite('faces/balloon-center.png')

        self.talk_layer.add(balloon_l)
        self.talk_layer.add(balloon_c)
        self.talk_layer.add(balloon_r)

        x1 = face.image.width*face.scale
        y1 = y - face.image.height * face.scale
        x2 = x1+balloon_l.image.width
        y2 = y-3
        balloon_l._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]

        x1 = x-5-balloon_r.image.width
        y1 = y1
        x2 = x-5
        y2 = y-3
        balloon_r._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]

        x1 = face.image.width*face.scale+balloon_l.image.width
        y1 = y1
        x2 = x-5-balloon_r.image.width
        y2 = y-3
        balloon_c._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]



        label = cocos.text.Label(text,
            font_name='Times New Roman',
            font_size=32,
            x=x1, y=y-20,
            anchor_x='left', anchor_y='top', width=x-face.image.width*face.scale-40, multiline=True)
        label.element.color = 0,0,0,255
        self.talk_layer.add(label, z=1)
        self.do( Delay(5) + CallFunc(self.end_talking) )

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
        father = Father(get_animation('father_idle'), (-250,0), self)
        self.player = father
        self.add(father)
        collision_layer.add(father, static=father.shape.static)

        # any actor except father must be added into the if, else they
        # pester you when editing waypoints
        if not options.wpt_on:
            boy = Boy(get_animation('boy_idle'), (-150,100), self.player)
            self.add(boy)
            collision_layer.add(boy, static=boy.shape.static)

            girl = Girl(get_animation('girl_idle'), (-250,120), self.player)
            self.add(girl)
            collision_layer.add(girl, static=girl.shape.static)

            mother = Mother(get_animation('mother_idle'), (-350,-100), self.player)
            self.add(mother)
            collision_layer.add(mother, static=mother.shape.static)

            x, y = director.get_window_size()
            for c in zombie_spawn.get_children():
                z = Zombie(get_animation('zombie1_idle'), self.player)
                z.x = c.x
                z.y = c.y
                z.position = z.x, z.y
                self.map_node.add(z)
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
        #collision_layer.show_shapes = True

        for layer in layers:
            for z, child in layer.children:
                img = {'filename': child.path, 'position': child.position,
                       'rotation': child.rotation, 'scale': child.scale,
                       'opacity': child.opacity, 'rect': child.rect}
                wall = self._create_wall(img)
                collision_layer.add(wall, static=wall.shape.static)
        return collision_layer


    def _create_sprite(self, data, shape_cls=None):
        img = data['img']
        sprite = NotifierSprite(str(img['filename']),
                                img['position'], img['rotation'],
                                img['scale'], img['opacity'])
        sprite.label = img['label'] if "label" in img else None
        sprite.path = img['filename']
        sprite.rect = img['rect']

        args = (sprite,) + data.get('args', ())
        kwargs = dict(data.get('kwargs', {}))

        if shape_cls is not None:
            shape = shape_cls(*args, **kwargs)
        else:
            shape = None
        sprite.shape = shape
        return sprite


    def _create_wall(self, img):
        data = {'img': img}
        return self._create_sprite(data, Wall)

    def _create_bullet(self, origin, target):
        img = {'filename': 'img/bullet.png', 'position': origin,
               'rotation': 0, 'scale': 1.0,
               'opacity': 0, 'rect': [0, 0, 64, 64]}
        args = (origin, target)
        data = {'img': img, 'args': args}
        return self._create_sprite(data, Bullet)

    def update(self, dt):
        x, y = director.get_window_size()
        self.x = -self.player.x + x/2
        self.y = -self.player.y + y/2

        # clear out any non-collisioned bullets
        self._remove_bullets()

    def _remove_bullets(self):
        collision_layer = self.map_node.get('collision')
        for z, child in self.children:
            if isinstance(child, NotifierSprite) and isinstance(child.shape, Bullet):
                if not child.shape.data['collided']:
                    # only remove non collided shapes, as collided shapes will be removed by
                    # the collided object
                    #print 'removing BULLET'
                    collision_layer.remove(child, static=child.shape.static)
                    self.remove(child)
                else:
                    #print 'bullet collided. NOT REMOVING'
                    pass


if __name__ == '__main__':
    main()
