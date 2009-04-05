""" code to glue model, view, controller parts"""
import cocos
import cocos.scene

import models
import controller
import playview

def get_new_ladder():
    '''returns the game scene'''
    scene = cocos.scene.Scene()

    # model
    model = models.GameLadder()

    # controller
    ctrl = controller.LadderController( model )

    # view
    view = playview.LadderView( model )

    # set controller in model
    model.set_controller( ctrl )

    # add controller
    scene.add( ctrl, z=1, name="controller" )

    # add view
    scene.add( view, z=2, name="view" )

    return scene

def get_new_level(level, result_callback):
    """returns the level scene"""
    scene = cocos.scene.Scene()

    #model : got as the 'level' param

    # controller
    ctrl = controller.PlayController( level )

    # view
    hud = playview.HUD()
    view = playview.WorldView( level, hud, result_callback )

    # set controller in model
    level.set_controller( ctrl )

    # add controller
    scene.add( ctrl, z=1, name="controller" )

    # add view
    scene.add( hud, z=3, name="hud" )
    scene.add( view, z=2, name="view" )

    return scene
