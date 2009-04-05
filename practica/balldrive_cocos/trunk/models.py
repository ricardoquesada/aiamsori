import weakref

# balldrive model
import pyglet

class GameLadder(pyglet.event.EventDispatcher):
    """
    Responsability:
        Handles level progression."""
    def __init__(self):
        super(GameLadder,self).__init__()
        # stats that persist between levels goes here ( score, lives, medals...)
        self.levelnum = 1 # level to play
        self.set_level()
        self.ladder_continue = True

    def set_controller( self, ctrl ):
        self.ctrl = weakref.ref( ctrl ) # access as self.ctrol().whatever

    ### business logic --->
        
    def set_level(self):
        levelmap = self.get_levelmap_from_levelnum()
        level = Level()
        level.load(levelmap)
        self.level = level

    def level_ends(self,bWin):
        if bWin:
            self.level_win()
        else:
            self.level_losed()

    def level_win(self):
        # level sequencer oportunity
        self.next_level()

    def next_level(self):
        self.levelnum += 1
        self.set_level()

    def level_losed(self):
        # if the gameplay allowed for multiple lives/ or 'load saved game',
        # this would be the point to handle those
        self.ladder_continue = False #self.dispatch_event("on_game_over")
        
    def start_level(self): # called at end of Ladder view
        self.dispatch_event("on_new_level", self.level, self.level_ends)

        # self.ctrl().resume_controller()

    ### <--- business logic
    
    def get_levelmap_from_levelnum(self):
        # future feature, will return a filename or the contents
        # for wich Level will have the responsability to parse.
        # in the meantime, return None. Level will understand
        # 'make a random level'
        return None

#GameLadder.register_event_type('on_game_over')
GameLadder.register_event_type('on_new_level')



##position and distances between points ( as radius or width) are expresed in
##world units/coordinates

class Level(pyglet.event.EventDispatcher): # complex coords, because the pygame version used these
    """
    Responsabilities:
        Generation: load or random generates a level
        Initial State: Set initial playststate
        Play: updates level state, by time and user input. Detection of
        end-of-level conditions.
    """
    def __init__(self):
        super(Level,self).__init__()
        # empty level, populated by random map, load, or editor interactions
        self.blist = [] # all actors
        self.player = None
        self.food_cnt = 0

        self.win_status = None # None | 'conquered' | 'losed' ,
                                # None means still playing

        #player phys params(must be reset at each level start)
        self.topSpeed = 75.0 #50.
        self.impulseDir = 0.0-1.0j
        self.impulseForce=0.0

    def set_controller( self, ctrl ):
        self.ctrl = weakref.ref( ctrl ) # access as self.ctrol().whatever

    def start_level(self): # called after the 'Ready' message vanishes in the HUD
        self.ctrl().resume_controller()

    def is_conquered(self):
        return ( self.win_status == 'conquered' )

    def load(self, levelmap):
        if levelmap is None:
            self.generate_random_level()
            return
        print 'not implemented'
        raise ValueError

    def generate_random_level(self):
        import random
        # hardcoded params:
        vWidth = 400. # world virtual width
        vHeight = 300. # world virtual height
        rPlayer = 8.0 # player radius in virtual space
        player_color = (255,0,0)
        border_color = (0,0,0) # outline color all actors
        food_num = 5
        food_color = (0,0,255)
        food_scale = 1.0 # relative to player
        wall_num = 10
        wall_color = (255,255,0)
        wall_scale_min = 0.75 # relative to player
        wall_scale_max = 2.25 # relative to player
        gate_open_color = (0, 255, 0)
        gate_scale = 1.5 # relative to player
        bg_color = (200,200,100,255)
        min_separation = 3.0 # as fraction of player diameter
        #level = Level( 10,5,(255,255,0),(200,200,100),3.) # params pygame generator

        # build !        
        self.bg_color = bg_color
        self.vWidth = vWidth
        self.vHeight = vHeight

        #add player
        self.player = Ball(0.5*vWidth,0.5*vHeight,rPlayer,'player')
        self.blist.append(self.player)

        minSeparation = min_separation*2.*rPlayer

        # add gate
        rGate = gate_scale * rPlayer
        cx,cy = 0.5*vWidth , 0.5*vHeight
        cntTrys = 0
        while self.collision(cx,cy,rGate,minSeparation) and cntTrys<100:
            cx = rGate+random.random()*(vWidth-2.0*rGate)
            cy = rGate+random.random()*(vHeight-2.0*rGate)
            cntTrys +=1
            if cntTrys == 100: # nota: resetear cntTrys ?
                continue
        self.gate = Ball(cx,cy,rGate,'gate')
        self.blist.append(self.gate)

        # add food
        rFood = food_scale*rPlayer
        self.cnt_food = 0
        for i in range(food_num):
            cntTrys = 0
            cx,cy = 0.5*vWidth , 0.5*vHeight
            while self.collision(cx,cy,rFood,minSeparation) and cntTrys<100:
                cx = rFood+random.random()*(vWidth-2.0*rFood)
                cy = rFood+random.random()*(vHeight-2.0*rFood)
                cntTrys +=1
            if cntTrys == 100:
                continue
            self.blist.append(Ball(cx,cy,rFood,'food'))
            self.cnt_food +=1

        # add walls
        for i in range(wall_num):
            cntTrys = 0
            s = random.random()
            r = rPlayer*( wall_scale_min*s + wall_scale_max*(1.0-s)) #lerp
            cx,cy = 0.5*vWidth , 0.5*vHeight
            while self.collision(cx,cy,r,minSeparation) and cntTrys<100:
                cx = r+random.random()*(vWidth-2.0*r)
                cy = r+random.random()*(vHeight-2.0*r)
                cntTrys +=1            
            if cntTrys == 100:
                continue
            self.blist.append(Ball(cx,cy,r,'wall'))
    
    def collision(self, cx, cy, r, minSeparation=0, ignoreBall=None):
        res = False
        index = 0
        c=complex(cx,cy)
        for ball in self.blist:
            sep = abs(c-ball.pos)-(r+ball.radius)
            if sep<minSeparation and id(ball)!=id(ignoreBall):
                res = True
                break
            index += 1
        if ignoreBall is None:
            return res
        else:
            return res,index

    def deleteActor(self,index):
        obj = self.blist.pop(index)
        # tell the view this object was deleted
        self.dispatch_event("on_delete_actor", id(obj) )

    ## playing the level    

    def update(self,dt,buttons):
        # if level conquered or losed dont update model
        if self.win_status:
            return

        # update impulse from buttons 
        if buttons['left']:
            self.impulseDir *= 0.99619469809174555-0.087155742747658166j #(cos,sin) of 5deg
