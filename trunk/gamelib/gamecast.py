from glob import glob
import geom
import random
from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt
from pyglet.image import Animation, AnimationFrame, load
#from pymunk.vec2d import Vec2d

RANDOM_DELTA = 128

from cocos.sprite import Sprite
from cocos.actions.interval_actions import MoveBy
from cocos.euclid import Point2
from boids import merge, seek, cap, avoid_group
#from shapes import BulletShape, RayShape, AgentShape, ZombieShape, WallShape
#from tiless_editor.layers.collision import Circle
import sound

# NOTE: select wich class will be used as Zombie near EOF

COLLISION_GROUP_FATHER = 1

COLLISION_DISTANCE_SQUARED = 64**2

TOP_SPEED = 430
ACCEL_FACTOR = 300

POWERUP_TYPE_AMMO_LIST = ['bullets']
POWERUP_TYPE_WEAPON_LIST = ['shotgun']
POWERUP_TYPE_FOOD_LIST = ['chicken', 'burger']
POWERUP_TYPE_HEALTH_LIST = ['medicine']
POWERUP_TYPE_LIFE_LIST = POWERUP_TYPE_FOOD_LIST + POWERUP_TYPE_HEALTH_LIST
POWERUP_AMMO = 15
POWERUP_LIFE = {'chicken': 20, 'burger': 20, 'medicine': 50}
WEAPON_FULL_AMMO = 25
PLAYER_MAX_LIFE = 100

BLOOD_SPLATTER_RANGE = 50, 200
BLOOD_SPLATTER_SECONDS = .7

BLOODY_HANDS_EASTEREGG = False

####Pruebas hechas en win:
####No conversion , glob encuentra nombres, pero los entrga con barras mezcladas,
####cuelga el app no encontrando file (ej: "data/img\sangre1.png" not found )
####Convertir a win antes de glob, salen barras parejas tipo windows, igual
#### el app saca "data\img\sangre2.png" not found ( la intercepcion de glob
#### mostraba que habia encontrado  'data\\img\\sangre2.png' )
####Convertir antes a win y despues del glob a unix: BINGO!!!. take that, sucker!!!
##def globx(s):
##    import os
##    print '*** globx'
##    print 's:',s
##    if os.sep == '\\':
##        z = s.replace('/',os.sep)
##        s = z
##        print 'z:',z
##    li = glob(s)
##    print 'glob results unconverted:'
##    print li
##    if os.sep == '\\':
##        li2 = [ s.replace('\\','/') for s in li ]
##        li = li2
##        print 'glob result converted back to unix:'
##        li
##    return li

def globx(s):
    import os
    if os.sep == '\\':
        z = s.replace('/',os.sep)
        s = z
    li = glob(s)
    if os.sep == '\\':
        li2 = [ s.replace('\\','/') for s in li ]
        li = li2
        # 'glob result converted back to unix:'
    return li


def get_animation(anim_name):
    return Animation([AnimationFrame(load(img_file), 0.15)
                      for img_file in  globx('data/img/%s*.png' % anim_name)])

class Gore(Sprite):
    def __init__(self, *a, **kw):
        img = random.choice(self.images)
        super(Gore, self).__init__(img, *a, **kw)
        self.scale = 1.5

class Blood(Gore):
    images = globx("data/img/sangre[0-9]*.png")

class BloodPool(Gore):
    images = globx("data/img/sangre_mancha[0-9]*.png")

