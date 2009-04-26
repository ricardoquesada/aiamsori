
from cocos.director import director
from cocos.layer import Layer
from cocos.sprite import Sprite

from pyglet.window import key


class GameCtrl(Layer):
    is_event_handler = True

    def __init__(self, main_layer):
        super(GameCtrl, self).__init__()
        self.main_layer = main_layer
        
        self.pressed_keys = key.KeyStateHandler()
        director.window.push_handlers(self.pressed_keys)        

    def on_key_press(self, k, m):


        if k in [key.UP, key.W]:
#            print self.pressed_keys
            print self.main_layer.player.speed
            self.main_layer.player.speed = 300
            print self.main_layer.player.speed

##             if self.main_layer.player.speed < 300:
##                 print self.main_layer.player.speed
##                 self.main_layer.player.speed += 10

        if k in [key.DOWN, key.S]:
            self.main_layer.player.speed = -300

        if k in [key.RIGHT, key.D]:
            pass
                
        if k in [key.RIGHT, key.A]:
            pass


    def on_key_release(self, k, m):
        if k in [key.UP, key.DOWN, key.W, key.S]:
            print "release"
            self.main_layer.player.speed = 0

    def on_mouse_motion(self, px, py, dx, dy):
        self.main_layer.player.look_at(px, py)
            

