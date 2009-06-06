import re
import collections
import pyglet
#interesting entities
zombie_spawn = [

        "zombie_spawn:zombie-spawm#0",
        "zombie_spawn:zombie-spawm#1",
        "zombie_spawn:zombie-spawm#2",
        "zombie_spawn:zombie-spawm#3",
        "zombie_spawn:zombie-spawm#4",
]
item_spawn = [

        "item_spawn:item-spawn#0",
        "item_spawn:item-spawn#1",
        "item_spawn:item-spawn#2",
        "item_spawn:item-spawn#3",
        "item_spawn:item-spawn#4",
]
waypoints = [

        "waypoints:waypoint#0",
        "waypoints:waypoint#1",
        "waypoints:waypoint#2",
        "waypoints:waypoint#3",
        "waypoints:waypoint#4",
        "waypoints:waypoint#5",
        "waypoints:waypoint#6",
        "waypoints:waypoint#7",
        "waypoints:waypoint#8",
        "waypoints:waypoint#9",
        "waypoints:waypoint#10",
        "waypoints:waypoint#11",
        "waypoints:waypoint#12",
        "waypoints:waypoint#13",
        "waypoints:waypoint#14",
        "waypoints:waypoint#15",
        "waypoints:waypoint#16",
        "waypoints:waypoint#17",
        "waypoints:waypoint#18",
        "waypoints:waypoint#19",
        "waypoints:waypoint#20",
        "waypoints:waypoint#21",
        "waypoints:waypoint#22",
        "waypoints:waypoint#23",
        "waypoints:waypoint#24",
        "waypoints:waypoint#25",
        "waypoints:waypoint#26",
        "waypoints:waypoint#27",
        "waypoints:waypoint#28",
        "waypoints:waypoint#29",
        "waypoints:waypoint#30",
        "waypoints:waypoint#31",
        "waypoints:waypoint#32",
        "waypoints:waypoint#33",
]
lights = [

        "lights:luz_ventana#0",
        "lights:light#1",
        "lights:luz_ventana#2",
        "lights:light#3",
        "lights:luz_ventana#4",
        "lights:luz_ventana#5",
        "lights:light#6",
        "lights:luz_ventana#7",
        "lights:light#8",
        "lights:light#9",
        "lights:light#10",
        "lights:light#11",
        "lights:light#12",
        "lights:light#13",
        "lights:light#14",
        "lights:light#15",
        "lights:light#16",
]

ZOMBIE_WAVE_COUNT = 4
ZOMBIE_DEBUG = 0
ZOMBIE_WAVE_DURATION = 60

RANDOM_DELTA = 128
UNKNOWN_ITEM_PROBABILTY = 0.1
UNKNOWN_PLACE_PROBABILTY = 0.1

WAVE_DELAY = [15, 30, 25, 25, 20, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11]
WAVE_NUM   = [1,  1,  1,  1,  2,  2,  2,  2,  2, 3, 3, 3, 4, 4, 4]

PWUP_MIN_TIME = 10
PWUP_MAX_TIME = 30

##        self.zombie_spawn = None
##        self.z_spawn_lifetime = 0
##        self.zombie_wave_number = 0
##        self.schedule(self.respawn_zombies)
##
##        self.setup_powerups(item_spawn)
##
##        self.flicker()
script = """
#wait_for_event, map_loaded
wait, 3
talk, Bee, "Zombies are coming!", 2
talk, Mom, "Protect your family!", 2
talk, Zack, "Click on us to move us", 2
wait, 6
##relay, zombie_spawn:zombie-spawm#0, set_devflag, trace_cmds, 1
##relay, zombie_spawn:zombie-spawm#0, set_devflag, trace_state_changes, 1
##relay, zombie_spawn:zombie-spawm#0, set_devflag, show_errors, 1
add_zombie, zombie_spawn:zombie-spawm#0, zombie#1, boy
add_zombie, zombie_spawn:zombie-spawm#0, zombie#2, girl
add_zombie, zombie_spawn:zombie-spawm#0, zombie#3, mother
add_zombie, zombie_spawn:zombie-spawm#0, zombie#3, father
wait, 500

add_powerup, 'shotgun', "DAMN ZOMBIES!!!! Where's my shotgun!!!"
# level 0
play level_begin
add_swarm , 3, [wpts_initial patrol], 
wait, 1
wait_no_zombies
play level_ends
update_level
wait, 5 
"""

