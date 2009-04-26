import os.path
import pyglet
import simplejson
import sys
import random
import geom

from math import cos, sin, radians, degrees, atan, atan2, pi, sqrt

import cocos
from cocos.director import director
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import NotifierSprite, Sprite

from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
from tiless_editor.layers.collision import CollisionLayer
from tiless_editor.tiless_editor import LayersNode

from pyglet.image.atlas import Allocator

# python
import os
import simplejson
import Image


# How many pixels left as border
PIXEL_BORDER = 1

class MyAllocator(Allocator):

    def alloc(self, width, height):

        # create an Atlas with 1 pixel of border
        width +=  PIXEL_BORDER + 1
        height += PIXEL_BORDER + 1
        return super(MyAllocator,self).alloc(width, height)

class _Void(object):
    pass

class TextureAtlas(object):
    def __init__(self):
        self.source_images = {}

    def build(self):
        x=256
        y=256

        self.sprites = {}
        self.regions = []

        voids = []

        for path, img in self.source_images.items():
                void = _Void()
                void.img = img.image_data
                void.path = path
                voids.append( void )

        # order by height (decrese) to improve chances
        voids = sorted(voids, key=lambda i: i.img.height, reverse=True)

        while True:
            try:
                print 'trying with atlas: %d, %d' % (x,y)
                atlas = pyglet.image.atlas.TextureAtlas(x,y)
                atlas.allocator = MyAllocator(x,y)
                for void in voids:
                    self.regions.append( atlas.add( void.img) )
                break

            except pyglet.image.atlas.AllocatorException, e:
                print str(e)
                x += 256
                y += 256
                self.regions = []


        for i in range( len (self.regions) ):
            region = self.regions[i]
            sprite = Sprite( region )
            self.sprites[ voids[i].path ] = sprite
            sprite.rect = [region.x, region.y, region.width, region.height]

        self.texture = atlas.texture



class WallLayer(cocos.cocosnode.CocosNode):
    def __init__(self):
        super(WallLayer, self).__init__()
        self.top_batch = pyglet.graphics.Batch()
        self.wall_batch = pyglet.graphics.Batch()
        self.atlas = TextureAtlas()
        self.top_to_wall = {}

    def add_source(self, sprite, wall):
        self.atlas.source_images[sprite.path] = sprite.image
        self.atlas.source_images[wall.path] = wall.image
        self.top_to_wall[sprite.path] = wall.path

    def make(self):
        self.atlas.build()

    def add(self, source_sprite):
        sprite = self.atlas.sprites[source_sprite.path]
        wall_sprite = self.atlas.sprites[
            self.top_to_wall[source_sprite.path]
        ]
        wd = sprite.image.width/2
        hd = sprite.image.height/2
        wh = 50
        x, y = source_sprite.position
        x = int(x)
        y = int(y)
        l = (x-wd, y-hd, wh, x+wd, y-hd, wh, x+wd, y+hd, wh, x-wd, y+hd, wh)
        #l = (x-wd, y-hd, x+wd, y-hd, x+wd, y+hd, x-wd, y+hd)
        vertex_list = self.top_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', [255, 255, 255]*4),
            ('t3f', sprite.image.tex_coords)
        )

        #top wall
        l = (x-wd, y-hd, 0, x+wd, y-hd, 0, x+wd, y-hd, wh, x-wd, y-hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', [255, 255, 255]*4),
            ('t3f', wall_sprite.image.tex_coords)
        )
        #bottom wall
        l = (x-wd, y+hd, 0, x+wd, y+hd, 0, x+wd, y+hd, wh, x-wd, y+hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', [255, 255, 255]*4),
            ('t3f', wall_sprite.image.tex_coords)
        )
        #left wall
        l = (x-wd, y+hd, 0, x-wd, y-hd, 0, x-wd, y-hd, wh, x-wd, y+hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', [255, 255, 255]*4),
            ('t3f', wall_sprite.image.tex_coords)
        )
        #right wall
        l = (x+wd, y+hd, 0, x+wd, y-hd, 0, x+wd, y-hd, wh, x+wd, y+hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', [255, 255, 255]*4),
            ('t3f', wall_sprite.image.tex_coords)
        )
        self.texture = sprite.image.texture

    def draw(self):
        pyglet.gl.glPushMatrix()
        self.transform()
        texture = self.texture
        pyglet.gl.glEnable(texture.target)
        pyglet.gl.glBindTexture(texture.target, texture.id)
        self.wall_batch.draw()
        self.top_batch.draw()
        pyglet.gl.glDisable(texture.target)

        pyglet.gl.glPopMatrix()

def get_wall(child):
    path = {'tiles/pared.jpg':'tiles/pared.jpg',
            'tiles/ventana_rot.png':'tiles/ventana_v.png',
            'tiles/ventana.png':'tiles/ventana_v.png',
        }[child.path]
    s = Sprite(path)
    s.path = path
    return s

def create_wall_layer(layers):
    dest = WallLayer()
    for layer in layers:
        for z, child in layer.children:
            print child.path
            dest.add_source(child, get_wall(child))
    dest.make()
    for layer in layers:
        for z, child in layer.children:
            dest.add(child)

    return dest
