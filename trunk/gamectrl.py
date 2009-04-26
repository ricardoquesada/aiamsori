from cocos.director import director
from cocos.scene import Scene
from cocos.layer import Layer, ColorLayer


class GameCtrl(Layer):
    is_event_handler = True

    def __init__(self):
        super(GameCtrl, self).__init__()


class DummyGame(ColorLayer):

    def __init__(self):
        super(DummyGame, self).__init__()
        
        

if __name__ == "__main__":

    director.init(width=800, height=600, fullscreen=False )


    dummy_game =  Scene(DummyGame(200,100,100,255))
    director.run(dummy_game)

