
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

##         if k in [key.RIGHT, key.D]:
##             self.game_layer.player.strafe_speed = 1

##         if k in [key.LEFT, key.A]:
##             self.game_layer.player.strafe_speed = -1

        if k == key.R:
            x, y = self.game_layer.player.position
            origin = (x, y)
            target = self.game_layer.player.target
            is_clear = self.game_layer.is_clear_path(origin, target)
            if not is_clear:
                pass
#                print 'OBSTACLE'
            else:
                pass
#                print 'FREE PATH'

        if k == key._1:
            self.game_layer.player.switch_weapon('fist')
#            self.game_layer.player.weapon = self.game_layer.player.weapons['fist']


        if k == key._2:
            self.game_layer.player.switch_weapon('shotgun')
#            self.game_layer.player.weapon = self.game_layer.player.weapons['shotgun']


        ## attack
        if k == key.SPACE:
            self.game_layer.player.attack()


    def on_key_release(self, k, m):
        if k in [key.UP, key.DOWN, key.W, key.S]:
            self.game_layer.player.acceleration = 0
            self.game_layer.player.speed = 0
            self.game_layer.player.play_anim('idle')
        if k in [key.LEFT, key.A]:
            if self.game_layer.player.rotation_speed == -1:
                self.game_layer.player.rotation_speed = 0
        if k in [key.RIGHT, key.A, key.D]:
            if self.game_layer.player.rotation_speed == 1:
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
        if button == 1:
            hud = self.game_layer.hud
            current_selected_relative = self.game_layer.player.selected_relative
            new_selected_relative = self._get_hud_face(px, py, hud)
            print new_selected_relative, current_selected_relative
            if current_selected_relative is not None:
                if new_selected_relative is not None:
                    self.game_layer.player.selected_relative = None
                    hud.faces[current_selected_relative.name].color = (255, 255, 255)
                    if new_selected_relative != current_selected_relative:
                        self.game_layer.player.selected_relative = new_selected_relative
                        hud.faces[new_selected_relative.name].color = (0,172, 0)
                else:
                    self.game_layer.player.selected_relative.target = (px, py)
                    #self.game_layer.player.selected_relative = None
            else:
                if new_selected_relative is not None:
                    self.game_layer.player.selected_relative = new_selected_relative
                    hud.faces[new_selected_relative.name].color = (0,172, 0)
                #for relative in self.game_layer.player.family.values():
                #    x, y = relative.x, relative.y
                #    mouse_over = (px-x)**2+(py-y)**2 < 100**2
                #    if mouse_over:
                #        self.game_layer.player.selected_relative = relative

        ## test for is empty, cambien el button cuando quieran(pero avisen)
        ## te aviso: lo cambie :P
        if button == 4:
            print '** is_empty:',self.game_layer.is_empty(px,py)

    def _get_hud_face(self, px, py, hud):
        for relative in self.game_layer.player.family.values():
            # test for mouse over on the relative
            x, y = relative.x, relative.y
            mouse_over = (px-x)**2+(py-y)**2 < 100**2
            if mouse_over:
                #self.game_layer.player.selected_relative = relative
                return relative

            # test for mouse over on the faces
            face = hud.faces[relative.name]
            x, y = face.position
            print x, y, px, py
            mouse_over = (px-x)**2+(py-y)**2 < 100**2
            if mouse_over:
                return relative
            