# regexes
rx_first_no_blank = re.compile(r'\s*(.)')
rx_match_arg = re.compile(r'\s*([^,]+)\s*')
rx_match_quoted_arg = re.compile(r'\s*"([^"]+)"\s*')

class ScriptDirector(pyglet.event.EventDispatcher):
    def __init__(self, script):
        self.script_lines = script.split('\n')
        self.linenum = 0
        self.waiting = False
        self.waiting_time = 0.0
        self.awaiting_event = None

    def next_command(self):
        while 1:
            line = self.script_lines[self.linenum]
            line = line.strip()
            self.linenum += 1
            if len(line)==0 or line[0]=='#':
                continue
            parts = collections.deque()
            start = 0
            linelen = len(line)
            bValid = True
            while start<linelen:
                match = rx_first_no_blank.match(line,start)
                if match is None:
                    break
                if match.group(1)=='"':
                    match = rx_match_quoted_arg.match(line, match.start()) 
                    if match is None:
                        print '*** warn : unbalanced "  , ignoring line',self.linenum
                        bValid = False
                        break
                    part = match.group(1)
                    # match.end() points 1st no blank after " or past EOL
                    if match.end()<linelen and line[match.end()]!=',':
                        print '*** warn : extra chars after ", ignoring line ',self.linenum
                        bValid = False
                        break
                else:
                    match = rx_match_arg.match(line,start)
                    if match is None:
                        # maybe EOL, maybe empty arg ',,' or ^,
                        if line.find(',',start)>-1:
                            print 'empty cmd or arg , ignoring line',self.linenum
                            bValid = False
                        break
                    part = match.group(1).rstrip()
                    # convert to the first type posible: int, float, string
                    res = None
                    try:
                        res = int(part)
                    except ValueError:
                        pass
                    if res is None:
                        try:
                            res = float(part)
                        except ValueError:
                            pass
                    if res is not None:
                        part = res

                parts.append(part)
                start = match.end()+1
            if bValid:
                return parts

    def game_event_handler(self,event):
        print '>>> scripter.game_event_handler() received',event 
        if event==self.awaiting_event:
            self.awaiting_event = None

    def update(self,dt,level_time):
        self.level_time = level_time
        # update waiting state
        self.waiting = self.waiting_time>level_time or self.awaiting_event

        # do script commands 
        while not self.waiting:
            # process script commands
            parts = self.next_command()
            cmd = parts.popleft()
            print '*** scripter loop got cmd, params', cmd, parts
            try:
                fn = getattr(self, 'c_%s'%cmd)
            except AttributeError:
                print 'script error: unknown command',cmd
                continue
            fn(parts)
            self.waiting = self.waiting_time>level_time or self.awaiting_event
            
    def c_wait(self,parts):
        if len(parts)!=1:
            print "error cmd script 'wait' bad parameter quantity; ignoring line",self.linenum
            return
        self.waiting_time = self.level_time + parts[0]

    def c_wait_for_event(self,parts):
        if len(parts)!=1:
            print "error cmd script 'wait_for_event' bad parameter quantity; ignoring line",self.linenum
            return
        self.awaiting_event = parts[0]
        
    def c_talk(self,parts):
        self.dispatch_event("on_talk",parts[0],parts[1],parts[2]) #who, what, duration

    def c_add_zombie(self,parts):
        self.dispatch_event("on_relay",parts[0],'spawn_zombie',parts[1],parts[2]) # zombie_spawn label, zombie label, target_label

    def c_relay(self,parts):
        self.dispatch_event("on_relay",*parts)

