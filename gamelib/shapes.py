from tiless_editor.layers.collision import Segment, Circle, Square

COLLISION_LAYER_AGENT = 1
COLLISION_LAYER_ZOMBIE = 2
COLLISION_LAYER_WALL = 4
COLLISION_LAYER_RAY = 8
COLLISION_LAYER_BULLET = 16

COLLISION_GROUP_AGENT = 1
COLLISION_GROUP_ZOMBIE = 2

BULLET_RADIUS = 10
BULLET_DAMAGE_ENERGY = 10


class AgentShape(Circle):
    def __init__(self, sprite):
        radius = 0.5 * max(sprite.width, sprite.height) * sprite.scale
        super(AgentShape, self).__init__(radius, position=sprite.position)
        self.sprite = sprite
        self.static = False
        self.layers = COLLISION_LAYER_AGENT | COLLISION_LAYER_ZOMBIE | COLLISION_LAYER_WALL | COLLISION_LAYER_BULLET


class ZombieShape(Circle): 
    def __init__(self, sprite):
        radius = 0.5 * max(sprite.width, sprite.height) * sprite.scale
        super(ZombieShape, self).__init__(radius, position=sprite.position)
        self.sprite = sprite
        self.static = False
        self.layers = COLLISION_LAYER_AGENT | COLLISION_LAYER_ZOMBIE | COLLISION_LAYER_WALL | COLLISION_LAYER_BULLET


class Wall(Square):
    def __init__(self, sprite):
        super(Wall, self).__init__(sprite.width, sprite.height, position=sprite.position)
        self.sprite = sprite
        self.static = True
        self.layers = COLLISION_LAYER_AGENT | COLLISION_LAYER_ZOMBIE | COLLISION_LAYER_WALL | COLLISION_LAYER_RAY | COLLISION_LAYER_BULLET


class Ray(Segment):
    def __init__(self, radius, origin, target):
        super(Ray, self).__init__(radius, origin=origin, target=target)
        self.sprite = sprite
        self.static = False
        #self.layers = COLLISION_LAYER_WALL | COLLISION_LAYER_RAY


class Bullet(Segment):
    def __init__(self, origin, target):
        super(Bullet, self).__init__(BULLET_RADIUS, origin=origin, target=target)
        self.sprite = sprite
        self.static = False
        #self.layers = COLLISION_LAYER_AGENT | COLLISION_LAYER_ZOMBIE | COLLISION_LAYER_WALL | COLLISION_LAYER_BULLET
        self.damage_energy = BULLET_DAMAGE_ENERGY

