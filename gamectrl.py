import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gamelib/'))

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

    def on_key_press(self, k, m):
        if k == key.UP:
            print "UP"
##             game.player_char.position


class DummyGame(ColorLayer):

    def __init__(self, r, g, b, a):
        super(DummyGame, self).__init__(r,g,b,a)
        self.player_char = Sprite('data/img/tipito.png')
        self.player_char.position = (100,100)

        self.add(self.player_char)
        

if __name__ == "__main__":

    director.init(width=800, height=600, fullscreen=False )


    dummy_game =  Scene(DummyGame(200,100,100,255))
    dummy_game.add(GameCtrl(dummy_game))
    director.run(dummy_game)