def test_next_command():
    script_director = ScriptDirector(script)
    while 1:
        print script_director.next_command()

if __name__ == '__main__':
    test_next_command()
                
##
##
##            self.z_spawn_lifetime += 1
##        else:
##            self.z_spawn_lifetime += dt
##            waveno = min(self.zombie_wave_number,len(WAVE_DELAY)-1)
##            delay = WAVE_DELAY[ waveno ]
##            if self.z_spawn_lifetime >= delay:
##                z_count = len([c for c in self.agents_node.get_children() if isinstance(c, Zombie)])
##                if z_count < 12:
##                    print "Wave Numer:", waveno, z_count
##                    # we have a zombie wave
##                    msg = random.choice([
##                        "cerebroooo.....",
##                        "brraaaaaiins....",
##                        "arrghhhhh....",
##                        "me hungry!"
##                    ])
##                    self.talk("zombie", msg)
##                    for i in range(WAVE_NUM[ waveno ]):
##                        for c in self.zombie_spawn.get_children():
## ..
##                    self.z_spawn_lifetime = 0
##                    self.zombie_wave_number += 1

##    def flicker(self):
##        delay = random.random()*5+2
##        action = Delay(delay)
##        light = random.choice(self.lights.get_children())
##
##        for i in range(random.randint(5, 10)):
##            micro_delay = random.random()*0.50
##            micro_delay2 = random.random()*0.50
##            action = action + FadeTo(50, micro_delay) + FadeTo(255, micro_delay2)
##        action = action + CallFunc(self.flicker)
##        light.do(action)
##
##    def setup_powerups(self, layer):
##        self.item_spawn = []
##        for c in layer.get_children():
##            self.item_spawn.append( c.position )
##        # wait 4 seconds before displaying first message
##        self.do(Delay(3) + CallFunc(lambda: self.talk('Bee', "Zombies are coming!", duration=2, transient=False)))
##        self.do(Delay(5) + CallFunc(lambda: self.talk('Mom', "Protect your family!", duration=2, transient=False)))
##        self.do(Delay(7) + CallFunc(lambda: self.talk('Zack', "Click on us to move us", duration=2, transient=False)))
##        self.do(Delay(9) + CallFunc(lambda: self.add_powerup('shotgun', "DAMN ZOMBIES!!!! Where's my shotgun!!!")))
##        self.spawn_powerup()
##
##    def spawn_powerup(self, type=''):
##        delay = random.randrange(PWUP_MIN_TIME, PWUP_MAX_TIME)
##        self.do(Delay(delay) + CallFunc(lambda: self.add_powerup(type)))
##
##    def add_powerup(self, type='', msg=''):
##        position = random.choice(self.item_spawn)
##        if not type:
##            # make ammo and life categories equally probable
##            type = random.choice(POWERUP_TYPE_AMMO_LIST*3 + POWERUP_TYPE_LIFE_LIST)
##        powerup = PowerUp(type, position, self)
##        self.agents_node.add(powerup)
##        item = type
##        if item == 'burger':
##            item = 'a burger'
##        elif item == 'medicine':
##            item = 'some medicine'
##        if random.random() < UNKNOWN_ITEM_PROBABILTY:
##            item = ''
##        place = powerup.label if hasattr(powerup, 'label') else ''
##        if random.random() < UNKNOWN_PLACE_PROBABILTY:
##            place = ''
##        if not msg:
##            msg = "I think I remember seeing "
##            if item:
##                msg += item
##            else:
##                msg += 'something'
##            if place:
##                msg += " in the %s." % place
##            else:
##                msg += ' somewhere.'
##        self.talk("Dad", msg, transient=False)
##        #print "powerup ", powerup, 'at', place, position
##
##    

# register the events scriptdirector will trigger
ScriptDirector.register_event_type('on_talk')
ScriptDirector.register_event_type('on_relay')
