import os.path
import simplejson
import random
import optparse
import time

import pyglet
from pyglet import gl
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
from tiless_editor.tiless_editor import LayersNode
from tiless_editor.tilesslayer import TilessLayer
from tiless_editor.atlas import SavedAtlas

from walls import create_wall_layer
import talk
import gamehud
import sound
from light import Light
import waypointing

from gamecast import Agent, Father, Zombie, Boy, Girl, Mother, Wall, ZombieSpawn, get_animation
from gamecast import PowerUp, POWERUP_TYPE_AMMO_LIST, POWERUP_TYPE_LIFE_LIST
from wallmask import WallMask

import scripter

import gg

#WIDTH, HEIGHT = 1024, 768
MAPFILE = 'data/map.json'
#RETREAT_DELAY = 0.1


has_grabber = True # potentially reset at startup or in .visit() 

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

def make_special_sprites_layer(layer_data, atlas, cls, game_layer):
    # cls reqires an init as def __init__(self,game_layer,json_obtained_dict):
    # the concrete use case is for ZombieSpawn
    # probably better if json_obtained_dict has key 'cls_name', wich will resolve here with
    # the aid of a name to class name 
    saved_atlas = SavedAtlas('data/atlas-fixed.png', 'data/atlas-coords.json')

    layer = BatchNode()
    for item in layer_data["sprites"]:
        obj = cls(game_layer,item)
        layer.add(obj, name=obj.label)
    return layer

class DeadStuffLayer(cocos.cocosnode.CocosNode):
    """Everything added to this node disappears a few seconds later"""

    def __init__(self):
        super(DeadStuffLayer, self).__init__()

    def add(self, child, duration=5, **kw):
        super(DeadStuffLayer, self).add(child, **kw)
        child.do(Delay(duration) + FadeOut(1) + CallFunc(lambda: self.remove(child)))

