from glob import glob
from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt, hypot
import random

from pyglet.image import Animation, AnimationFrame, load
from cocos.sprite import Sprite
from cocos.actions import MoveBy, FadeTo, CallFunc

import gg

BLOOD_SPLATTER_RANGE = 50, 200
BLOOD_SPLATTER_SECONDS = .7

# must return unix style paths, wich is wath pyglet.resources expects
def globx(s):
    import os
    if os.sep == '\\':
        s = s.replace('/',os.sep)
    li = glob(s)
    if os.sep == '\\':
        li = [ s.replace('\\','/') for s in li ]
    return li

def get_animation(anim_name):
    return Animation([AnimationFrame(load(img_file), 0.15)
                      for img_file in  globx('data/img/%s*.png' % anim_name)])

class Gore(Sprite):
    def __init__(self, *a, **kw):
        img = random.choice(self.images)
        super(Gore, self).__init__(img, *a, **kw)
        self.scale = 1.5
        self.label = None

class Blood(Gore):
    images = globx("data/img/sangre[0-9]*.png")

class BloodPool(Gore):
    images = globx("data/img/sangre_mancha[0-9]*.png")

class BodyParts(Gore):
    images = globx("data/img/cacho[0-9]*.png") + BloodPool.images

###  mixins to handle comands and state  ######################################

class CmdMixin(object):
##    def __init__(self):
##        self._devflags = {}

    def do_cmd(self,cmd, *args,**kwargs):
        if self.is_set_devflag('trace_cmds'):
            print 'do_cmd> agent |%s| received relayed command |%s| \n\targs=%s , \n\tkwargs=%s'%(self.label, cmd, args, kwargs)
        try:
            fn = getattr(self, 'a_%s'%cmd)
        except AttributeError:
            if self.is_set_devflag('show_errors'):
                print 'do_cmd_error> agent |%s| received the unknown command |%s|'%(self.label,cmd)
            return
        fn(*args,**kwargs)        

    def a_set_devflag(self, flag_name, boolean):
        """a_set_devflag(flag_name, boolean): self.devflag[flag_name] <- bool(boolean)
        Standart flags:
            trace_cmds
            show_errors
            trace_state_steps
            trace_state_changes
        """
        self._devflags[flag_name] = bool(boolean)

    def is_set_devflag(self, flag_name):
        """is_set_devflag(flag_name, boolean) -> self.devflag.setdefault('flag_name,false)
        Standart flags:
            trace_cmds
            show_errors
            trace_state_steps
            trace_state_changes
        """
        return self._devflags.setdefault(flag_name,False)

class CmdAndStateMixin(object):
##    def __init__(self):
##        self._devflags = {}
##        self.stname = ''
##        self.next_stname = ''

    def do_cmd(self,cmd, *args,**kwargs):
        if self.is_set_devflag('trace_cmds'):
            print 'do_cmd> agent |%s| received relayed command |%s| \n\targs=%s , \n\tkwargs=%s'%(self.label, cmd, args, kwargs)
        try:
            fn = getattr(self, 'a_%s'%cmd)
        except AttributeError:
            if self.is_set_devflag('show_errors'):
                print 'do_cmd_error> agent |%s| received the unknown command |%s|'%(self.label,cmd)
            return
        fn(*args,**kwargs)        

    def a_set_devflag(self, flag_name, boolean):
        """a_set_devflag(flag_name, boolean): self.devflag[flag_name] <- bool(boolean)
        Standart flags:
            trace_cmds
            show_errors
            trace_state_steps
            trace_state_changes
        """
        self._devflags[flag_name] = bool(boolean)

    def is_set_devflag(self, flag_name):
        """is_set_devflag(flag_name, boolean) -> self.devflag.setdefault('flag_name,false)
        Standart flags:
            trace_cmds
            show_errors
            trace_state_steps
            trace_state_changes
        """
        return self._devflags.setdefault(flag_name,False)

    def update(self,*args,**kwargs):
        if self.stname != self.next_stname:
            if self.is_set_devflag('trace_state_changes'):
                print 'state> entity |%s| changestate from: |%s| to: |%s|'%(self.label,self.stname,self.next_stname)
            self.stname = self.next_stname
        if self.is_set_devflag('trace_state_steps'):
            print 'state> entity |%s| in state |%s| doing update'%(self.label, self.stname)
        try:
            fn = getattr(self, 'e_%s'%self.stname)
        except AttributeError:
            if self.is_set_devflag('show_errors'):
                print 'state_error> entity |%s| in unknown state |%s|'%(self.label,self.stname)
            return
        fn(*args,**kwargs)        
            
