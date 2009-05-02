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

from pyglet import gl
import cocos
from cocos import framegrabber
from cocos.actions import Delay, CallFunc
from cocos.director import director
from cocos.batch import BatchNode
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import Sprite
from cocos.scenes.transitions import TransitionScene
from cocos.text import Label
from cocos.sprite import Sprite
from cocos.actions.instant_actions import Hide, Show
from cocos.actions.interval_actions import Delay

from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
#from tiless_editor.layers.collision import CollisionLayer
from tiless_editor.tiless_editor import LayersNode
from tiless_editor.tilesslayer import TilessLayer
from tiless_editor.atlas import SavedAtlas

from walls import create_wall_layer
import talk
import gamehud
import sound
from light import Light

from gamecast import Agent, Father, Zombie, Boy, Girl, Mother, Wall, Ray, PowerUp, get_animation
from gamectrl import MouseGameCtrl, KeyGameCtrl
from wallmask import WallMask

#WIDTH, HEIGHT = 1024, 768
MAPFILE = 'data/map.json'
RETREAT_DELAY = 0.1

ZOMBIE_WAVE_COUNT = 5
ZOMBIE_WAVE_DURATION = 60

RANDOM_DELTA = 70

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

#    avbin.init_avbin() #warn: if uncomented windows crash

    try:
        import cocos.gl_framebuffer_object as FG
        FG.FramebufferObject().check_status()
        has_grabber = True
    except Exception:
        print 'ERROR: You should install your video card drivers.'
        print 'If you already have, your video card doesn\'t support this game\'s effects.'
        print "press enter to play without effects"
        raw_input()
        has_grabber = False

    # initialize cocos director
    #director.init(fullscreen=True)
    director.init(options.width, options.height, resizable=True)
    sound.init()
    # create game scene
    hud_layer = gamehud.HudLayer()
    game_layer = GameLayer(MAPFILE, hud_layer, has_grabber)
#    game_layer.position = (400, 300)
    x,y = director.get_window_size()
    image_layer = ImageLayer(x,y)

    director.set_3d_projection()
#    director.set_2d_projection()

    main_scene = Scene()
    first_scene = Scene()
    first_scene.add(image_layer)
    image_layer.next = (director, main_scene)   #ugly?
    main_scene.add(game_layer)
    main_scene.add(hud_layer, z = 1)
    if options.wpt_on:
        from gamectrl_wpt import MouseGameCtrl, KeyGameCtrl
    else:
        from gamectrl import MouseGameCtrl, KeyGameCtrl
    main_scene.add(KeyGameCtrl(game_layer))
    main_scene.add(MouseGameCtrl(game_layer))

    director.run(main_scene)
    #director.run(first_scene)


