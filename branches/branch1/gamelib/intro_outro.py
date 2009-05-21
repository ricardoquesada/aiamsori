from cocos.director import director
from cocos.layer.base_layers import Layer
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.actions import Delay, CallFunc, FadeTo, FadeOut, Show, Hide, FadeIn, FadeOut
from cocos.text import Label
from cocos.sprite import Sprite

import sound
import gg

class ImageLayer(Layer):
    is_event_handler = True

    def __init__(self, size=None):
        super(ImageLayer, self).__init__()
        if size == None:
            size = director.get_window_size()
        self.w = size[0]
        self.h = size[1]
        self.state = "intro"

        grossini = Sprite('data/img/grossini.png')
        mom = Sprite('data/img/Mom.png')
        bee = Sprite('data/img/Bee.png')
        zack = Sprite('data/img/Zack.png')
        dad = Sprite('data/img/Dad.png')
        sprites = [grossini, mom, bee, zack, dad]
        for s in sprites:
            self.add(s)
            s.position = self.w / 2, self.h / 2
            s.do(Hide())

        # grossini abajo a la izquierda
        grossini.position = self.w - grossini.image.width, grossini.image.height
        #texts = ['aiamsori productions presents...', '', '', '', '','and the neighbours','', 'in',]
        texts = ['productions.png'] + ['none.png'] * 4 + ['neigs.png', 'none.png', 'in.png']
        labels = []
        for t in texts:
#            l = Sprite(os.path.join('data', 'img', t)) # not found in win
            l = Sprite('/'.join(['data', 'img', t]))
            l.position = self.w / 2, self.h / 2
            labels.append(l)
            self.add(l, z=1)
            l.do(Hide())

        delay = 1
        ft = 1
        for l in labels:
            l.do(Delay(delay) + Show() + FadeIn(ft) + Delay(1) + FadeOut(ft))
            delay += 3

        delay = 1
        for s in sprites:
            s.do(Delay(delay) + Show() + FadeIn(ft) + Delay(1) + FadeOut(ft))
            delay += 3

        delay += 3
        zombies = []
        for zf in [
                'img/Punkie zombie.png',
                'img/Afro zombie.png',
                'img/Fat zombie byn.png',
                'img/Bitch zombie.png',
                ]:
            s = Sprite(zf)
            self.add(s)
            s.position = self.w / 2, self.h / 2
            s.do(Hide())
            zombies.append(s)

        for s in zombies:
            s.do(Delay(delay) + Show() + FadeIn(0.3) + Delay(0.3) + FadeOut(0.3))
            delay += 0.7

        self.borrar = labels + sprites
        self.do(Delay(delay+3) + CallFunc(lambda: self.goto_title()))
        sound.play_music("intro_music")

#    def on_key_press(self, k, m):
    def goto_title(self):
        self.state = "title"
        [self.remove(h) for h in self.borrar]
        x,y = self.w, self.h
##        labelkey = Label('press any key to start', font_name='Times New Roman', font_size=28, bold=True, anchor_x='center')
##         labelkey.position = self.w / 2  , 150
##         labelkey.element.color = 0,0,0,180
##         self.add(labelkey, z=1)
##         labelkey.do(Hide())

        bg = Sprite('data/img/ppl.png')
        self.add(bg)
        bg._vertex_list.vertices = [0,0,x,0,x,y,0,y]
#        labelkey.do(Delay(5) + Show() + FadeIn(2))
        self.do(Delay(4) + CallFunc(lambda: self.goto_game()))


    def on_key_press( self, symbol, modifiers ):
        if symbol == pyglet.window.key.ESCAPE:
            if self.state == "intro":
                self.goto_title()
            if self.state == "title":
                self.goto_game()

            return True

    def goto_game(self):
        sound.stop_music()
        game_scene = gg.services["s_get_game_scene"]()
        director.replace(game_scene)


class GameOverLayer(Layer):
    is_event_handler = True

    def __init__(self):
        super(GameOverLayer, self).__init__()
        w, h = director.get_window_size()
        label = Label("You've lasted  %ds..." % director.return_value, font_name='youmurdererbb_reg', font_size=42, bold=True)
        label.position = w / 2 - 340 , h / 2 + 100
#        label.element.color = 40,179,75,180
        label.element.color = 255,255,255,255
        label2 = Label('do you want to play again?', font_name='youmurderer', font_size=42, bold=True)
        label2.position = w / 2 - 420 , h / 2
        label2.element.color = 40,179,75,180
        label3 = Label('(Y/N)', font_name='youmurdererbb', font_size=52, bold=True)
        label3.position = w / 2 - 40, h / 2 - 100
        label3.element.color = 40,179,75,180
        self.add(label, z=1)
        #label.do(Hide() + Delay(10) + Show())
        label2.do(Delay(10) + Show())
        label3.do(Delay(10) + Show())
        self.add(label)
        self.add(label2)
        self.add(label3)
        sound.play("MusicEnd")

    def on_key_press(self, k, m):
        from pyglet.window import key
        sound.stop_music()
        if k == key.Y:
            game_scene = gg.services["s_get_game_scene"]()
            director.replace(game_scene)
            return True
        elif k == key.N:
            director.pop()
            return True

# services
def get_intro_scene():
    image_layer = ImageLayer()
    scene = Scene()
    scene.add(image_layer)
    return scene

def get_end_scene():
    scene = Scene()
    scene.add(GameOverLayer())
    return scene


# publish services
gg.services["s_get_intro_scene"] = get_intro_scene
gg.services["s_get_end_scene"] = get_end_scene
    
