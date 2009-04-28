import pyglet

sound_resources =  {
    'zombie_attack': 'sounds/zombie_attack.wav',
    'player_defend': 'sounds/player_defend.mp3',
    'player_die':    'sounds/player_die.mp3',
    'player_punch':  'sounds/player_punch.ogg',
}

class Sounds(object):
    """
        Para agregar un sonido:
            self.sounds = {'nombre_de_la_accion':
                pyglet.resource.media('sounds/file_name.ext', streaming=False)}

        Para reproducir un sonido:
            from sound import Sounds
            a = Sounds()
            a.sound('nombre_de_la_accion')
    """

    def __init__(self):
        try:
            import pyglet.media.avbin
            self.have_avbin = True
            self.music = True
            self.sfx = True
        except:
            pyglet.options['audio'] = ('silent')
            self.have_avbin = False
            self.music = False
            self.sfx = False

        self.playing = False

        self.sounds = dict([(k,  pyglet.resource.media(v, streaming=False)) for k, v in sound_resources.items() ])


    def play(self, s):
        if self.have_avbin and self.sfx:
            self.sounds[s].play().volume *= 1

play = None
def init():
    global play
    play = Sounds().play