#            self.impulseDir *= 0.984807753012-0.173648177667j #(cos,sin) of 10deg
        if buttons['right']:
            self.impulseDir *= 0.99619469809174555+0.087155742747658166j # 5 deg
#            self.impulseDir *= 0.984807753012+0.173648177667j # 10 deg
        if buttons['up']:
            self.impulseForce += 0.25 # todo: enforce an upper bound
        if buttons['down']:
            self.impulseForce -= 0.25
            if self.impulseForce<0.0:
                self.impulseForce = 0.0

        #world phys step
        impulse = self.impulseForce*self.impulseDir
        newVel = self.player.vel + impulse
        fasteness = abs(newVel)
        if fasteness>self.topSpeed:
            newVel = newVel/fasteness*self.topSpeed

        ppos=self.player.pos
        newPos = ppos
        #consume the dt
        r = self.player.radius
        while dt>1.e-6:
            newPos = ppos+dt*newVel
            consumed_dt = dt
            # what about screen boundaries ? if colision bounce
            if newPos.real<r:
                consumed_dt = (r-ppos.real)/newVel.real
                newPos = ppos+consumed_dt*newVel
                newVel = -newVel.conjugate()
            if newPos.real>(self.vWidth-r):
                consumed_dt = (self.vWidth-r-ppos.real)/newVel.real
                newPos = ppos+consumed_dt*newVel
                newVel = -newVel.conjugate()
            if newPos.imag<r:
                consumed_dt = (r-ppos.imag)/newVel.imag
                newPos = ppos+consumed_dt*newVel
                newVel = newVel.conjugate()
            if newPos.imag>(self.vHeight-r):
                consumed_dt = (self.vHeight-r-ppos.imag)/newVel.imag
                newPos = ppos+consumed_dt*newVel
                newVel = newVel.conjugate()
            dt -= consumed_dt
            
            #interactions with other balls
            bCollision, index = self.collision(newPos.real, newPos.imag,
                                            self.player.radius,0,self.player)        
            if bCollision:
                other = self.blist[index]
                typeball = other.btype
                if typeball == 'food':
                    self.deleteActor(index)
                    self.cnt_food -= 1
                    if not self.cnt_food:
                        # open gate: gate morphs from wall to opengate
                        gate = self.gate
                        self.dispatch_event("on_gate_opened", gate )

                elif (typeball == 'wall' or
                      typeball == 'gate' and self.cnt_food>0):
                    # player dies, levels ends with lose
                    if self.win_status is None:
                        self.win_status = 'losed'
                        self.dispatch_event("on_level_losed")

                elif typeball == 'gate':
                    # if no food, gate is open, level ends with win
                    # else gate can act as a wall
                    if self.win_status is None:
                        self.win_status = 'conquered'
                        self.dispatch_event("on_level_conquered")

        self.player.vel = newVel
        self.player.pos = newPos


Level.register_event_type('on_delete_actor')
Level.register_event_type('on_gate_opened')
Level.register_event_type('on_level_losed')
Level.register_event_type('on_level_conquered')



# all actors (wall, food, player, gate) are Balls in model    
class Ball:
    def __init__(self,cx,cy,radius,btype,vel=None):
        self.pos = complex(cx,cy)
        if vel is None:
            vel = complex(0.,0.)
        self.vel = vel
        self.radius = radius
        self.btype = btype