class GameLayer(Layer):
    is_event_handler = True

    def __init__(self, mapfile, hud):
        super(GameLayer, self).__init__()
        global has_grabber
        if has_grabber:
            width, height = director.get_window_size()

            self.texture = pyglet.image.Texture.create_for_size(
                    gl.GL_TEXTURE_2D, width,
                    height, gl.GL_RGBA)

            self.grabber = framegrabber.TextureGrabber()
            self.grabber.grab(self.texture)

        self.frame_time = 0.0
        self.map_node = LayersNode()
        self.dead_items = set()
        self.wallmask = WallMask()
        self.agents_node = LayersNode()
        self.script_director = scripter.ScriptDirector(scripter.script)
        self.objs_by_label = {}


        # get layers from map
        collision_layers = []
        walls_layers = []

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
            if layer_type == 'sprite' and layer_label=='zombie_spawn':
                sprite_layer = make_special_sprites_layer(layer_data['data'], self.atlas, ZombieSpawn, self)
                self.map_node.add_layer(layer_data['label'], layer_data['z'],sprite_layer)
                for z,c in sprite_layer.children:
                    self.objs_by_label[c.label] = c
                continue
            elif layer_type == 'sprite':
                sprite_layer = make_sprites_layer(layer_data['data'], self.atlas)
                if layer_label in ["floor", "furninture"]:
                    self.map_node.add_layer(layer_data['label'], layer_data['z'],
                                       sprite_layer)
                if layer_label in ['walls', 'furninture']:
                    collision_layers.append(sprite_layer)
                if layer_label in ['walls', 'gates']:
                    walls_layers.append(sprite_layer)
                if layer_label in ['item_spawn']:
                    item_spawn = sprite_layer
                if layer_label in ['waypoints']:
                    waypoints = sprite_layer
                    for z,c in sprite_layer.children: #? probably innecesary
                        self.objs_by_label[c.label] = c
                if layer_label in ['lights']:
                    self.lights = Light(sprite_layer)
                    for z,c in sprite_layer.children:
                        self.objs_by_label[c.label] = c


        # temporary dead stuff layer
        # it should be above the furniture, but below the walls
        self.deadstuff_layer = DeadStuffLayer()
        self.map_node.add(self.deadstuff_layer)

        # create collision info
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
        if gg.wpt_on:
            from wptlayer import WptLayer
            self.wptlayer = WptLayer(mapfile)
            self.map_node.add_layer('wptedit',1,self.wptlayer) # ?
        else:
            # LATER:
            # obtain wpts, instantiation need to wait until is safe to call
            # ray functions..
            wpts = [ (s.x,s.y) for s in waypoints.get_children()] #Esta bien asi Lucio?
            # a seguir

        # init terminates
        self.script_director.push_handlers(self.on_talk, self.on_relay)
        self.script_director.game_event_handler('map_loaded')
        print '+++ GameLayer init completado'

    def on_resize(self, w, h):
        global has_grabber
        if has_grabber:
            width, height = w, h
            print "RESETING TEXTURE", width, height


            self.texture = pyglet.image.Texture.create_for_size(
                    gl.GL_TEXTURE_2D, width,
                    height, gl.GL_RGBA)

    def visit(self):
        global has_grabber
        if not has_grabber:
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
            has_grabber = False # really can change ?


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

    def on_enter(self):
        self.enter_time = time.time()
        super(GameLayer, self).on_enter()
        x, y = director.get_window_size()
        self.lights.on_enter()
        sound.play('zombie_eat')

        self.do( Delay(3) + CallFunc(lambda: sound.stop_music()) +
                CallFunc(lambda: sound.play_music('game_music', 0.25)) )

    def on_exit(self):
        print "Exiting GameLayer"
        super(GameLayer, self).on_exit()
        #self.light.disable()
        self.lights.on_exit()
        sound.stop_music()

    def _create_agents(self):
        father = Father(self, get_animation('father_idle'), (40,-900))
        father.rotation = 90
        self.player = father
        self.hud.set_life("Dad", father.life)
        if hasattr(father.weapon, 'ammo'):
            self.hud.set_bullets(father.weapon.ammo)
        else:
            # fist weapon has no bullets
            self.hud.set_bullets(0)
        self.add_agent(father)

        # any actor except father must be added into the if, else they
        # pester you when editing waypoints
        if not gg.wpt_on:
            position = 40, -1200
            boy = Boy(self, get_animation('boy_idle'), position, self.player)
            boy.rotation = -90
            self.add_agent(boy)

            position = -100, -1050
            girl = Girl(self, get_animation('girl_idle'), position, self.player)
            self.add_agent(girl)

            position = 180, - 1050
            mother = Mother(self, get_animation('mother_idle'), position, self.player)
            mother.rotation = 180
            self.add_agent(mother)

    def update(self, dt):
        if dt>0.25:
            dt = 0.25
        self.frame_time += dt

        self.script_director.update(dt, self.frame_time)

        x, y = director.get_window_size()
        self.x = -self.player.x + x/2
        self.y = -self.player.y + y/2
        
        self._remove_dead_items()

    def talk(self, who, what, duration=5, transient=False):
        if who not in self.hud.deads:
            self.talk_layer.talk(who, what, duration=duration, transient=transient)

    def add_agent(self,obj):
        if obj.label:
            self.objs_by_label[obj.label] = obj
        self.agents_node.add(obj)

    def kill(self, obj):
        label = obj.label
        try:
            del self.objs_by_label[label]
        except KeyError:
            pass
        self.dead_items.add(obj)        

    def add_projectile(self, projectile):
        self.add_agent(projectile)

        self.fire_light.x = self.player.x
        self.fire_light.y = self.player.y
        self.fire_light.rotation = self.player.rotation
        self.show_fire_frames = 3

    def game_over(self):
        director.return_value = time.time() - self.enter_time
        director.replace(gg.services["s_get_end_scene"]())

    def on_talk(self,who, what, duration):
        self.talk(who, what, duration=duration, transient=False)

    def on_relay(self, label, *args, **kwargs):
        try:
            obj = self.objs_by_label[label]
        except KeyError:
            print 'relay error: unknown label',label
            return
        obj.do_cmd(*args,**kwargs)

    def _remove_dead_items(self):
        for item in self.dead_items:
            if item in self.agents_node:
                self.agents_node.remove(item)
        self.dead_items.clear()

    def is_empty(self,x,y):
        # note: ATM only walls, not muebles
        return self.wallmask.is_empty(x,y)


# service
def get_game_scene():
    
    # create game scene
    hud_layer = gamehud.HudLayer()
    game_layer = GameLayer(MAPFILE, hud_layer)

    scene = Scene()
    scene.add(game_layer)
    scene.add(hud_layer, z = 1)
    if gg.wpt_on:
        from gamectrl_wpt import MouseGameCtrl, KeyGameCtrl
    else:
        from gamectrl import MouseGameCtrl, KeyGameCtrl
    scene.add(KeyGameCtrl(game_layer))
    scene.add(MouseGameCtrl(game_layer))

    return scene

# publish services
gg.services["s_get_game_scene"] = get_game_scene
