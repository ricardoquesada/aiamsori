from glob import glob
import geom
import random
from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt
from pyglet.image import Animation, AnimationFrame, load
#from pymunk.vec2d import Vec2d

RANDOM_DELTA = 128

from cocos.sprite import Sprite

from boids import merge, seek, cap, avoid_group
#from shapes import BulletShape, RayShape, AgentShape, ZombieShape, WallShape
#from tiless_editor.layers.collision import Circle
import sound

# NOTE: select wich class will be used as Zombie near EOF

COLLISION_GROUP_FATHER = 1

COLLISION_DISTANCE_SQUARED = 64**2

TOP_SPEED = 430
ACCEL_FACTOR = 300

POWERUP_TYPE_WEAPON_LIST = ['shotgun']
POWERUP_TYPE_BULLETS = 'bullets'
POWERUP_TYPE_LIFE = 'life'
POWERUP_BULLETS = 5
POWERUP_LIFE = 20
FULL_LOAD_BULLETS = 50

PLAYER_MAX_LIFE = 100

def get_animation(anim_name):
    return Animation([AnimationFrame(load(img_file), 0.15)
                      for img_file in  glob('data/img/%s*.png' % anim_name)])

class Gore(Sprite):
    def __init__(self, *a, **kw):
        img = random.choice(self.images)
        super(Gore, self).__init__(img, *a, **kw)

class Blood(Gore):
    images = glob("data/img/sangre[0-9]*.png")

class BodyParts(Gore):
    images = glob("data/img/cacho[0-9]*.png")

class Agent(Sprite):
    def __init__(self, game_layer, img, position=(0,0)):
        super(Agent, self).__init__(img, position)
        self.anims = {}
        self.game_layer = game_layer
        self.current_anim = 'idle'

        ###self.shape = AgentShape(self)
        self.just_born = True
        self.life = PLAYER_MAX_LIFE
        self.collided_agent = None

    def update_position(self, position):
        self.old_position = self.position
        self.position = position

        # check collisions with static objects
        if not self.game_layer.is_empty(*self.position):
            self.x = self.old_position[0]
            if not self.game_layer.is_empty(*self.position):
                self.y = self.old_position[1]
                self.x = position[0]
                if not self.game_layer.is_empty(*self.position):
                    self.position = self.old_position
                    return

        # check collisions with dynamic objects
        agents = self.parent.children
        for z, agent in agents:
            if agent is self: continue
            distance = (self.position[0]-agent.position[0])**2+(self.position[1]-agent.position[1])**2
            collision = distance <= COLLISION_DISTANCE_SQUARED
            if collision:
                #print self, 'COLLISION', agent
                # objects collided
                if self.just_born:
                    print 'newborn collision', self.position
                    ###distance = (self.position[0]-agent.position[0])**2+(self.position[1]-agent.position[1])**2
                    ###collision = distance <= COLLISION_DISTANCE_SQUARED
                    ###while collision:
                    self.x += random.choice([-1,1])*RANDOM_DELTA
                    self.y += random.choice([-1,1])*RANDOM_DELTA
                    self.target = self.position = (self.x, self.y)
                    self.target = self.position
                    ###self.just_born = False
                    return

                #nx = self.old_position[0] + random.choice([-1,1])*RANDOM_DELTA
                #ny = self.old_position[1] + random.choice([-1,1])*RANDOM_DELTA
                #self.position = (nx, ny)
                self.position = self.old_position
                self.on_collision(agent)
                agent.on_collision(self)
                #f = getattr(self.collision, "on_collision", None)
                #if f is not None:
                #    f(self)

                #self.position = position[0], self.old_position[1]
                #collision = Vec2d(self.position).get_distance(agent.position) <= COLLISION_DISTANCE
                #if collision:
                #    self.position = self.old_position[0], position[1]
                #    collision = Vec2d(self.position).get_distance(agent.position) <= COLLISION_DISTANCE
                #    if collision:
                #        self.position = self.old_position
            else:
                if self.just_born:
                    self.just_born = False



    def _on_collision(self, other):
        # used internally for collision testing
        if isinstance(other, Bullet):
            self.on_collision(other)
        if not self.updating:
            return

    def play_anim(self, anim_name):
        self.image = self.anims[anim_name]
        self.image_anchor = (self.image.frames[0].image.width / 2,
                             self.image.frames[0].image.height / 2)
        self.current_anim = anim_name

    def on_collision(self, other):
        #print 'self', self, 'other', other
        if isinstance(other, Bullet):
            if not isinstance(self, Father):
                bullet = other
                self.receive_damage(bullet.player.weapon.damage, bullet)
        elif isinstance(other, Agent):
            self.collided_agent = other

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
        self.player.game_layer.deadstuff_layer.add(gore, duration)


