from pyglet.window import key # for key constants and KeyStateHandler

import cocos
import cocos.layer
from cocos.director import director

class LadderController( cocos.layer.Layer ):

    is_event_handler = True #: enable pyglet's events

    def __init__(self, model):
        super(LadderController,self).__init__()

        self.model = model

    def on_enter(self):
        print 'ladder on_enter'
        super(LadderController,self).on_enter()
        self.play_triggered = False
        self.allow_early_play = False
        self.schedule_interval(self.enable_early_play, 0.1)
        # ojo, podemos entrar por escape (como para salir) , por cambio/
        # restart de nivel, o en caso de gameover

    def on_exit(self):
        self.unschedule(self.play_level)
        super(LadderController,self).on_exit()

    def enable_early_play(self,dummy):
        print 'ladder enable...'
        self.allow_early_play = True
        self.unschedule(self.enable_early_play)
        self.schedule_interval(self.play_level, 1.0)

    def on_key_press(self, k, m ):
        if self.allow_early_play:
            self.play_level(0)
        elif k==key.ESCAPE:
            return False
        return True

    # bussines logic --->
    def play_level(self,dummy):
        print 'ladder play_'
        if not self.play_triggered:
            self.play_triggerred = True
            self.model.start_level()
    # <--- bussines logic

##    def draw( self ):
##        ''''''
##        pass


class PlayController( cocos.layer.Layer ):

    is_event_handler = True #: enable pyglet's events

    def __init__(self, level):
        super(PlayController,self).__init__()

        self.paused = True #begins paused, in tetrico was unpaused from
                           #model.set_next_level

        self.level = level

        self.bindings = { #key constant : button name
            key.LEFT:'left',
            key.RIGHT:'right',
            key.UP:'up',
            key.DOWN:'down'
            }
        self.buttons = { #button name : current value, 0 not pressed, 1 pressed
            'left':0,
            'right':0,
            'up':0,
            'down':0
            }

    #tracking of keys : keys updates self.buttons, model uses buttons
    def on_key_press(self, k, m ):
        binds = self.bindings
        if k in binds:
            self.buttons[binds[k]] = 1
            return True
        return False

    def on_key_release(self, k, m ):
        binds = self.bindings
        if k in binds:
            self.buttons[binds[k]] = 0
            return True
        return False


    def pause_controller( self ):
        '''removes the schedule timer and doesn't handler the keys'''
        self.paused = True
        self.unschedule( self.step )

    def resume_controller( self ):
        '''schedules  the timer and handles the keys'''
        self.paused = False
        self.schedule( self.step )

    def step( self, dt ):
        '''updates the engine'''
##        #if not self.paused:
        self.level.update( dt, self.buttons )
        

##    def draw( self ):
##        ''''''
##        pass
