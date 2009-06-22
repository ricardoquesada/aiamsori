from tiless_editor.plugin import LayerFactory, Plugin
from tiless_editor.picker import PickerBatchNode
from cocos.sprite import NotifierSprite
import pyglet
from pyglet import gl
from tiless_editor.atlas import TextureAtlas, SavedAtlas

class SpriteLayerFactory(LayerFactory):
    def __init__(self, tiles_path):
        self.tiles_path = tiles_path

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
        source_atlas = SavedAtlas('atlas-fixed.png', 'atlas-coords.json')
        def build_sprite(img):

            sp = source_atlas[img['filename']]
            s = NotifierSprite(sp,
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

        for item in in_dict["sprites"]:
#            fix_region( item, newatlas )
            sprite = build_sprite(item)
            layer.add(sprite)


        return layer

class SpriteLayerPlugin(Plugin):
    name = 'sprite_layer'

    def __init__(self, editor):
        self.ed = editor
        self.factory = SpriteLayerFactory(editor.tilesdir)
        editor.register_layer_factory("sprite", self.factory)