class Family(Agent):
    def receive_damage(self, damage, other):
        super(Family, self).receive_damage(damage, other)
        self.game_layer.hud.set_life(self.name, self.life)

class Father(Family):
    name = "Dad"
    def __init__(self, game_layer, img, position):
        super(Father, self).__init__(game_layer, img, position)
        ###self.shape.group = COLLISION_GROUP_FATHER

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
        self.anim_sets = {'fist': {'idle': get_animation('father_idle'),
                                   'walk': get_animation('father_walk'),
                                   },
                          'shotgun': {'idle': get_animation('father_shotgun_idle'),
                                      'walk': get_animation('father_shotgun_walk'),
                                      },
                          }

##         self.anims = {'idle': get_animation('father_idle'),
##                       'walk': get_animation('father_walk'),
##                       }
        self.current_anim = 'idle'
        self.family = {}
        self.selected_relative = None
        self.just_born = False
        self.weapons = {'shotgun': RangedWeapon(self),
                        'fist': MeleeWeapon(self)}
        self.weapon = self.weapons['fist']
        self.time_since_attack = 0
        self.player = self #shortcut

    def on_collision(self, other):
        super(Father, self).on_collision(other)
        if isinstance(other, PowerUp):
            hud = self.game_layer.hud
            if other.type == POWERUP_TYPE_BULLETS:
                weapon = self.weapons['shotgun']
                weapon.ammo += POWERUP_BULLETS
                print 'new ammo', weapon.ammo
                hud.set_bullets(weapon.ammo)
            elif other.type == POWERUP_TYPE_LIFE:
                self.life += POWERUP_LIFE
                if self.life > PLAYER_MAX_LIFE:
                    self.life = PLAYER_MAX_LIFE
                print 'new life', self.life
                hud.set_life(self.name, self.life)
            elif other.type in POWERUP_TYPE_WEAPON_LIST:
                weapon = self.weapons[other.type]
                if hasattr(weapon, 'ammo'):
                    weapon.ammo += FULL_LOAD_BULLETS
                    hud.set_bullets(weapon.ammo)
                self.switch_weapon(other.type)

    def update(self, dt):
        # update speed
        if self.acceleration != 0 and abs(self.speed) < TOP_SPEED:
            self.speed += self.acceleration*ACCEL_FACTOR*dt

        self.rotation += 110 * self.rotation_speed * dt
        # update the position, based on the speed
        nx = (self.x + cos( radians(-self.rotation) ) * self.speed * dt)
        ny = (self.y + sin( radians(-self.rotation) ) * self.speed * dt)
        # FIXME: for some reason the x/y attributes don't update the position attribute correctly
        new_position = (nx, ny)

        self.update_position(new_position)

        # update layer position (center camera)
        self.game_layer.update(dt)
        self.time_since_attack += dt



    def look_at(self, px, py):
        # translate mouse position to world
        px = px - self.game_layer.x
        py = py - self.game_layer.y
        self.target = (px, py)
        pl_x, pl_y = self.position[0], self.position[1]
        self.rotation = -(atan2(py - pl_y, px - pl_x) / pi * 180)

    def attack(self):
        if self.time_since_attack > self.weapon.frequency:
            self.weapon.attack()
            self.time_since_attack = 0

    def die(self):
        # only mark it as dead, as I cannot remove the pymunk stuff while within the collision detection phase
        # as segfaults might occur
        game_layer = self.game_layer
        game_layer.dead_items.add(self)

    def _get_game_layer(self):
        return self.game_layer

    def switch_weapon(self, weapon_name):
        weapon = self.weapons[weapon_name]
        if hasattr(weapon, 'ammo') and weapon.ammo < 1:
            return
        self.weapon = weapon
        self.anims = self.anim_sets[weapon_name]
        self.play_anim('idle')


class Weapon(object):
    def __init__(self, player, damage, atk_range, frequency, sound=None):
        self.player = player
        self.damage = damage
        self.range = atk_range
        self.frequency = frequency
        self.sound = sound
        self.time_since_attack = 0

    def _play_sound(self):
        sound.play(self.sound)


