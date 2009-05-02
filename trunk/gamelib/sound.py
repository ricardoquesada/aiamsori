import pyglet

sound_resources =  {
    'ZombieDie': 'sounds/ZombieDie.ogg',
    'ZombieGerman': 'sounds/ZombieGerman.ogg',
    'player_die':    'sounds/player_die.mp3',
#    'player_punch':  'sounds/player_punch.ogg',
    'game_music': 'sounds/Music01.ogg',
    'intro_music': 'sounds/Musictitle.ogg',
    'zombie_eat': 'sounds/ZombieEat.ogg',
    'fire_shotgun': 'sounds/Shoot01.ogg',
    'melee': 'sounds/player_punch.ogg',
    'pickup_helth': 'sounds/pickup_health.wav',
    'pickup_shotgun': 'sounds/pickup_shotgun.wav',
    'MusicEnd': 'sounds/MusicEnd.ogg',
   'intro_music': 'sounds/Musictitle.ogg',
##    'zombie_eat': 'sounds/player_die.mp3'
}

current_music = None
play = None

class Sounds(object):
    """
        Para agregar un sonido agregar:
        'nombre_de_la_accion': 'sounds/file_name.ext',
        a sound_resorces

        Para reproducir un sonido:
            import sound
            play('nombre_de_la_accion')
    """

    def __init__(self):
        try:
            import pyglet.media.avbin as PMA
            self.have_avbin = True
            self.music = True
            self.sfx = True
        except:
            pyglet.options['audio'] = ('silent')
            self.have_avbin = False
            self.music = False
            self.sfx = False

        self.playing = False

        if self.have_avbin:
            self.sounds = dict([(k,  pyglet.resource.media(v, streaming=False)) for k, v in sound_resources.items() ])
            self.music_player =  pyglet.media.Player()


    def play(self, s, vol=1):
        if self.have_avbin and self.sfx:
            self.sounds[s].play().volume *= vol

    def set_music(self, name, volumen=1):
        global current_music

        if not self.have_avbin:
            return

        if name == current_music:
            return

        current_music = name

        if not self.music:
            return

        self.music_player.next()
        self.music_player.queue(pyglet.resource.media(sound_resources[name], streaming=True))
        self.music_player.play()
        # pyglet bug
        self.music_player.volume = volumen
        self.music_player.eos_action = 'loop'

    def stop_music(self):
        #self.music_player.eos_action = 'next'
        #self.music_player.next()
        if not self.have_avbin:
            return
        self.music_player.pause()

def init():
    a = Sounds()
    global play
    play = a.play
    global play_music, stop_music
    play_music = a.set_music
    stop_music = a.stop_music