class BodyParts(Gore):
    images = globx("data/img/cacho[0-9]*.png") + BloodPool.images

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

        is_family = isinstance(self, Relative)
        # check collisions with dynamic objects
        agents = self.parent.children
        collided = False
        for z, agent in agents:
            if agent is self: continue
            distance = (self.position[0]-agent.position[0])**2+(self.position[1]-agent.position[1])**2
            collision = distance <= COLLISION_DISTANCE_SQUARED

            if is_family:
                if isinstance(agent, Father):
                    if distance > 1100**2:
                        self.alone = True
                    else:
                        self.alone = False


            if collision:
                collided = True
                # objects collided
                if self.just_born:
                    ###distance = (self.position[0]-agent.position[0])**2+(self.position[1]-agent.position[1])**2
                    ###collision = distance <= COLLISION_DISTANCE_SQUARED
                    ###while collision:
                    self.x += random.choice([-1,1])*RANDOM_DELTA
                    self.y += random.choice([-1,1])*RANDOM_DELTA
                    self.position = (self.x, self.y)
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

        if not collided:
            if self.just_born:
                self.just_born = False


    def play_anim(self, anim_name):
        self.image = self.anims[anim_name]
        self.image_anchor = (self.image.frames[0].image.width / 2,
                             self.image.frames[0].image.height / 2)
        self.current_anim = anim_name

    def on_collision(self, other):
        #print 'self', self, 'other', other
        if isinstance(other, Bullet):
#            if not isinstance(self, Father):
            if isinstance(self, Zombie):
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
        dist = random.randrange(*BLOOD_SPLATTER_RANGE)
        alpha = radians(-other.rotation)
        gore.do(MoveBy( (cos(alpha)*dist, sin(alpha)*dist), BLOOD_SPLATTER_SECONDS))
        self.player.game_layer.deadstuff_layer.add(gore, duration)


class Family(Agent):
    def receive_damage(self, damage, other):
        self.life -= damage
        self.game_layer.hud.set_life(self.name, self.life)
        ## return True if died
        if self.life <= 0:
            self.die()
            self.add_gore(BloodPool, other, duration=5)
            return True
        self.add_gore(Blood, other, duration=.5)
        return False

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
        #self.weapons = {'shotgun': RangedWeapon(self),
        #                'fist': MeleeWeapon(self)}
        self.weapons = {'fist': MeleeWeapon(self)}
        self.weapon = self.weapons['fist']
        self.ammo = 0
        self.time_since_attack = 0
        self.player = self #shortcut

    def on_collision(self, other):
        super(Father, self).on_collision(other)
        hud = self.game_layer.hud
        if isinstance(other, PowerUp):
            if other.type in POWERUP_TYPE_AMMO_LIST:
                if self.weapons.has_key('shotgun'):
                    weapon = self.weapons['shotgun']
                    weapon.ammo += POWERUP_AMMO
                    hud.set_bullets(weapon.ammo)
                    self.switch_weapon('shotgun')
                    sound.play('pickup_shotgun')
                else:
                    self.ammo += POWERUP_AMMO
                    hud.set_bullets(self.ammo)
            elif other.type in POWERUP_TYPE_LIFE_LIST:
                self.life += POWERUP_LIFE[other.type]
                if self.life > PLAYER_MAX_LIFE:
                    self.life = PLAYER_MAX_LIFE
                sound.play('pickup_helth')
                hud.set_life(self.name, self.life)
            elif other.type in POWERUP_TYPE_WEAPON_LIST:
                if self.weapons.has_key(other.type):
                    weapon = self.weapons[other.type]
                    if hasattr(weapon, 'ammo'):
                        weapon.ammo += WEAPON_FULL_AMMO
                        hud.set_bullets(weapon.ammo)
                    else:
                        return
                elif other.type == 'shotgun':
                    weapon = RangedWeapon(self)
                    weapon.ammo += self.ammo
                    self.ammo = 0
                    weapon.ammo += WEAPON_FULL_AMMO
                    hud.set_bullets(weapon.ammo)
                    self.weapons['shotgun'] = weapon
                self.switch_weapon('shotgun')
                sound.play('pickup_shotgun')
        elif isinstance(other, Relative):
            if self.weapons.has_key('shotgun'):
                weapon = self.weapons['shotgun']
                weapon.ammo += other.ammo
                other.ammo = 0
                hud.set_bullets(weapon.ammo)
                self.switch_weapon('shotgun')
                sound.play('pickup_shotgun')
            

    def update(self, dt):
        # update speed
        if self.acceleration != 0 and abs(self.speed) < TOP_SPEED:
            self.speed += self.acceleration*ACCEL_FACTOR*dt

