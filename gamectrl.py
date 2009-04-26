import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gamelib/'))

from math import cos, radians, sin, degrees, atan, atan2, pi, sqrt
from cocos.director import director
from cocos.scene import Scene
from cocos.layer import Layer, ColorLayer
from cocos.sprite import Sprite

from pyglet.window import key


class GameCtrl(Layer):
    is_event_handler = True

    def __init__(self, game):
        super(GameCtrl, self).__init__()
        self.game = game
        
        self.pressed_keys = key.KeyStateHandler()
        director.window.push_handlers(self.pressed_keys)        

    def on_key_press(self, k, m):


        if k in [key.UP, key.W]:
#            print self.pressed_keys
            print self.game.player.speed
            self.game.player.speed = 300
            print self.game.player.speed

##             if self.game.player.speed < 300:
##                 print self.game.player.speed
##                 self.game.player.speed += 10

        if k in [key.DOWN, key.S]:
            self.game.player.speed = -300

        if k in [key.RIGHT, key.D]:
            pass
                
        if k in [key.RIGHT, key.A]:
            pass


    def on_key_release(self, k, m):
        if k in [key.UP, key.DOWN, key.W, key.S]:
            print "release"
            self.game.player.speed = 0

    def on_mouse_motion(self, px, py, dx, dy):
        pl_x, pl_y = self.game.player.position[0],\
                     self.game.player.position[1]
        
        angle =  -(atan2(py - pl_y, px - pl_x) / pi * 180)

        self.game.player.rotation = angle
            

class Char(Sprite):

    def __init__(self, img):
        super(Char, self).__init__(img)
        self.speed = 0
        self.schedule(self.update)

    def update(self, dt):
        b = self
        a = -b.rotation
        b.x = (b.x + cos( radians(a) ) * b.speed * dt)
        b.y = (b.y + sin( radians(a) ) * b.speed * dt)
    

class DummyGame(ColorLayer):

    def __init__(self, r, g, b, a):
        super(DummyGame, self).__init__(r,g,b,a)
        self.player = Char('data/img/tipito.png')
        self.player.position = (100,100)
        self.player.speed = 0

        self.add(self.player)
        


if __name__ == "__main__":

    director.init(width=800, height=600, fullscreen=False )


    game_layer = DummyGame(200,100,100,255)
    dummy_game =  Scene(game_layer)
    dummy_game.add(GameCtrl(game_layer))
    
    director.run(dummy_game)

