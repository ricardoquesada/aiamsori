# ----------------------------------------------------------------------------
# cocos2d
# ----------------------------------------------------------------------------
'''
TilessLayer
'''

__docformat__ = 'restructuredtext'

# This code is so you can run the samples without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# cocos2d
import cocos
from cocos.cocosnode import *
from cocos.director import director
from cocos.actions import Accelerate, Rotate
from cocos.sprite import Sprite

# pyglet
import pyglet
from pyglet import gl
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
    def __init__(self, textures, basename=""):
        x=256
        y=256

        self.sprites = []
        self.regions = []

        self.atlas_image_name = 'atlas.png'
        if basename:
            basename += "-"
        self.basename = basename

        voids = []
        if isinstance(textures, str):
            out = []
            for filename in os.listdir(textures):
                if os.path.splitext(filename)[1] in ['.jpg', '.jpeg', '.png']:
                    path = os.path.join(textures, filename)
                    # FIXME: Hack for paths working on windows:
                    path = path.replace("\\", "/")
                    out.append(path)
            textures = out
        for path in textures:


                img = pyglet.image.load(path)
                void = _Void()
                void.path = path
                void.img = img

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
            self.sprites.append( sprite )
            sprite.path = voids[i].path
            sprite.rect = [region.x, region.y, region.width, region.height]


        self.texture = atlas.texture
        atlas.texture.save( self.basename +  self.atlas_image_name )


    def fix_image(self):

        im = Image.open( self.basename  +self.atlas_image_name )
        size = im.size
        for region in self.regions:
            rect = [ region.x, (size[1] - region.y) - region.height, region.width, region.height ]

            # left / bottom borders don't need painting
            for x in range( rect[0]-1, rect[0] + rect[2] ):

                y = rect[1]
                if x > 0 and x < size[0] and y >= 0 and y < size[1]:
                    pixel = im.getpixel( (x,y) )
                    im.putpixel( (x,y-1), pixel )

                y = rect[1] + rect[3] - 1
                if x > 0 and x < size[0] and y >= 0 and y < (size[1]-1):
                    pixel = im.getpixel( (x,y) )
                    im.putpixel( (x,y+1), pixel )

            # left / bottom borders don't need painting
            for y in range( rect[1], rect[1] + rect[3] ):

                x = rect[0]
                if x > 0 and x < size[0] and y >= 0 and y < size[1]:
                    pixel = im.getpixel( (x,y) )
                    im.putpixel( (x-1,y), pixel )

                x = rect[0] + rect[2] - 1
                if x > 0 and x < size[0] and y >= 0 and y < (size[1]-1):
                    pixel = im.getpixel( (x,y) )
                    im.putpixel( (x+1,y), pixel )

        im.save(self.basename + "atlas-fixed.png", "PNG")
        self.output_coords()

    def output_coords( self ):
        im = Image.open( self.basename + self.atlas_image_name )
        fp = open(self.basename + 'atlas-coords.json','w')
        size = im.size
        coords = []
        d = {}
        for sprite in self.sprites:
            d[sprite.path] = sprite.rect

        simplejson.dump(d,fp, indent=4)
        fp.close()

class SavedAtlas(object):
    def __init__(self, atlas_img, coords_file):
        img = pyglet.image.load(  atlas_img )
        self.atlas = pyglet.image.atlas.TextureAtlas( img.width, img.height )
        self.atlas.texture = img.texture
        gl.glTexParameteri( img.texture.target, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE )
        gl.glTexParameteri( img.texture.target, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE )
        self.map = dict([
            (k, pyglet.image.TextureRegion( rect[0], rect[1], 0, rect[2], rect[3], self.atlas.texture ))
            for k, rect in simplejson.load(open(coords_file)).items()])

    def __getitem__(self, key):
        region = self.map[key]
        return region

if __name__ == "__main__":
    director.init()
    tex = TextureAtlas( 'tiles/set4')
    tex.fix_image()
    tex.output_coords()
