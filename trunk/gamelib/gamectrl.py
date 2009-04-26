
from cocos.director import director
from cocos.layer import Layer
from cocos.sprite import Sprite

from pyglet.window import key


class GameCtrl(Layer):
    is_event_handler = True

    def __init__(self, game_layer):
        super(GameCtrl, self).__init__()
        self.game_layer = game_layer
        
#        self.pressed_keys = key.KeyStateHandler()
#        director.window.push_handlers(self.pressed_keys)        

    def on_key_press(self, k, m):


        if k in [key.UP, key.W]:
            self.game_layer.player.acceleration= 2

        if k in [key.DOWN, key.S]:
            self.game_layer.player.acceleration= -2

        if k in [key.RIGHT, key.D]:
            pass
                
        if k in [key.RIGHT, key.A]:
            pass


    def on_key_release(self, k, m):
        if k in [key.UP, key.DOWN, key.W, key.S]:
            self.game_layer.player.acceleration = 0
            self.game_layer.player.speed = 0

    def on_mouse_motion(self, px, py, dx, dy):
        self.game_layer.player.look_at(px, py)
            

