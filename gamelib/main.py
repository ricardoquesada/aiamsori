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
import time

from pyglet import gl, font
from pyglet.window import key

import cocos
from cocos import euclid
from cocos import framegrabber
from cocos.actions import Delay, CallFunc, FadeTo, FadeOut, Show, Hide, FadeIn, FadeOut
from cocos.director import director
from cocos.batch import BatchNode
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import Sprite
from cocos.scenes.transitions import TransitionScene
from cocos.text import Label
from cocos.sprite import Sprite

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
import waypointing

from gamecast import Agent, Father, Zombie, Boy, Girl, Mother, Wall, Ray, get_animation
from gamecast import PowerUp, POWERUP_TYPE_AMMO_LIST, POWERUP_TYPE_LIFE_LIST
from gamectrl import MouseGameCtrl, KeyGameCtrl
from wallmask import WallMask

#WIDTH, HEIGHT = 1024, 768
MAPFILE = 'data/map.json'
RETREAT_DELAY = 0.1

ZOMBIE_WAVE_COUNT = 4
ZOMBIE_DEBUG = 0
ZOMBIE_WAVE_DURATION = 60

RANDOM_DELTA = 128
UNKNOWN_ITEM_PROBABILTY = 0.1
UNKNOWN_PLACE_PROBABILTY = 0.1

options = None
has_grabber = True

WAVE_DELAY = [15, 30, 25, 25, 20, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11]
WAVE_NUM   = [1,  1,  1,  1,  2,  2,  2,  2,  2, 3, 3, 3, 4, 4, 4]

PWUP_MIN_TIME = 10
PWUP_MAX_TIME = 30

def get_intro_scene():
    x,y = director.get_window_size()
    image_layer = ImageLayer(x,y)
    scene = Scene()
    scene.add(image_layer)
    return scene

def get_game_scene():
    global has_grabber
    # create game scene
    hud_layer = gamehud.HudLayer()
    game_layer = GameLayer(MAPFILE, hud_layer, has_grabber)

    scene = Scene()
    scene.add(game_layer)
    scene.add(hud_layer, z = 1)
    if options.wpt_on:
        from gamectrl_wpt import MouseGameCtrl, KeyGameCtrl
    else:
        from gamectrl import MouseGameCtrl, KeyGameCtrl
    scene.add(KeyGameCtrl(game_layer))
    scene.add(MouseGameCtrl(game_layer))

    return scene

def get_end_scene():
    scene = Scene()
    scene.add(GameOverLayer())
    return scene


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
    basepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
    pyglet.resource.path.append(basepath)
    pyglet.resource.reindex()

    #Fonts stuff
    fonts_path = os.path.join(basepath, 'data/fonts')
    font.add_directory(fonts_path)

    print "#####################################################################"
    print "#####################################################################"
    print "###                                                               ###"
    print "###                 if you get a segfault                         ###"
    print "###                                                               ###"
    print "###                    please try again                           ###"
    print "###                                                               ###"
    print "###                multiplatform sound sucks                      ###"
    print "###                                                               ###"
    print "#####################################################################"
    print "#####################################################################"

    #Load avbin
    avbin.init_avbin()

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
    director.init(fullscreen=True)
#    director.init(options.width, options.height, resizable=True)
    sound.init()

    director.set_3d_projection()
#    director.set_2d_projection()

    # FIXME: transition between scenes are not working
    scene = get_intro_scene()
    #scene = get_game_scene()
    #scene = get_end_scene()
    director.run(scene)

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
        self.state = "intro"

        grossini = Sprite('data/img/grossini.png')
        mom = Sprite('data/img/Mom.png')
        bee = Sprite('data/img/Bee.png')
        zack = Sprite('data/img/Zack.png')
        dad = Sprite('data/img/Dad.png')
        sprites = [grossini, mom, bee, zack, dad]
        for s in sprites:
            self.add(s)
            s.position = self.w / 2, self.h / 2
            s.do(Hide())

        # grossini abajo a la izquierda
        grossini.position = self.w - grossini.image.width, grossini.image.height
        #texts = ['aiamsori productions presents...', '', '', '', '','and the neighbours','', 'in',]
        texts = ['productions.png'] + ['none.png'] * 4 + ['neigs.png', 'none.png', 'in.png']
        labels = []
        for t in texts:
#            l = Sprite(os.path.join('data', 'img', t)) # not found in win
            l = Sprite('/'.join(['data', 'img', t]))
            l.position = self.w / 2, self.h / 2
            labels.append(l)
            self.add(l, z=1)
            l.do(Hide())

        delay = 1
        ft = 1
        for l in labels:
            l.do(Delay(delay) + Show() + FadeIn(ft) + Delay(1) + FadeOut(ft))
            delay += 3

        delay = 1
        for s in sprites:
            s.do(Delay(delay) + Show() + FadeIn(ft) + Delay(1) + FadeOut(ft))
            delay += 3

        delay += 3
        zombies = []
        for zf in [
                'img/Punkie zombie.png',
                'img/Afro zombie.png',
                'img/Fat zombie byn.png',
                'img/Bitch zombie.png',
                ]:
            s = Sprite(zf)
            self.add(s)
            s.position = self.w / 2, self.h / 2
            s.do(Hide())
            zombies.append(s)

        for s in zombies:
            s.do(Delay(delay) + Show() + FadeIn(0.3) + Delay(0.3) + FadeOut(0.3))
            delay += 0.7

        self.borrar = labels + sprites
        self.do(Delay(delay+3) + CallFunc(lambda: self.goto_title()))
        sound.play_music("intro_music")

#    def on_key_press(self, k, m):
    def goto_title(self):
        self.state = "title"
        [self.remove(h) for h in self.borrar]
        x,y = self.w, self.h
##        labelkey = Label('press any key to start', font_name='Times New Roman', font_size=28, bold=True, anchor_x='center')
##         labelkey.position = self.w / 2  , 150
##         labelkey.element.color = 0,0,0,180
##         self.add(labelkey, z=1)
##         labelkey.do(Hide())

        bg = Sprite('data/img/ppl.png')
        self.add(bg)
        bg._vertex_list.vertices = [0,0,x,0,x,y,0,y]
#        labelkey.do(Delay(5) + Show() + FadeIn(2))
        self.do(Delay(4) + CallFunc(lambda: self.goto_game()))


    def on_key_press( self, symbol, modifiers ):
        if symbol == pyglet.window.key.ESCAPE:
            if self.state == "intro":
                self.goto_title()
            if self.state == "title":
                self.goto_game()

            return True

    def goto_game(self):
        sound.stop_music()
        director.replace(get_game_scene())
        self.state = 2


class GameOverLayer(Layer):
    is_event_handler = True

    def __init__(self):
        super(GameOverLayer, self).__init__()
        w, h = director.get_window_size()
        label = Label("You've lasted  %ds..." % director.return_value, font_name='youmurdererbb_reg', font_size=42, bold=True)
        label.position = w / 2 - 340 , h / 2 + 100
#        label.element.color = 40,179,75,180
        label.element.color = 255,255,255,255
        label2 = Label('do you want to play again?', font_name='youmurderer', font_size=42, bold=True)
        label2.position = w / 2 - 420 , h / 2
        label2.element.color = 40,179,75,180
        label3 = Label('(Y/N)', font_name='youmurdererbb', font_size=52, bold=True)
        label3.position = w / 2 - 40, h / 2 - 100
        label3.element.color = 40,179,75,180
        self.add(label, z=1)
        #label.do(Hide() + Delay(10) + Show())
        label2.do(Delay(10) + Show())
        label3.do(Delay(10) + Show())
        self.add(label)
        self.add(label2)
        self.add(label3)
        sound.play("MusicEnd")

    def on_key_press(self, k, m):
        sound.stop_music()
        if k == key.Y:
            game_scene = get_game_scene()
            director.replace(game_scene)
            return True
        elif k == key.N:
            director.pop()
            return True



