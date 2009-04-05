
import pyglet
import pyglet.font

import cocos
from cocos.director import director

import uiview
# let know pyglet where are the app resources
pyglet.resource.path.append('data')
pyglet.resource.reindex()
pyglet.font.add_directory('data')


director.init( resizable=True, width=800, height=600 )
scene = cocos.scene.Scene()
scene.add( cocos.layer.MultiplexLayer(
                uiview.GameIntro(), 
                uiview.StartMatchLayer()
                ),
            z=1 ) 
director.run( scene )