class RangedWeapon(Weapon):
    def __init__(self, player, damage=60, atk_range=1000, frequency=1, sound='fire_shotgun'):
        super(RangedWeapon, self).__init__(player, damage, atk_range, frequency, sound)
        self.ammo = 0

    def attack(self):
        projectile = Bullet(get_animation('bullet'), self.player)
        self.player.game_layer.add_projectile(projectile)
        self._play_sound()
        self.ammo -= 1
        if self.ammo < 1:
            # defensive progamming
            self.ammo = 0
            self.player.switch_weapon('fist')
        self.player.game_layer.hud.set_bullets(self.ammo)


class MeleeWeapon(Weapon):
    def __init__(self, player, damage=35, atk_range=0, frequency=0.2, sound='melee'):
        super(MeleeWeapon, self).__init__(player, damage, atk_range, frequency, sound)

    def attack(self):
        print "ATTACK"
        if self.player.collided_agent != None:
            print 'morite!!', self.player.collided_agent
            died = self.player.collided_agent.receive_damage(self.damage, self.player)
            if died:
                self.player.collided_agent = None
            self._play_sound()


class Relative(Family):
    def __init__(self, game_layer, img, position, player):
        super(Relative, self).__init__(game_layer, img, position)
        self._old_state = {}
        self.speed = 100
        self.schedule(self.update)
        self.player = player
        self.updating = False
        self.collision = False
        self.current_anim = 'idle'
        self.target = self.position

    def update(self, dt):
        # move to designated target or stay and fight

        # save old position
        self._old_state = {'position': self.position, 'rotation': self.rotation}

        locals = []
        goal = seek(self.x, self.y, self.target[0], self.target[1])

        delta = geom.angle_rotation(radians(self.rotation), radians(goal))
        delta = degrees(delta)
        max_r = 270
        delta = cap(delta, -max_r, max_r) * dt
        self.rotation += delta

        # FIXME: for some reason the x/y attributes don't update the position attribute correctly
        self.position = (self.x, self.y)
        self.rotation = self.rotation % 360
        # update position
        a = -self.rotation
        nx = (self.x + cos( radians(a) ) * self.speed * dt)
        ny = (self.y + sin( radians(a) ) * self.speed * dt)

        self.update_position((nx, ny))

        if self.position != self.old_position:
            self.play_anim('walk')

        else:
            if self.current_anim != 'idle':
                self.play_anim('idle')

    def die(self):
        # only mark it as dead, as I cannot remove the pymunk stuff while within the collision detection phase
        # as segfaults might occur
        game_layer = self.player.game_layer
        game_layer.dead_items.add(self)

    def _get_game_layer(self):
        return self.player.game_layer


class Boy(Relative):
    name = "Zack"
    def __init__(self, game_layer, img, position, player):
        super(Boy, self).__init__(game_layer, img, position, player)
        self.anims = {'idle': get_animation('boy_idle'),
                      'walk': get_animation('boy_walk'),
                      }
        self.sounds = {}
        player.family['boy'] = self


class Girl(Relative):
    name = "Bee"
    def __init__(self, game_layer, img, position, player):
        super(Girl, self).__init__(game_layer, img, position, player)
        self.anims = {'idle': get_animation('girl_idle'),
                      'walk': get_animation('girl_walk'),
                      }
        self.sounds = {}
        player.family['girl'] = self


class Mother(Relative):
    name = "Mom"
    def __init__(self, game_layer, img, position, player):
        super(Mother, self).__init__(game_layer, img, position, player)
        self.anims = {'idle': get_animation('mother_idle'),
                      'walk': get_animation('mother_walk'),
                      }
        self.sounds = {}
        player.family['mother'] = self


# ZombieBoid , the old zombie class
class ZombieBoid(Agent):
    def __init__(self, game_layer, img, player):
        super(Zombie, self).__init__(game_layer, img)
        self._old_state = {}
        self.speed = 100
        self.schedule(self.update)
        self.player = player
        self.updating = False
        self.collision = False
        self.anims = {'idle': get_animation('zombie1_idle'),
                      'walk': get_animation('zombie1_walk'),
                      }
        self.current_anim = 'idle'
        ###self.shape = ZombieShape(self)
        self.last_goal = random.random()*0.3
        self.goal = self.position
        self.target = None


    def on_enter(self):
        super(ZombieBoid, self).on_enter()
        self.target = random.choice(
            [ p for p in self.parent.get_children() if isinstance(p, Family) ]
        )

    def update(self, dt):
        # save old position
        self._old_state = {'position': self.position, 'rotation': self.rotation}

        locals = []
        b = self
        self.last_goal += dt
        if self.last_goal > 0.3:
            self.last_goal = 0
            if self.target is None:
                target = self
            else:
                target = self.target
            self.goal = self.game_layer.ways.get_dest(self.position, target.position)
        gx, gy = self.goal
        goal = seek(b.x, b.y, gx, gy)
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

    def die(self):
        # only mark it as dead, as I cannot remove the pymunk stuff while within the collision detection phase
        # as segfaults might occur
        game_layer = self.player.game_layer
        game_layer.dead_items.add(self)

    def _get_game_layer(self):
        return self.player.game_layer


