import cocos
from cocos.actions import Delay, CallFunc
from cocos.director import director
from cocos.batch import BatchNode
from cocos.scene import Scene
from cocos.layer.base_layers import Layer
from cocos.sprite import Sprite

class TalkLayer(cocos.layer.Layer):
    def __init__(self):
        super(TalkLayer, self).__init__()
        self.talking = []

    def talk(self, who, message, duration=5, transient=True):
        # transient messages get discarded if we are talking
        # non transient messages are queued.
        if transient and self.talking:
                return
        if self.talking:
            self.talking.append((who, message, duration))
        else:
            self.talking.append((who, message, duration))
            self.update_talk()

    def end_talking(self):
        self.talking = self.talking[1:]
        ch = list(self.get_children())
        for c in ch:
            self.remove(c)
        self.update_talk()

    def update_talk(self):
        if not self.talking:
            return
        who, text, duration = self.talking[0]
        x, y = director.get_window_size()

        face = Sprite('faces/%s.png'%who)
        self.add(face)
        face.position = face.image.width*face.scale/2, y - face.image.height * face.scale/2

        balloon_l = Sprite('faces/balloon-left.png', opacity=127)
        balloon_r = Sprite('faces/balloon-right.png', opacity=127)
        balloon_c = Sprite('faces/balloon-center.png', opacity=127)

        self.add(balloon_l)
        self.add(balloon_c)
        self.add(balloon_r)

        x1 = face.image.width*face.scale
        y1 = y - face.image.height * face.scale
        x2 = x1+balloon_l.image.width
        y2 = y-3
        balloon_l._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]

        x1 = x-5-balloon_r.image.width
        y1 = y1
        x2 = x-5
        y2 = y-3
        balloon_r._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]

        x1 = face.image.width*face.scale+balloon_l.image.width
        y1 = y1
        x2 = x-5-balloon_r.image.width
        y2 = y-3
        balloon_c._vertex_list.vertices[:] = [x1, y1, x2, y1, x2, y2, x1, y2]



        label = cocos.text.Label(text,
            font_name='Times New Roman',
            font_size=32,
            x=x1, y=y-20,
            anchor_x='left', anchor_y='top', width=x-face.image.width*face.scale-40, multiline=True)
        label.element.color = 0,0,0,255
        self.add(label, z=1)
        self.do( Delay(duration) + CallFunc(self.end_talking) )
