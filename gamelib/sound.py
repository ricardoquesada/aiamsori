import pyglet

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

        self.sounds = { 'zombie_attack':
            pyglet.resource.media('sounds/zombie_attack.wav', streaming=False),
                        'player_defend':
            pyglet.resource.media('sounds/player_defend.mp3', streaming=False),
                        'player_die':
            pyglet.resource.media('sounds/player_die.mp3', streaming=False),
                        'player_punch':
            pyglet.resource.media('sounds/player_punch.ogg', streaming=False),
            }


    def sound(self, s):
        if self.have_avbin and self.sfx:
            self.sounds[s].play().volume *= 1
