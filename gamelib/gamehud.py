import cocos
from cocos.actions import Delay, CallFunc
from cocos.director import director
from cocos.batch import BatchNode
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import NotifierSprite, Sprite

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

        self.life_ico = face = Sprite('hud/life.png')
        self.life_ico.position = (
            x-self.life_ico.image.width/2,
            self.life_ico.image.height/2
        )

        self.life_label = cocos.text.Label(str(life),
            font_name='Times New Roman',
            font_size=32,
            x=x-self.life_ico.image.width-10,
            y=self.life_ico.image.height/2,
            anchor_x='right', anchor_y='center')
        self.add(self.life_ico)
        self.add(self.life_label)

    def set_life(self, life):
        self.life_label.element.text = str(life)

    def set_bullets(self, bullets):
        self.bullets_label.element.text = str(bullets)
