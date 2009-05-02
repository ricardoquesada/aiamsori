from tiless_editor.layers.collision import Segment, Circle, Square

COLLISION_LAYER_AGENT = 1
COLLISION_LAYER_ZOMBIE = 2
COLLISION_LAYER_WALL = 4
COLLISION_LAYER_RAY = 8
COLLISION_LAYER_BULLET = 16

COLLISION_GROUP_AGENT = 1
COLLISION_GROUP_ZOMBIE = 2

# bullet shape radius is a little smaller than the agent/zombie body so as to
# hit almost everywhere on the body
BULLET_RADIUS = 30
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


class WallShape(Square):
    def __init__(self, sprite):
        super(WallShape, self).__init__(sprite.width, sprite.height, position=sprite.position)
        self.sprite = sprite
        self.static = True
        #self.layers = COLLISION_LAYER_AGENT | COLLISION_LAYER_ZOMBIE | COLLISION_LAYER_WALL | COLLISION_LAYER_RAY | COLLISION_LAYER_BULLET
        self.layers = COLLISION_LAYER_AGENT | COLLISION_LAYER_RAY | COLLISION_LAYER_BULLET


class RayShape(Segment):
    def __init__(self, radius, origin, target):
        super(Ray, self).__init__(radius, origin=origin, target=target)
        self.sprite = sprite
        self.static = False
        #self.layers = COLLISION_LAYER_WALL | COLLISION_LAYER_RAY


class BulletShape(Segment):
    def __init__(self, sprite, origin, target):
        super(BulletShape, self).__init__(BULLET_RADIUS, origin=origin, target=target, scale=sprite.scale, rotation=sprite.rotation)
        self.sprite = sprite
        self.static = False
        #self.layers = COLLISION_LAYER_AGENT | COLLISION_LAYER_ZOMBIE | COLLISION_LAYER_WALL | COLLISION_LAYER_BULLET
        self.layers = COLLISION_LAYER_ZOMBIE
        self.damage_energy = BULLET_DAMAGE_ENERGY

    # README: uncomment this to debug collision shape
    #def draw(self):
    #    return
    #    import pyglet
    #    from pymunk.vec2d import Vec2d
    #    batch = pyglet.graphics.Batch()
    #    v1 = Vec2d(0, -self.radius)
    #    #v1.rotate(-self.sprite.rotation)
    #    v2 = Vec2d(0, self.radius)
    #    #v2.rotate(-self.sprite.rotation)
    #    rotation = self.rotation
    #    origin_1 = self.a + v1.rotated(-rotation)
    #    origin_2 = self.a + v2.rotated(-rotation)
    #    target_1 = self.b + v2.rotated(-rotation)
    #    target_2 = self.b + v1.rotated(-rotation)
    #    collision_layer = self.sprite.parent
    #    points = [origin_1[0], origin_1[1], origin_2[0], origin_2[1], target_1[0], target_1[1], target_2[0], target_2[1]]
    #    batch.add(4, pyglet.gl.GL_LINE_LOOP, None,
    #            ('v2f', points),
    #            ('c3B', [255,255,255]*4))
    #    batch.draw()