class DeadStuffLayer(cocos.cocosnode.CocosNode):
    """Everything added to this node disappears a few seconds later"""

    def __init__(self):
        super(DeadStuffLayer, self).__init__()

    def add(self, child, duration=5, **kw):
        super(DeadStuffLayer, self).add(child, **kw)
        child.do(Delay(duration) + FadeOut(1) + CallFunc(lambda: self.remove(child)))

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
        self.zombie_wave_number = 0
        self.schedule(self.respawn_zombies)

        img = pyglet.image.load(  'data/atlas-fixed.png' )
        self.atlas = pyglet.image.atlas.TextureAtlas( img.width, img.height )
        self.atlas.texture = img.texture
        pyglet.gl.glTexParameteri( img.texture.target, pyglet.gl.GL_TEXTURE_WRAP_S, pyglet.gl.GL_CLAMP_TO_EDGE )
        pyglet.gl.glTexParameteri( img.texture.target, pyglet.gl.GL_TEXTURE_WRAP_T, pyglet.gl.GL_CLAMP_TO_EDGE )

        self.show_fire_frames = 0
        self.fire_lights = Layer()
        self.fire_light = Sprite("data/newtiles/luz_escopeta.png")
        self.fire_light.scale = 1
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


        # temporary dead stuff layer
        # it should be above the furniture, but below the walls
        self.deadstuff_layer = DeadStuffLayer()
        self.map_node.add(self.deadstuff_layer)

        # create collision shapes
        ###collision_layer = self._create_collision_layer(for_collision_layers)
        ###self.map_node.add_layer('collision', 1000, collision_layer)
        self.map_node.add(create_wall_layer(walls_layers), z=10)
        # add scene map node to the main layer
        self.add(self.map_node)

        self.add(self.agents_node, z=1)

        # talk queue
        self.hud = hud
        self.talk_layer = talk.TalkLayer()
        self.hud.add(self.talk_layer, z=10)
        #self.talk("Dad", "DAMN ZOMBIES!!!! Where's my shotgun!!!")
        #self.talk("Dad", "hello hello hello"*5)
        #self.talk("Bee", "Bye Bye"*5, transient=False, duration=2)


        x, y = director.get_window_size()
        #self.light = light.Light(x/2, y/2)

        # ends wallmask preparation, makes available service .is_empty(x,y)
        #self.wallmask.get_mask() #called for side effect _fill_gaps
        for layer in collision_layers:
            for child in layer.get_children():
                self.wallmask.add(child)
        # now is safe to call self.is_empty()

        # create agents (player and NPCs)
        self._create_agents()

        # calculate waypoints
        self.setup_waypoints(waypoints)
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

        self.setup_powerups(item_spawn)

        self.flicker()

    def flicker(self):
        delay = random.random()*5+2
        action = Delay(delay)
        light = random.choice(self.lights.get_children())

        for i in range(random.randint(5, 10)):
            micro_delay = random.random()*0.50
            micro_delay2 = random.random()*0.50
            action = action + FadeTo(50, micro_delay) + FadeTo(255, micro_delay2)
        action = action + CallFunc(self.flicker)
        light.do(action)


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
        try:

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
        except pyglet.gl.GLException:
            print "***"*1000, "nograbber"
            self.has_grabber = False


    def on_key_press( self, symbol, modifiers ):
        if symbol == pyglet.window.key.F and (modifiers & pyglet.window.key.MOD_ACCEL):
            return True

    def setup_waypoints(self, layer):
        print "Setting up navigation..."
        self.waypoints_list = points = [ c.position for c in layer.get_children() ]
        def is_visible(p, q):
            if p == q:
                return True

            p = euclid.Vector2(*p)
            q = euclid.Vector2(*q)
            d = p-q

            steps = d.magnitude() / 30
            for i in range(int(steps+1)):
                c = q+d*(i/float(steps))
                if not self.is_empty(*c):
                    return False
            return True

        visible_map = set()
        not_visible_map = set()
        for a in points:
            for b in points:
                if is_visible(a, b):
                    visible_map.add((a,b))
                else:
                    not_visible_map.add((a,b))
        def visible(a, b):
            if (a,b) in visible_map:
                return True
            if (a,b) in not_visible_map:
                return False
            return is_visible(a, b)

        def _visible(a, b):
            r = _visible(a, b)
            #print "visible", a, b, r
            return r
        print "Found", len(visible_map), "connections"
        self.ways = waypointing.WaypointNav(points, visible)
        print "Navigation setup done."

    def setup_powerups(self, layer):
        self.item_spawn = []
        for c in layer.get_children():
            self.item_spawn.append( c.position )
        # wait 4 seconds before displaying first message
        self.do(Delay(3) + CallFunc(lambda: self.talk('Bee', "Zombies are coming!", duration=2, transient=False)))
        self.do(Delay(5) + CallFunc(lambda: self.talk('Mom', "Protect your family!", duration=2, transient=False)))
        self.do(Delay(7) + CallFunc(lambda: self.talk('Zack', "Click on us to move us", duration=2, transient=False)))
        self.do(Delay(9) + CallFunc(lambda: self.add_powerup('shotgun', "DAMN ZOMBIES!!!! Where's my shotgun!!!")))
        self.spawn_powerup()

    def spawn_powerup(self, type=''):
        delay = random.randrange(PWUP_MIN_TIME, PWUP_MAX_TIME)
        self.do(Delay(delay) + CallFunc(lambda: self.add_powerup(type)))

    def add_powerup(self, type='', msg=''):
        position = random.choice(self.item_spawn)
        if not type:
            # make ammo and life categories equally probable
            type = random.choice(POWERUP_TYPE_AMMO_LIST*3 + POWERUP_TYPE_LIFE_LIST)
        powerup = PowerUp(type, position, self)
        self.agents_node.add(powerup)
        item = type
        if item == 'burger':
            item = 'a burger'
        elif item == 'medicine':
            item = 'some medicine'
        if random.random() < UNKNOWN_ITEM_PROBABILTY:
            item = ''
        place = powerup.label if hasattr(powerup, 'label') else ''
        if random.random() < UNKNOWN_PLACE_PROBABILTY:
            place = ''
        if not msg:
            msg = "I think I remember seeing "
            if item:
                msg += item
            else:
                msg += 'something'
            if place:
                msg += " in the %s." % place
            else:
                msg += ' somewhere.'
        self.talk("Dad", msg, transient=False)
        #print "powerup ", powerup, 'at', place, position

    def respawn_zombies(self, dt):

        if ZOMBIE_DEBUG:
            if self.z_spawn_lifetime == 0:
                print "NEW ZOMBIE"
                p = self.zombie_spawn.get_children()[0]
                z = Zombie(self, get_animation('zombie1_idle'), self.player)
                z.position = p.position
                self.agents_node.add(z)
                print "NEW ZOMBIE"
                z = Zombie(self, get_animation('zombie1_idle'), self.player)
                z.position = p.position
                self.agents_node.add(z)


            self.z_spawn_lifetime += 1
        else:
            self.z_spawn_lifetime += dt
            waveno = min(self.zombie_wave_number,len(WAVE_DELAY)-1)
            delay = WAVE_DELAY[ waveno ]
            if self.z_spawn_lifetime >= delay:
                z_count = len([c for c in self.agents_node.get_children() if isinstance(c, Zombie)])
                if z_count < 12:
                    print "Wave Numer:", waveno, z_count
                    # we have a zombie wave
                    msg = random.choice([
                        "cerebroooo.....",
                        "brraaaaaiins....",
                        "arrghhhhh....",
                        "me hungry!"
                    ])
                    self.talk("zombie", msg)
                    for i in range(WAVE_NUM[ waveno ]):
                        for c in self.zombie_spawn.get_children():
                            z = Zombie(self, get_animation('zombie1_idle'), self.player)
                            z.x = c.x + random.choice([-1,1])*RANDOM_DELTA
                            z.y = c.y + random.choice([-1,1])*RANDOM_DELTA
                            z.position = z.x, z.y
                            self.agents_node.add(z)
                    self.z_spawn_lifetime = 0
                    self.zombie_wave_number += 1


    def talk(self, who, what, duration=5, transient=False):
        if who not in self.hud.deads:
            self.talk_layer.talk(who, what, duration=duration, transient=transient)

    def on_enter(self):
        self.enter_time = time.time()
        super(GameLayer, self).on_enter()
        x, y = director.get_window_size()
        self.lights.on_enter()
        sound.play('zombie_eat')

        self.do( Delay(3) + CallFunc(lambda: sound.stop_music()) +
                CallFunc(lambda: sound.play_music('game_music', 0.25)) )

        #self.light.set_position(x/2, y/2)
        #self.light.enable()

    def on_exit(self):
        print "Exiting GameLayer"
        super(GameLayer, self).on_exit()
        #self.light.disable()
        self.lights.on_exit()
        sound.stop_music()



    def _create_agents(self):
        # get collision layer

        # create agent sprite
        father = Father(self, get_animation('father_idle'), (40,-900))
        father.rotation = 90
        self.player = father
        self.hud.set_life("Dad", father.life)
        if hasattr(father.weapon, 'ammo'):
            self.hud.set_bullets(father.weapon.ammo)
        else:
            # fist weapon has no bullets
            self.hud.set_bullets(0)
        self.agents_node.add(father)

        # any actor except father must be added into the if, else they
        # pester you when editing waypoints
        if not options.wpt_on:
            position = 40, -1200
            boy = Boy(self, get_animation('boy_idle'), position, self.player)
            boy.rotation = -90
            self.agents_node.add(boy)

            position = -100, -1050
            girl = Girl(self, get_animation('girl_idle'), position, self.player)
            self.agents_node.add(girl)

            position = 180, - 1050
            mother = Mother(self, get_animation('mother_idle'), position, self.player)
            mother.rotation = 180
            self.agents_node.add(mother)

    def update(self, dt):
        x, y = director.get_window_size()
        self.x = -self.player.x + x/2
        self.y = -self.player.y + y/2
        #self.lights.sprite.position = self.player.position

        # clear out any non-collisioned projectiles
#        self._remove_projectiles()

        # clear out any dead items
        self._remove_dead_items()


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

    def game_over(self):
        director.return_value = time.time() - self.enter_time
        director.replace(get_end_scene())




if __name__ == '__main__':
    main()
