from glob import glob
import geom
from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt
from pyglet.image import Animation, AnimationFrame, load

from cocos.sprite import NotifierSprite

from boids import merge, seek, cap, avoid_group
import sound


def get_animation(anim_name):
    return Animation([AnimationFrame(load(img_file), 0.2)
                      for img_file in  glob('data/img/%s*.png' % anim_name)])


class Agent(NotifierSprite):
    def __init__(self, img, position=(0,0)):
        super(Agent, self).__init__(img, position)
        self.anims = {}
        self.current_anim = 'idle'
    
    def update_position(self, position):
        # test for collisions
        self.old_position = self.position
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

            self.position = position[0], self.old_position[1]
            self.collision = None
            collision_layer.step()
            if self.collision:
                self.position = self.old_position[0], position[1]
                self.collision = None
                collision_layer.step()
                if self.collision:
                    self.position = self.old_position

    def _on_collision(self, other):
        # used internally for collision testing
        if not self.updating:
            return
        self.collision = other

    def on_collision(self, other):
        # called when we want to report a collision
        pass

    def play_anim(self, anim_name):        
        self.image = self.anims[anim_name]
        self.image_anchor = (self.image.frames[0].image.width / 2,
                             self.image.frames[0].image.height / 2)
        self.current_anim = anim_name
        

class Father(Agent):
    def __init__(self, img, position, game_layer):
        super(Father, self).__init__(img, position)
        self._old_state = {'position': position}
        self.speed = 0
        self.position = position
        self.schedule(self.update)
        self.game_layer = game_layer
        self.acceleration = 0
        self.updating = False
        self.rotation_speed = 0
        self.collision = False
        self.anims = {'idle': get_animation('father_idle'),
                      'walk': get_animation('father_walk'),
                      }
        self.current_anim = 'idle'

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
        self.anims = {'idle': get_animation('zombie_idle'),
                      'walk': get_animation('zombie_walk'),
                      }
        self.current_anim = 'idle'

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

        if self.position != self.old_position:
            self.play_anim('walk')

        else:
            if self.current_anim != 'idle':
                self.play_anim('idle')

