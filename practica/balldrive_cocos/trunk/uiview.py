"""ui components that dont need to interact with the model

Examples are splash screens, main menu, settings menu"""
import math

import pyglet

import cocos
import cocos.draw
import cocos.text
from cocos.director import director
from cocos.actions import *

import g #globals

# StarBgLayer ##################################################################
# basically taken from cocos samples\test_draw_rotate.py

class StarBgLayer(cocos.layer.Layer):
    """ Composes a background for uiview scenes

    responsability:
    compose the background used in game intro and start match screens.
    """
    def __init__(self):
        super( StarBgLayer, self ).__init__()

        self.add( cocos.layer.ColorLayer(200,0,80,255) ) # needs explicit alpha
        self.add( RoundStarCanvas() )        
        self.schedule( lambda x: 0 )

class RoundStarCanvas(cocos.draw.Canvas):
    """ Composes a circle like shape, radius aprox big as 80% min screen dimension
    """
    def render(self):
        x,y = director.get_window_size()
        r = min(x,y)*0.6/2.0 ; print r
        ye = r
        xs = r
        line_width = 20
        self.set_color( (0,200,80,125) )
        self.set_stroke_width( line_width )
        parts = int(2*math.pi*r/line_width)
        # draw lines
        self.set_endcap( cocos.draw.ROUND_CAP )
        self.translate(( x/2, y/2 ))
        for i in range(parts):
            self.move_to( (0,0) )
            self.line_to( (xs,ye) )
            self.rotate( 2*math.pi/ parts )

def test_StarBgLayer():
    director.init()
    test_layer = StarBgLayer()
    main_scene = cocos.scene.Scene(test_layer)
    director.run(main_scene)



# Game Intro ###################################################################
# basically taken from cocos samples\tetrico\HUD.py MessageLayer

class GameIntro(cocos.layer.Layer):
    """ Game Intro screen

        responsability: presents the game name ; after a prescribed time
        switchs screen to 'start match screen'
    """
    def __init__(self):
        super( GameIntro, self ).__init__()

        self.add(StarBgLayer(),z=-1)

    def on_enter(self):
        super(GameIntro,self).on_enter()
        w,h = director.get_window_size()
        self.msg = cocos.text.Label( 'Cocos Balldrive', 
            font_size=52,
            font_name=g.font_name,
            color=(255,255,255,255),
            anchor_y='center',
            anchor_x='center' )
        self.msg.position=(w/2.0, h)

        self.add( self.msg )
        actions = ( Show() +
                    Accelerate(MoveBy( (0,-h/2.0), duration=0.5)) + 
                    Delay(1) +  
                    Accelerate(MoveBy( (0,-h/2.0), duration=0.5)) + 
                    Hide() +
                    CallFunc( self.end_intro )
                   )
        self.msg.do( actions )

    def end_intro( self ):
        self.parent.switch_to(1) # want to switch to StartMatch
        pass            

def test_GameIntro():
    director.init()
    test_layer = GameIntro()
    # replace end_into for testing purposes
    import pyglet
    def test_end_intro(instance):
        pyglet.app.exit()
    import new
    test_layer.end_intro = new.instancemethod( test_end_intro, test_layer , GameIntro) # func, instance, class
    main_scene = cocos.scene.Scene(test_layer)
    director.run(main_scene)



# Start Match ##################################################################

from pyglet.window import key # for key constants
# code adapted from GameIntro
class StartMatchLayer(cocos.layer.Layer):
    """start match screen

        responsability: Presents the option 'start match ?',
        on yes starts a match,
        on no terminates the app.
    """
    is_event_handler = True #: enable pyglet's events (for keys)
    def __init__(self):
        super( StartMatchLayer, self ).__init__()

        self.add(StarBgLayer(),z=-1)

    def on_enter(self):
        super(StartMatchLayer,self).on_enter()
        w,h = director.get_window_size()
        self.msg = cocos.text.Label( 'Start Match ?', 
            font_size=52,
            font_name=g.font_name,
            color=(255,255,255,255),
            anchor_y='center',
            anchor_x='center' )
        self.msg.position=(w/2.0, h)

        self.add( self.msg )
        actions = ( Show() +
                    Accelerate(MoveBy( (0,-h/2.0), duration=0.5)) 
                   )
        self.msg.do( actions )

    def on_exit(self):
        self.stop()
        self.remove(self.msg) # else next time double message
        self.msg = None
        super(StartMatchLayer,self).on_exit()
        
    def on_key_press( self, k, m ):
        if k in [ key.ENTER, key.SPACE, key.Y]:
            self.selected_yes()
        elif k in [ key.ESCAPE, key.N]:
            self.selected_no()
        else:
            pass
        return True # make app ignore unknown keys

    def selected_yes( self ):
        import cocos.scenes
        import MVClink
##        director.push( cocos.scenes.RotoZoomTransition(
##            MVClink.get_new_ladder(), 1.5 ) )
        director.push( MVClink.get_new_ladder() )

    def selected_no( self ):
        import pyglet
        pyglet.app.exit()


def test_StartMatch():
                     
    director.init()
    test_layer = StartMatchLayer()
    # replace selected_yes for testing purposes
    import pyglet
    def test_end(instance):
        print 'selected yes'
        pyglet.app.exit()
    import new
    test_layer.selected_yes = new.instancemethod( test_end, test_layer , StartMatchLayer) # func, instance, class
    main_scene = cocos.scene.Scene(test_layer)
    director.run(main_scene)

if __name__ == "__main__":
    test_StartMatch()
