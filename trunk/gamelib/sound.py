import pyglet

sound_resources =  {
    'zombie_attack': 'sounds/zombie_attack.wav',
    'player_defend': 'sounds/player_defend.mp3',
    'player_die':    'sounds/player_die.mp3',
    'player_punch':  'sounds/player_punch.ogg',
}

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


    def play(self, s):
        if self.have_avbin and self.sfx:
            self.sounds[s].play().volume *= 1

play = None
def init():
    global play
    play = Sounds().play