def make_sprites_layer(layer_data, atlas):
    saved_atlas = SavedAtlas('data/atlas-fixed.png', 'data/atlas-coords.json')

    def build_sprite(img):
        rect = img['rect']
        region = saved_atlas[img['filename']]
        s = Sprite(region,
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

class ImageLayer(Layer):
    is_event_handler = True

    def __init__(self, x, y):
        super(ImageLayer, self).__init__()
        self.w = x
        self.h = y
        bg = Sprite('data/img/ppl.png')
        bg._vertex_list.vertices = [0,0,x,0,x,y,0,y]
        self.add(bg)

        label = Label('Press any key to start!', font_name='Times New Roman', font_size=52, bold=True)
        label.position = self.w / 2 - 340 , self.h / 2
        label.element.color = 40,179,75,180
        self.add(label, z=1)
        label.do(Hide() + Delay(10) + Show())

    def on_key_press(self, k, m):
        print "aprento una tecla"
        director, scene = self.next
        director.replace(scene)

class GameLayer(Layer):
    is_event_handler = True

    def __init__(self, mapfile, hud, has_grabber):
        super(GameLayer, self).__init__()
        self.has_grabber = has_grabber
        if has_grabber:
            width, height = director.get_window_size()

            self.texture = pyglet.image.Texture.create_for_size(
                    gl.GL_TEXTURE_2D, width,
                    height, gl.GL_RGBA)
            self.fire_lights = Layer()

        self.grabber = framegrabber.TextureGrabber()
        self.grabber.grab(self.texture)
        self.map_node = LayersNode()
        self.projectiles = []
        self.dead_items = set()
        self.wallmask = WallMask()
        self.agents_node = LayersNode()

        # get layers from map
        collision_layers = []
        walls_layers = []
        self.zombie_spawn = None
        self.z_spawn_lifetime = 0
        self.schedule(self.respawn_zombies)

        img = pyglet.image.load(  'data/atlas-fixed.png' )
        self.atlas = pyglet.image.atlas.TextureAtlas( img.width, img.height )
        self.atlas.texture = img.texture
        pyglet.gl.glTexParameteri( img.texture.target, pyglet.gl.GL_TEXTURE_WRAP_S, pyglet.gl.GL_CLAMP_TO_EDGE )
        pyglet.gl.glTexParameteri( img.texture.target, pyglet.gl.GL_TEXTURE_WRAP_T, pyglet.gl.GL_CLAMP_TO_EDGE )

        self.show_fire_frames = 0
        self.fire_light = Sprite("data/newtiles/luz_escopeta.png")
        self.fire_light.scale = 3
        self.fire_lights.add(self.fire_light)

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
                    collision_layers.append(sprite_layer)
                if layer_label in ['walls', 'gates']:
                    walls_layers.append(sprite_layer)
                if layer_label in ['zombie_spawn']:
                    self.zombie_spawn = sprite_layer
                if layer_label in ['item_spawn']:
                    item_spawn = sprite_layer
                if layer_label in ['waypoints']:
                    waypoints = sprite_layer
                if layer_label in ['lights']:
                    self.lights = Light(sprite_layer)


        # create collision shapes
        ###collision_layer = self._create_collision_layer(for_collision_layers)
        ###self.map_node.add_layer('collision', 1000, collision_layer)
        self.map_node.add(create_wall_layer(walls_layers), z=10)
        # add scene map node to the main layer
        self.add(self.map_node)

        self.add(self.agents_node, z=1)

        # create agents (player and NPCs)
        self._create_agents()
        self.setup_powerups(item_spawn)
        self.setup_waypoints(waypoints)

        x, y = director.get_window_size()
        #self.light = light.Light(x/2, y/2)

        # ends wallmask preparation, makes available service .is_empty(x,y)
        #self.wallmask.get_mask() #called for side effect _fill_gaps
        for layer in collision_layers:
            for child in layer.get_children():
                self.wallmask.add(child)
        # now is safe to call self.is_empty()

        # if waypoint editing mode, create waypoints
        if options.wpt_on:
            from wptlayer import WptLayer
            self.wptlayer = WptLayer(mapfile)
            self.map_node.add_layer('wptedit',1,self.wptlayer) # ?
        else:
            # LATER:
            # obtain wpts, instantiation need to wait until is safe to call
            # ray functions..
            wpts = [ (s.x,s.y) for s in waypoints.get_children()] #Esta bien asi Lucio?
            # a seguir

        # talk queue
        self.hud = hud
        self.talk_layer = talk.TalkLayer()
        self.hud.add(self.talk_layer, z=10)
        self.talk("Dad", "hello hello hello"*5)
        self.talk("Dad", "hello hello hello"*5)
        self.talk("Bee", "Bye Bye"*5, transient=False, duration=2)
        self.flicker()

    def flicker(self):
        delay = random.random()*5+2
        action = Delay(delay)
        light = random.choice(self.lights.get_children())

        turn_on = CallFunc(lambda: setattr(light, "opacity", 255))
        turn_off = CallFunc(lambda: setattr(light, "opacity", 0))
        for i in range(random.randint(5, 10)):
            micro_delay = random.random()*0.10
            micro_delay2 = random.random()*0.10
            action = action + Delay(micro_delay) + turn_off + Delay(micro_delay2) + turn_on
        action = action + CallFunc(self.flicker)
        self.do(action)


    def on_resize(self, w, h):
        if self.has_grabber:
            width, height = w, h
            print "RESETING TEXTURE", width, height


            self.texture = pyglet.image.Texture.create_for_size(
                    gl.GL_TEXTURE_2D, width,
                    height, gl.GL_RGBA)


    def visit(self):
        if not self.has_grabber:
            super(GameLayer, self).visit()
            return
        #do lights

        # before render

        # capture before drawing
        self.grabber.before_render(self.texture)

        # render scene
        super(GameLayer, self).visit()

        # psot render
        # capture after drawing
        self.grabber.after_render(self.texture)

        ambient = 0.1
        gl.glClearColor(ambient,ambient,ambient,ambient)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        # after render
        # blit lights
        pyglet.gl.glPushMatrix()
        self.transform()
        #pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        #gl.glBlendFunc( gl.GL_ONE, gl.GL_ONE );
        #gl.glBlendEquation(gl.GL_MAX);

        self.lights.visit()
        if self.show_fire_frames > 0:
            self.fire_lights.visit()
            self.show_fire_frames -= 1

        gl.glPopMatrix()

        gl.glBlendFunc( gl.GL_DST_COLOR, gl.GL_ONE_MINUS_SRC_ALPHA );
        gl.glBlendEquation(gl.GL_FUNC_ADD);

        #gl.glBlendFunc( gl.GL_DST_COLOR, gl.GL_ONE_MINUS_SRC_ALPHA );
        #gl.glBlendEquation(gl.GL_FUNC_ADD);

        # blit
        gl.glEnable(self.texture.target)
        gl.glBindTexture(self.texture.target, self.texture.id)

        gl.glPushAttrib(gl.GL_COLOR_BUFFER_BIT)

        self.texture.blit(0,0)

        gl.glPopAttrib()
        gl.glDisable(self.texture.target)


    def on_key_press( self, symbol, modifiers ):
        if symbol == pyglet.window.key.F and (modifiers & pyglet.window.key.MOD_ACCEL):
            return True

    def setup_waypoints(self, layer):
        for c in layer.get_children():
            print "waypoint", c.position

    def setup_powerups(self, layer):
        self.item_spawn = []
        for c in layer.get_children():
            self.item_spawn.append( c.position )
        self.spawn_powerup()

    def spawn_powerup(self):
        delay = random.randrange(1, 30)
        print 'DELAY', delay
        self.do(Delay(delay))
        position = random.choice(self.item_spawn)
        type = random.choice(['bullets', 'life'])
        powerup = PowerUp(type, position, self)
        self.agents_node.add(powerup)
        print "powerup ", powerup, 'at', position
        #print "powerup position", position
        #self.do( Delay(self.powerup_interval)+CallFunc(self.spawn_powerup))

    def respawn_zombies(self, dt):
        self.z_spawn_lifetime += dt
        if self.z_spawn_lifetime == 0 or self.z_spawn_lifetime >= ZOMBIE_WAVE_DURATION:
            ###collision_layer = self.map_node.get('collision')
            for i in range(ZOMBIE_WAVE_COUNT):
                for c in self.zombie_spawn.get_children():
                    z = Zombie(self, get_animation('zombie1_idle'), self.player)
                    z.x = c.x + random.choice([-1,1])*RANDOM_DELTA
                    z.y = c.y + random.choice([-1,1])*RANDOM_DELTA
                    z.position = z.x, z.y
                    #self.map_node.add(z)
                    self.agents_node.add(z)
                    ###collision_layer.add(z, static=z.shape.static, scale=.75)
            self.z_spawn_lifetime = 0


    def talk(self, who, what, duration=5, transient=False):
        self.talk_layer.talk(who, what, duration=duration, transient=transient)

    def on_enter(self):
        super(GameLayer, self).on_enter()
        x, y = director.get_window_size()

        sound.play('zombie_eat')

        self.do( Delay(3) + CallFunc(lambda: sound.play_music('game_music')) )


        #self.light.set_position(x/2, y/2)
        #self.light.enable()

    def on_exit(self):
        super(GameLayer, self).on_exit()
        #self.light.disable()



    def _create_agents(self):
        # get collision layer
        ###collision_layer = self.map_node.get('collision')

        # create agent sprite
        father = Father(self, get_animation('father_idle'), (0,-800))
        self.player = father
        self.agents_node.add(father)
        ###collision_layer.add(father, static=father.shape.static)

        # any actor except father must be added into the if, else they
        # pester you when editing waypoints
        if not options.wpt_on:
            position = 0 + random.choice([-1,1])*RANDOM_DELTA, -800 + random.choice([-1,1])*RANDOM_DELTA
            boy = Boy(self, get_animation('boy_idle'), position, self.player)
            self.agents_node.add(boy)
            ###collision_layer.add(boy, static=boy.shape.static)

            position = 0 + random.choice([-1,1])*RANDOM_DELTA, -800 + random.choice([-1,1])*RANDOM_DELTA
            girl = Girl(self, get_animation('girl_idle'), position, self.player)
            self.agents_node.add(girl)
            ###collision_layer.add(girl, static=girl.shape.static)

            position = 0 + random.choice([-1,1])*RANDOM_DELTA, -800 + random.choice([-1,1])*RANDOM_DELTA
            mother = Mother(self, get_animation('mother_idle'), position, self.player)
#            mother = Mother(get_animation('mother_idle'), (-350,-100), self.player)
            self.agents_node.add(mother)
            ###collision_layer.add(mother, static=mother.shape.static)

    ###def on_collision(self, shape_a, shape_b):
    ###    node = shape_a.sprite
    ###    other = shape_b.sprite
    ###    if isinstance(node, Agent):
    ###        node._on_collision(other)
    ###    if isinstance(other, Agent):
    ###        other._on_collision(node)


    ###def _create_collision_layer(self, layers):
    ###    return
    ###    collision_layer = CollisionLayer(self.on_collision)
    ###    # README: uncomment this to debug collision shapes
    ###    #collision_layer.show_shapes = False

    ###    for layer in layers:
    ###        for z, child in layer.children:
    ###            wall = Wall(child)
    ###            collision_layer.add(wall, static=wall.shape.static)
    ###    return collision_layer

    def update(self, dt):
        x, y = director.get_window_size()
        self.x = -self.player.x + x/2
        self.y = -self.player.y + y/2
        #self.lights.sprite.position = self.player.position

        # clear out any non-collisioned projectiles
#        self._remove_projectiles()

        # clear out any dead items
        self._remove_dead_items()
        if hasattr(self, "lights"):
            self.lights.update(dt)


    def add_projectile(self, projectile):
        self.projectiles.append(projectile)
        self.agents_node.add(projectile)

        self.fire_light.x = self.player.x
        self.fire_light.y = self.player.y
        self.fire_light.rotation = self.player.rotation
        self.show_fire_frames = 3

    def remove_projectile(self, projectile):
        self.projectiles.remove(projectile)
        # delay objects deletion until later, to avoid segfaults
        self.dead_items.add(projectile)

    def _remove_projectiles(self):
        for projectile in self.projectiles:
            self.remove_projectile(projectile)
        #print self.projectiles

    def _remove_dead_items(self):
        ###collision_layer = self.map_node.get('collision')
        for item in self.dead_items:
            ###collision_layer.remove(item, static=item.shape.static)
            if item in self.agents_node:
                self.agents_node.remove(item)
        self.dead_items.clear()

    def is_clear_path(self, origin, target):
        ray = Ray(self.player, target)
        ###collision_layer = self.map_node.get('collision')
        ###collision_layer.add(ray, static=ray.shape.static)
        ###collision_layer.step()
        ###collision_layer.remove(ray)
        return not ray.shape.data['collided']

    def is_empty(self,x,y):
        # note: ATM only walls, not muebles
        return self.wallmask.is_empty(x,y)




if __name__ == '__main__':
    main()
