import pyglet

sound_resources =  {
#    'zombie_attack': 'sounds/zombie_attack.wav',
#    'player_defend': 'sounds/player_defend.mp3',
    'player_die':    'sounds/player_die.mp3',
#    'player_punch':  'sounds/player_punch.ogg',
    'game_music': 'sounds/Music01.ogg',
    'intro_music': 'sounds/Musictitle.ogg',
    'zombie_eat': 'sounds/ZombieEat.ogg',
    'fire_shotgun': 'sounds/Shoot01.ogg',
    'melee': 'sounds/player_punch.ogg',
    'pickup_helth': 'sounds/pickup_health.wav',
    'pickup_shotgun': 'sounds/pickup_shotgun.wav',
##    'game_music': 'sounds/player_die.mp3',
   'intro_music': 'sounds/Musictitle.ogg',
##    'zombie_eat': 'sounds/player_die.mp3'
}

music_player =  pyglet.media.Player()

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


    def play(self, s, vol=1):
        if self.have_avbin and self.sfx:
            self.sounds[s].play().volume *= vol

    def play_music(self, m, vol=0.15):
        if self.have_avbin and self.music:
            if m :
                music_player.queue(self.sounds[m])
            music_player.play()
            music_player.volume = vol
            music_player.eos_action = 'loop'

play = None
def init():
    global play
    play = Sounds().play
    global play_music
    play_music = Sounds().play_music
