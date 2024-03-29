# ----------------------------------------------------------------------------
# cocos2d
# ----------------------------------------------------------------------------
'''
ToolBar test
'''

__docformat__ = 'restructuredtext'

# This code is so you can run the samples without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cocos
from cocos.scene import *
from cocos.layer import *
from cocos.cocosnode import *
from cocos.sprite import *
from cocos.widget_container import *
from cocos.widget import *

from cocos.director import director

TOP_BAR_HEIGHT = 32
BOTTOM_BAR_HEIGHT = 32

class Test(Layer):

    def __init__(self):
        super(Test, self).__init__()

        x,y = director.get_window_size()

        j = 1
        for i in ['left','right','center']:
            bar = self.create_hbar(x,(j-1)*15)
            bar.position = (0,130*j)
            j += 1

            bar.align_horizontal(i)

            self.add( bar )

    def create_hbar(self, w, spacing):
        h = WidgetContainer( width=w,spacing=spacing)

        g = WidgetButton('tiles/set4/Chest Open.png', unselected_image='tiles/set4/Chest Closed.png', callback= self.callback)
        h.add(g)
        g = WidgetButton('tiles/set4/Chest Open.png', unselected_image='tiles/set4/Chest Closed.png', callback= self.callback)
        h.add(g)
        g = WidgetButton('tiles/set4/Chest Open.png', unselected_image='tiles/set4/Chest Closed.png', callback= self.callback)
        h.add(g)
        return h

    def callback( self, sender ):
        print sender


if __name__ == "__main__":
    director.init()
    s = Scene()
    t = Test()
    s.add(t)
    director.run( s )