##        self.rotation += 110 * self.rotation_speed * dt

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
        game_layer.game_over()

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
    def __init__(self, player, damage=100, atk_range=1000, frequency=0.6, sound='fire_shotgun'):
        super(RangedWeapon, self).__init__(player, damage, atk_range, frequency, sound)
        self.ammo = 0

    def attack(self):
        projectile = Bullet('img/bullet.png', self.player)
        self.player.game_layer.add_projectile(projectile)
        self._play_sound()
        self.ammo -= 1
        if self.ammo < 1:
            # defensive progamming
            self.ammo = 0
            self.player.switch_weapon('fist')
        self.player.game_layer.hud.set_bullets(self.ammo)


class MeleeWeapon(Weapon):
    def __init__(self, player, damage=20, atk_range=0, frequency=0.2, sound='melee'):
        super(MeleeWeapon, self).__init__(player, damage, atk_range, frequency, sound)

    def attack(self):
#        print "ATTACK"
        if BLOODY_HANDS_EASTEREGG:
            self.player.add_gore(Blood, self.player, duration=.5)

        if self.player.collided_agent != None:
#            print 'morite!!', self.player.collided_agent
            died = self.player.collided_agent.receive_damage(self.damage, self.player)
            if died:
                self.player.collided_agent = None
            self._play_sound()

class ZombieMeleeWeapon(MeleeWeapon):
    def __init__(self, player, damage=8, atk_range=0, frequency=2, sound='melee'):
        super(ZombieMeleeWeapon, self).__init__(player, damage, atk_range, frequency, sound)


class Relative(Family):
    def __init__(self, game_layer, img, position, player):
        super(Relative, self).__init__(game_layer, img, position)
        self._old_state = {}
        self.speed = 300
        self.schedule(self.update)
        self.player = player
        self.updating = False
        self.collision = False
        self.current_anim = 'idle'
        #self.target = self.position
        self.target = self.position
        self.goal = self.position
        self.updatecounter = 200
        self.mm = 0
        self.last_goal = 0
        self.alone = False
        self.last_alone = False
        self.ammo = 0

    def update(self, dt):
        # move to designated target or stay and fight

        # save old position
        self._old_state = {'position': self.position, 'rotation': self.rotation}

        locals = []
        if self.target and abs(Point2(*self.position) - Point2(*self.target) ) < 100:
            self.target = None

        self.last_goal += dt
        if self.target:

            if self.last_goal > 0.3:
                self.last_goal = 0
                self.goal = self.game_layer.ways.get_dest(self.position, self.target)
            goal = seek(self.x, self.y, self.goal[0], self.goal[1])

            #delta = geom.angle_rotation(radians(self.rotation), radians(goal))
            #delta = degrees(delta)
            #max_r = 5*270
            #delta = cap(delta, -max_r, max_r) * dt
            #self.rotation += delta
            self.rotation = goal
            # FIXME: for some reason the x/y attributes don't update the position attribute correctly
            self.position = (self.x, self.y)
            self.rotation = self.rotation % 360
            # update position
            a = -self.rotation
            nx = (self.x + cos( radians(a) ) * self.speed * dt)
            ny = (self.y + sin( radians(a) ) * self.speed * dt)

            self.update_position((nx, ny))
        else:
            self.update_position(self.position)

        if not self.last_alone and self.alone:
            if random.random() < 0.10:
                self.panic()
        if not self.alone and self.last_alone:
            print "NOT ALONE", self
        self.last_alone = self.alone

        if self.position != self.old_position:
            self.play_anim('walk')

        else:
            if self.current_anim != 'idle':
                self.play_anim('idle')

    def panic(self):
        self.target = random.choice(self.game_layer.waypoints_list)
        message = random.choice([
            "I'm scared!",
            "Zombies are everywhere! HELP!",
            "I need to run away!",
            "No one is here to protect me!"

        ])
        self.game_layer.talk(self.name, message, transient=False, duration=2)


    def die(self):
        # only mark it as dead, as I cannot remove the pymunk stuff while within the collision detection phase
        # as segfaults might occur
        game_layer = self.player.game_layer
        game_layer.dead_items.add(self)

        # check if whole family is dead
        if not self.player.family:
            game_layer.game_over()
        sound.play("player_die")

    def _get_game_layer(self):
        return self.player.game_layer

    def on_collision(self, other):
        super(Relative, self).on_collision(other)
        if isinstance(other, PowerUp):
            hud = self.game_layer.hud
            if other.type in POWERUP_TYPE_AMMO_LIST:
                # family just collects ammo for later use
                self.ammo += POWERUP_AMMO
            elif other.type in POWERUP_TYPE_LIFE_LIST:
                self.life += POWERUP_LIFE[other.type]
                if self.life > PLAYER_MAX_LIFE:
                    self.life = PLAYER_MAX_LIFE
                sound.play('pickup_helth')
                hud.set_life(self.name, self.life)

