import cocos
from cocos.actions import Delay, CallFunc
from cocos.director import director
from cocos.batch import BatchNode
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import Sprite
from cocos.actions import ScaleTo

class HudLayer(cocos.layer.Layer):
    def __init__(self, life=100, bullets=100):
        super(HudLayer, self).__init__()

        x, y = director.get_window_size()

        self.bullets_ico = face = Sprite('hud/bullets.png')
        self.bullets_ico.position = (
            self.bullets_ico.image.width/2,
            self.bullets_ico.image.height/2
        )

        self.bullets_label = cocos.text.Label(str(bullets),
            font_name='Times New Roman',
            font_size=32,
            x=self.bullets_ico.image.width+10,
            y=self.bullets_ico.image.height/2,
            anchor_x='left', anchor_y='center')
        self.add(self.bullets_ico)
        self.add(self.bullets_label)

        self.faces = {}
        space = 0
        self.face_scale = scale = 0.7
        for who in ["Dad", "Mom", "Zack", "Bee"]:
            sprite = Sprite('faces/%s.png'%who)
            self.faces[who] = sprite
            sprite.scale = scale
            sprite.position = (
                x-space-sprite.image.width*scale/2,
                sprite.image.height*scale/2
            )
            space += sprite.image.width*scale + 10

            self.add(sprite)

    def set_life(self, who, life):
        pic = self.faces[who]
        pic.opacity = life/100.0 * 255
        pic.stop()

        pic.do( ScaleTo(self.face_scale*0.8, 0.2) + ScaleTo(self.face_scale, 0.2))

    def set_bullets(self, bullets):
        self.bullets_label.element.text = str(bullets)
