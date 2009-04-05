
import pyglet
import cocos
from cocos.director import director
import cocos.text
from cocos.actions import * # for actions
import soundex

import uiview
import MVClink
import g #globals

class LadderView( cocos.layer.Layer ):
    def __init__(self,game_ladder):
        super( LadderView, self ).__init__()
        self.game_ladder = game_ladder # model part
        self.add(uiview.StarBgLayer(),z=-1)
        self.game_ladder.push_handlers( self.on_new_level,
                                        #self.on_game_over
                                       )

    def on_enter(self):
        super(LadderView,self).on_enter()
        w,h = director.get_window_size()
        self.msg = cocos.text.Label( 'Level %d'%self.game_ladder.levelnum, 
            font_size=52,
            font_name=g.font_name,
            color=(255,255,255,255),
            anchor_y='center',
            anchor_x='center' )
        self.msg.position=(w/2.0, h/2.0)

        self.add( self.msg )
        if not self.game_ladder.ladder_continue:
            director.pop()

    def on_exit(self):
        if self.msg:
            self.remove(self.msg) # else next time double message
            self.msg = None
        super(LadderView,self).on_exit()

##    def on_game_over(self):
##        director.pop()

    def on_new_level( self, level, cbak_level_end ):
        print 'ladder on_new_level'
        director.push( MVClink.get_new_level(level, cbak_level_end) )
        return True


################################################################################
# taken from cocos samples/tetrico/HUD.py
class HUD( cocos.layer.Layer ):
    """Head Up Display

        Responsability:
        Provides layout and access to all the objects that draw on top of
        worldview.
        
        Current Parts:
        Show start-end level messages by delegation to MessageLayer
    """
    def __init__( self ):
        super( HUD, self).__init__()
        self.add( MessageLayer(), name='msg' )

    def show_message( self, msg, callback = None ):
        self.get('msg').show_message( msg, callback )


class MessageLayer( cocos.layer.Layer ):
    """Transitory messages over worldview

    Responsability:
    full display cycle for transitory messages, with effects and
    optional callback after hiding the message.
    """

    def show_message( self, msg, callback=None ):
        print 'show_msg'
        w,h = director.get_window_size()

        self.msg = cocos.text.Label( msg,
            font_size=52,
            font_name=g.font_name,
            anchor_y='center',
            anchor_x='center' )
        self.msg.position=(w/2.0, h)

        self.add( self.msg )

        actions = ( Show() + Accelerate(MoveBy( (0,-h/2.0), duration=0.5)) + 
                    Delay(1) +  
                    Accelerate(MoveBy( (0,-h/2.0), duration=0.5)) + 
                    Hide()
                   )

        if callback:
            actions += CallFunc( callback )

        self.msg.do( actions )
                    
################################################################################

class WorldView( cocos.layer.Layer ):

    def __init__(self, level, hud, result_callback ):
        super(WorldView,self).__init__()

        self.level = level
        self.hud = hud
        self.result_callback = result_callback
        self.add(cocos.layer.ColorLayer( *level.bg_color ), z=-1)
        self.enter_level()
        self.hud.show_message( 'GET READY', self.level.start_level ) #indirect call to model

    def enter_level(self):
        width, height = director.get_window_size()

        #load resources:
        pics = {}
        pics["player"] = pyglet.resource.image('player2.png')
        pics["food"] = pyglet.resource.image('food.png')
        pics["wall"] = pyglet.resource.image('wall.png')
        pics["gateopen"]= pyglet.resource.image('gateopen.png')
        self.pic_gateopen = pics["gateopen"]

        #start the world to view coordinate subsystem.
        #this proto implementation suposes
        # 1. director provides a 4:3 window
        # 2. window size dont changes along this object life.
        # 3. world coords given as complex numbers
        #set the initial world to view coord change helpers
        self.coord_wtuple = (0.0, 0.0, 400.0, 300.0 )# left,top,right,bottom of world
        self.coord_vtuple = (0.0, float(height), float(width), 0.0) # same for view window

        def w_to_v(c): # probably needs clamp
            x = c.real/self.coord_wtuple[2]*self.coord_vtuple[2]
            y = self.coord_vtuple[1]*(1.0-c.imag/self.coord_wtuple[3])
            return x,y
        self.coord_w_to_v = w_to_v
        self.coord_w_to_v_scale = self.coord_vtuple[2]/self.coord_wtuple[2]
        

        #fill table actor_id -> sprite for the initial actors in level.
        #the table will be the stock worldview.children_names dict
        w_to_v = self.coord_w_to_v 
        bscale = self.coord_w_to_v_scale/62.0 # /png_r
        for a in self.level.blist:
            if a.btype != "gate":
                spr = cocos.sprite.Sprite(pics[a.btype],
                                             position=w_to_v(a.pos),
                                             scale=a.radius*bscale
                                             )
            elif a.btype == "gate":
                spr = cocos.sprite.Sprite(pics["wall"],
                                             position=w_to_v(a.pos),
                                             scale=a.radius*bscale
                                             )
            else:
                print "unknown actor type:",a.btype
                continue
            self.add(spr, name="%s"%id(a),z=1)
            # id() is unique and inmutable, as per 2.6 python docs
            # need z>0 so that self.draw be called before attempt to draw childs,
            # and self.draw will be used to update childs from model
            # cocosnode only accepts string names for childs (too bad)

        self.level.push_handlers( self.on_delete_actor,
                                  self.on_gate_opened,
                                  self.on_level_conquered,
                                  self.on_level_losed
                                 )

    def on_enter(self):
        super(WorldView,self).on_enter()

        soundex.set_music('Ryan_Silva-Song_6.mp3')
        soundex.play_music()

    def on_exit(self):
        super(WorldView,self).on_exit()
        soundex.stop_music()

    def on_delete_actor(self,idx):
        self.remove("%s"%idx) # cocosnode will only accepts str names
        return True

    def on_gate_opened(self,gate_obj):
        # with other sprites one can change the current img (cell) from wall
        # to opengate, not knowing if feasible and how to in cocos, let
        # remove the old sprite and make a new one
        self.remove("%s"%id(gate_obj)) # cocosnode child name can only be str
        w_to_v = self.coord_w_to_v 
        bscale = self.coord_w_to_v_scale/62.0 # /png_r
        spr = cocos.sprite.Sprite(self.pic_gateopen,
                                     position=w_to_v(gate_obj.pos),
                                     scale=gate_obj.radius*bscale
                                     )
        self.add(spr)
        return True

    def on_level_conquered(self):
#        soundex.play('level_conquered.mp3')
        self.hud.show_message('Level complete', self.msg_out_done)
        return True

    def on_level_losed(self):
#        soundex.play('level_losed.mp3')
        self.hud.show_message('Ouch!!!', self.msg_out_done)
        return True

    def msg_out_done(self):
        self.result_callback(self.level.is_conquered())
        director.pop()
    
    def draw( self ):
        '''update sprites, following model'''
        import math 
        #update player pos-impulse indicator direction
        w_to_v = self.coord_w_to_v
        mplayer = self.level.player
        spr_player = self.get("%s"%id(mplayer))
        spr_player.position = w_to_v(mplayer.pos)
        impulse_dir = self.level.impulseDir #complex
        spr_player.rotation = 180-math.degrees(math.atan2(impulse_dir.real,impulse_dir.imag))