class Boy(Relative):
    name = "Zack"
    def __init__(self, game_layer, img, position, player):
        super(Boy, self).__init__(game_layer, img, position, player)
        self.anims = {'idle': get_animation('boy_idle'),
                      'walk': get_animation('boy_walk'),
                      }
        self.sounds = {}
        player.family['boy'] = self

    def die(self):
        del self.player.family['boy']
        super(Boy, self).die()


class Girl(Relative):
    name = "Bee"
    def __init__(self, game_layer, img, position, player):
        super(Girl, self).__init__(game_layer, img, position, player)
        self.anims = {'idle': get_animation('girl_idle'),
                      'walk': get_animation('girl_walk'),
                      }
        self.sounds = {}
        player.family['girl'] = self

    def die(self):
        del self.player.family['girl']
        super(Girl, self).die()


class Mother(Relative):
    name = "Mom"
    def __init__(self, game_layer, img, position, player):
        super(Mother, self).__init__(game_layer, img, position, player)
        self.anims = {'idle': get_animation('mother_idle'),
                      'walk': get_animation('mother_walk'),
                      }
        self.sounds = {}
        player.family['mother'] = self

    def die(self):
        del self.player.family['mother']
        super(Mother, self).die()


class Zombie(Agent):
    def __init__(self, game_layer, img, player):
        super(Zombie, self).__init__(game_layer, img)
        self._old_state = {}
        self.speed = 100
        self.schedule(self.update)
        self.player = player
        self.updating = False
        self.collision = False

        n_zombie = random.choice([1,2,3])

        self.anims = {'idle': get_animation('zombie%d_idle'%n_zombie),
                      'walk': get_animation('zombie%d_walk'%n_zombie),
                      }
        self.current_anim = 'idle'

        self.weapon = ZombieMeleeWeapon(self)
        self.time_since_attack = 0

        ###self.shape = ZombieShape(self)
        self.last_goal = random.random()*0.3
        self.goal = self.position
        self.target = self.player


    def on_enter(self):
        super(Zombie, self).on_enter()
        self.pick_target()

    def pick_target(self):
        family = [ p for p in self.parent.get_children() if isinstance(p, Family) ]
        if family:
            self.target = random.choice(
                family
            )
        else:
            self.target = self

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
                if self.target.life <= 0:
                    self.pick_target()
                target = self.target
            self.goal = self.game_layer.ways.get_dest(self.position, self.target.position)

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

        self.game_layer.update(dt)
        self.time_since_attack += dt

        if self.position != self.old_position:
            self.play_anim('walk')

        else:
            if self.current_anim != 'idle':
                self.play_anim('idle')

    def attack(self):
        if self.time_since_attack > self.weapon.frequency:
            self.weapon.attack()
            self.time_since_attack = 0

    def on_collision(self, other):
        super(Zombie, self).on_collision(other)
        if isinstance(other, Family):
            # zombies don't attach each other
            self.attack()

    def die(self):
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
        self.speed = 1000
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
##         if nx > 1000 or nx < -1000 or ny > 1000 or ny < -1000:
##             self.hit()
        if not self.player.game_layer.is_empty(*self.position):
            self.hit()

    def update_position(self, position):
        self.position = position

    def on_collision(self, other):
        #print 'BULLET DIED'
        #print self, self.position, other, other.position
        if self.player != other:
            self.hit()


    def hit(self):
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