##############################################################################

class Agent(Sprite,CmdAndStateMixin):

    def __init__(self, game_layer, img, position=(0,0), label=None, collision_radius=32.0):
        super(Agent, self).__init__(img, position)
        self.label = label
        self.game_layer = game_layer
        self.collision_radius = collision_radius
        
        # mixins initialize members
        self._devflags = {}
        self.stname = ''
        self.next_stname = ''

        self.anims = {}
        self.current_anim = 'idle'

        self.just_born = True
        self.life = gg.player_max_life
        self.collided_agent = None

    def update_position(self, position):
        self.collided_agent = None
        self.old_position = self.position
        self.position = position

        # check collisions with static objects
        if not self.game_layer.is_empty(*self.position):
            if not self.just_born:
                self.x = self.old_position[0]
                if not self.game_layer.is_empty(*self.position):
                    self.y = self.old_position[1]
                    self.x = position[0]
                    if not self.game_layer.is_empty(*self.position):
                        self.position = self.old_position
                        return
            else:
                self.x += random.random() * 40 - 20
                self.y += random.random() * 40 - 20
                return

        if self.just_born:
            self.old_position = position

        # check collisions with dynamic objects
        agents = self.parent.children
        collided = False
        for z, agent in agents: #? posiblemente no deberiamos considerar bullets aqui?
            if agent is self: continue
            distance = hypot((self.position[0]-agent.position[0]),(self.position[1]-agent.position[1]))
            collision = distance<self.collision_radius+agent.collision_radius

            if collision:
                collided = True
                if self.just_born:
                    self.x += random.choice([-1,1])*RANDOM_DELTA
                    self.y += random.choice([-1,1])*RANDOM_DELTA
                    self.position = (self.x, self.y)
                    return

                self.position = self.old_position
                self.on_collision(agent)
                agent.on_collision(self)

        if not collided:
            if self.just_born:
                self.just_born = False

    def play_anim(self, anim_name):
        self.image = self.anims[anim_name]
        self.image_anchor = (self.image.frames[0].image.width / 2,
                             self.image.frames[0].image.height / 2)
        self.current_anim = anim_name

    def on_collision(self, other):
        self.collided_agent = other #? solo usado para melee atack,
##        if isinstance(other, Bullet):
##            if isinstance(self, Zombie):
##                bullet = other
##                self.receive_damage(bullet.player.weapon.damage, bullet)
##        elif isinstance(other, Agent):
##             

    def _get_game_layer(self):
        raise NotImplementedError

    def receive_damage(self, damage, other):
        self.life -= damage
        ## return True if died
        if self.life <= 0:
            self.die()
            self.add_gore(BodyParts, other, duration=5)
            return True
        self.add_gore(Blood, other, duration=.5)
        return False

    def add_gore(self, gore_class, other, duration=5):
        gore = gore_class((self.x, self.y), other.rotation)
        dist = random.randrange(*BLOOD_SPLATTER_RANGE)
        alpha = radians(-other.rotation)
        gore.do(MoveBy( (cos(alpha)*dist, sin(alpha)*dist), BLOOD_SPLATTER_SECONDS))
        self.player.game_layer.deadstuff_layer.add(gore, duration)