# actualmente es copia de ZombieBoid, esto es preparacion para implantar
class ZombieWpt(Agent):
    def __init__(self, game_layer, img, player):
        super(Zombie, self).__init__(game_layer, img)
        self._old_state = {}
        self.speed = 100
        self.schedule(self.update)
        self.player = player
        self.updating = False
        self.collision = False
        self.anims = {'idle': get_animation('zombie1_idle'),
                      'walk': get_animation('zombie1_walk'),
                      }
        self.current_anim = 'idle'
        ###self.shape = ZombieShape(self)

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
    def on_collision(self, other):
        #print 'Zombie on_collision', other
        #if isinstance(self.collision, Bullet):
        #    import pdb; pdb.set_trace()
        #elif isinstance(other.shape, Bullet):
        if isinstance(other, Bullet):
            #print 'Zombie hit at position', self.position
            self.die(other)

    def die(self, bullet):
        # only mark it as dead, as I cannot remove the pymunk stuff while within the collision detection phase
        # as segfaults might occur
        game_layer = self.player.game_layer
        game_layer.dead_items.add(self)

    def _get_game_layer(self):
        return self.player.game_layer

class Bullet(Sprite):
    def __init__(self, img, player):
        super(Bullet, self).__init__(img, player.position, player.rotation, player.scale)

        self.anims = {}
        self.player = player
        self.speed = 1500
        self.schedule(self.update)


        # get target
        WEAPON_RANGE = self.player.weapon.range

        #from pymunk.vec2d import Vec2d
        #offset = Vec2d(WEAPON_RANGE, 0).rotated(-self.rotation)
        #target = offset+position
        position = player.position
        nx = WEAPON_RANGE * cos( radians(-self.rotation) )
        ny = WEAPON_RANGE * sin( radians(-self.rotation) )
        target = (position[0] + nx, position[1] + ny)
        #print 'target ', target
        self.target = target
        #print 'BULLET CREATED'

        ###shape = BulletShape(self, position, target)
        ###shape.group = player.shape.group
        ###self.shape = shape

    def update(self, dt):
        goal = seek(self.x, self.y, self.target[0], self.target[1])

        self.position = (self.x, self.y)
        # update position
        a = -self.rotation
        nx = (self.x + cos( radians(a) ) * self.speed * dt)
        ny = (self.y + sin( radians(a) ) * self.speed * dt)

        #print 'updating bullet position', self.position, (nx,ny)
        self.update_position((nx, ny))
        # FIXME: this goes away as soon as bullets collide agains walls
        if nx > 1000 or nx < -1000 or ny > 1000 or ny < -1000:
            self.die()

    def update_position(self, position):
        self.position = position

    def on_collision(self, other):
        #print 'BULLET DIED'
        #print self, self.position, other, other.position
        if self.player != other:
            self.die()

    def die(self):
        # only mark it as dead, as I cannot remove the pymunk stuff while within the collision detection phase
        # as segfaults might occur
        game_layer = self.player.game_layer
        game_layer.dead_items.add(self)


class Ray(Sprite):
    def __init__(self, agent, target):
        super(Ray, self).__init__('img/bullet.png', agent.position, agent.rotation, agent.scale)
        ###shape = RayShape(self, agent.position, target)
        ###shape.group = agent.shape.group
        ###self.shape = shape


class Wall(Sprite):
    def __init__(self, child):
        img = {'filename': child.path, 'position': child.position,
               'rotation': child.rotation, 'scale': child.scale,
               'opacity': child.opacity, 'rect': child.rect}
        super(Wall, self).__init__(str(img['filename']), img['position'],
                                   img['rotation'], img['scale'],
                                   img['opacity'])
        self.label = None
        self.path = img['filename']
        self.rect = img['rect']
        ###self.shape = WallShape(self)

class PowerUp(Sprite):
    def __init__(self, type, position, game_layer):
        image = 'hud/%s.png' % type
        super(PowerUp, self).__init__(image, position)
        self.type = type
        self.game_layer = game_layer

    def on_collision(self, other):
        # remove powerup as we consumed it
        self.die()

    def die(self):
        self.game_layer.dead_items.add(self)
        self.game_layer.spawn_powerup()


#select here wich Zombie class
Zombie = ZombieBoid
