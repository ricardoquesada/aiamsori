
from cocos.director import director
from cocos.layer import Layer
from cocos.sprite import Sprite

from pyglet.window import key
import sound

class KeyGameCtrl(Layer):
    is_event_handler = True

    def __init__(self, game_layer):
        super(KeyGameCtrl, self).__init__()
        self.game_layer = game_layer


    def on_key_press(self, k, m):
        if k in [key.UP, key.W]:
            self.game_layer.player.acceleration= 1
            self.game_layer.player.play_anim('walk')

        if k in [key.DOWN, key.S]:
            self.game_layer.player.acceleration= -1
            self.game_layer.player.play_anim('walk')

        if k in [key.RIGHT, key.D]:
            self.game_layer.player.rotation_speed = 1

        if k in [key.LEFT, key.A]:
            self.game_layer.player.rotation_speed = -1

        if k == key.R:
            x, y = self.game_layer.player.position
            origin = (x, y)
            target = self.game_layer.player.target
            is_clear = self.game_layer.is_clear_path(origin, target)
            if not is_clear:
                print 'OBSTACLE'
            else:
                print 'FREE PATH'

        if k == key._1:
            self.game_layer.player.weapon = self.game_layer.player.weapons['fist']


        if k == key._2:
            self.game_layer.player.weapon = self.game_layer.player.weapons['shotgun']


        ## attack
        if k == key.SPACE:
            self.game_layer.player.attack()


    def on_key_release(self, k, m):
        if k in [key.UP, key.DOWN, key.W, key.S]:
            self.game_layer.player.acceleration = 0
            self.game_layer.player.speed = 0
            self.game_layer.player.play_anim('idle')

        if k in [key.LEFT, key.RIGHT, key.A, key.D]:
            self.game_layer.player.rotation_speed = 0

        


class MouseGameCtrl(Layer):
    is_event_handler = True

    def __init__(self, game_layer):
        super(MouseGameCtrl, self).__init__()
        self.game_layer = game_layer

    def on_mouse_motion(self, px, py, dx, dy):
        self.game_layer.player.look_at(px, py)

    def on_mouse_press(self, px, py, button, m):
        px = px - self.game_layer.x
        py = py - self.game_layer.y

        ## select a relative or set target for the one already selected
        if button == 4:
            if self.game_layer.player.selected_relative:
                self.game_layer.player.selected_relative.target = (px, py)
                self.game_layer.player.selected_relative = None

            else:
                for relative in self.game_layer.player.family.values():
                    x, y = relative.x, relative.y
                    mouse_over = (px-x)**2+(py-y)**2 < 100**2
                    if mouse_over:
                        self.game_layer.player.selected_relative = relative

        ## test for is empty, cambien el button cuando quieran(pero avisen)
        if button ==1:
            print '** is_empty:',self.game_layer.is_empty(px,py)
