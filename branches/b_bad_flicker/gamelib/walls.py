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
from cocos.sprite import Sprite

from tiless_editor.plugins.sprite_layer import SpriteLayerFactory
#from tiless_editor.layers.collision import CollisionLayer
from tiless_editor.tiless_editor import LayersNode
from tiless_editor.atlas import SavedAtlas

from pyglet.image.atlas import Allocator

# python
import os
import simplejson
import Image



class WallLayer(cocos.cocosnode.CocosNode):
    def __init__(self):
        super(WallLayer, self).__init__()
        self.top_batch = pyglet.graphics.Batch()
        self.wall_batch = pyglet.graphics.Batch()
        self.top_to_wall = {}
        self.walls_atlas = SavedAtlas('data/walls-atlas-fixed.png', 'data/walls-atlas-coords.json')

    def add(self, source_sprite):
        sprite = source_sprite
        wall_sprite = self.get_wall(source_sprite)
        wd = sprite.image.width/2
        hd = sprite.image.height/2
        wh = 50
        x, y = source_sprite.position
        x = int(x)
        y = int(y)
        l = (x-wd, y-hd, wh, x+wd, y-hd, wh, x+wd, y+hd, wh, x-wd, y+hd, wh)
        #l = (x-wd, y-hd, x+wd, y-hd, x+wd, y+hd, x-wd, y+hd)
        color = [128, 128, 128]
        vertex_list = self.top_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', color*4),
            ('t3f', sprite.image.tex_coords)
        )

        #top wall
        l = (x-wd, y-hd, 0, x+wd, y-hd, 0, x+wd, y-hd, wh, x-wd, y-hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', color*4),
            ('t3f', wall_sprite.tex_coords)
        )
        #bottom wall
        l = (x-wd, y+hd, 0, x+wd, y+hd, 0, x+wd, y+hd, wh, x-wd, y+hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', color*4),
            ('t3f', wall_sprite.tex_coords)
        )
        #left wall
        l = (x-wd, y+hd, 0, x-wd, y-hd, 0, x-wd, y-hd, wh, x-wd, y+hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', color*4),
            ('t3f', wall_sprite.tex_coords)
        )
        #right wall
        l = (x+wd, y+hd, 0, x+wd, y-hd, 0, x+wd, y-hd, wh, x+wd, y+hd, wh)
        vertex_list = self.wall_batch.add(4, pyglet.gl.GL_QUADS, None,
            ('v3i', l),
            ('c3B', color*4),
            ('t3f', wall_sprite.tex_coords)
        )
        self.texture = sprite.image.texture

    def draw(self):
        pyglet.gl.glPushMatrix()
        self.transform()
        texture = self.walls_atlas.atlas.texture
        pyglet.gl.glEnable(texture.target)
        pyglet.gl.glBindTexture(texture.target, texture.id)
        self.wall_batch.draw()
        pyglet.gl.glDisable(texture.target)
        texture = self.texture
        pyglet.gl.glEnable(texture.target)
        pyglet.gl.glBindTexture(texture.target, texture.id)
        self.top_batch.draw()
        pyglet.gl.glDisable(texture.target)

        pyglet.gl.glPopMatrix()

    def get_wall(self, child):
        path = conf_walls[child.path]
        s = self.walls_atlas[path]
        return s

def create_wall_layer(layers):
    dest = WallLayer()
    for layer in layers:
        for z, child in layer.children:
            dest.add(child)

    return dest

# si cambian esto, tienen que ejecutar este archivo para que arregle el atlas y la lista de coordenadas
conf_walls =  {'newtiles/pared.png':'walls/pared_v.png',
                'newtiles/ventana.png':'walls/ventana_v.png',
                'newtiles/alambre.png':'walls/alambre_v.png',
                'newtiles/alambre_rot.png':'walls/alambre_v.png',
            }
if __name__ == "__main__":
    from tiless_editor.atlas import TextureAtlas
    director.init()
    atlas = TextureAtlas(conf_walls.values(), basename='walls')
    atlas.fix_image()
