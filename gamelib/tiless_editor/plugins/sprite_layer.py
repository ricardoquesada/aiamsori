from tiless_editor.plugin import LayerFactory, Plugin
from tiless_editor.picker import PickerBatchNode
from cocos.sprite import NotifierSprite
import pyglet
from pyglet import gl
from tiless_editor.atlas import TextureAtlas

class SpriteLayerFactory(LayerFactory):
    def __init__(self, tiles_path):
        pass#self.atlas = TextureAtlas(tiles_path)

    def get_new_layer(self):
        layer = PickerBatchNode()
        layer.layer_type = "sprite"
        return layer

    def layer_to_dict(self, layer):
        sprites = []
        for i, c in layer.children:
            label = getattr(c, "label", None)
            sprites.append(dict(position=c.position,
                                 scale=c.scale,
                                 rotation=c.rotation,
                                 opacity=c.opacity,
                                 filename=c.path,
                                 label=label,
                                 z=0,
                                 rect=c.rect,
                                 ))
        return dict(sprites=sprites)

    def dict_to_layer(self, in_dict):
        def build_sprite(img, texture=None):

            rect = img['rect']
            region = pyglet.image.TextureRegion( rect[0], rect[1], 0, rect[2], rect[3], texture )
            s = NotifierSprite(region,
                       img['position'], img['rotation'], img['scale'], img['opacity'])
#            s = NotifierSprite(str(img['filename']),
#                       img['position'], img['rotation'], img['scale'], img['opacity'])
            s.label = img['label'] if "label" in img else None
            s.path = img['filename']
            s.rect = img['rect']
            return s

        def fix_region( item , newatlas ):
            for sprite in newatlas.sprites:
                if item['filename'] == sprite.path:
                    item['rect'] = sprite.rect


        layer = self.get_new_layer()

        image = pyglet.image.load( 'atlas.png')
        atlas = pyglet.image.atlas.TextureAtlas( image.width, image.height )
        atlas.texture = image.texture
        gl.glTexParameteri( image.texture.target, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE )
        gl.glTexParameteri( image.texture.target, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE )


        newatlas = TextureAtlas('tiles')
        newatlas.fix_image()

        for item in in_dict["sprites"]:
#            fix_region( item, newatlas )
            sprite = build_sprite(item, atlas.texture)
            layer.add(sprite)


        return layer

class SpriteLayerPlugin(Plugin):
    name = 'sprite_layer'

    def __init__(self, editor):
        self.ed = editor
        self.factory = SpriteLayerFactory(editor.tilesdir)
        editor.register_layer_factory("sprite", self.factory)
