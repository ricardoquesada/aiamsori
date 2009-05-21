
import os.path
import simplejson
import optparse

import pyglet
import avbin
from pyglet import gl, font

import cocos
from cocos import framegrabber
from cocos.actions import Delay, CallFunc, FadeTo, FadeOut, Show, Hide, FadeIn, FadeOut
from cocos.director import director

import sound

# modules that need to be imported to get services registered:
import intro_outro
import gamescene

# globals
import gg

def main():
    # make available options
    parser = optparse.OptionParser()
    parser = optparse.OptionParser()
    parser.add_option("-w", "--wpting",
                      action="store_true", dest="wpt_on", default=False,
                      help="waypointing mode on")
    parser.add_option("-x", "--width", type='int', dest="width", default='1024',
                      help="set window width", metavar="WIDTH")
    parser.add_option("-y", "--height", type="int", dest="height", default='768',
                      help="set window height", metavar="HEIGHT")

    global options
    (options, args) = parser.parse_args()

    #copy to globals module gg each value you need available.
    gg.wpt_on = options.wpt_on
    
    # fix pyglet resource path
    basepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
    pyglet.resource.path.append(basepath)
    pyglet.resource.reindex()

    #Fonts stuff
    fonts_path = os.path.join(basepath, 'data/fonts')
    font.add_directory(fonts_path)

    print "#####################################################################"
    print "#####################################################################"
    print "###                                                               ###"
    print "###                 if you get a segfault                         ###"
    print "###                                                               ###"
    print "###                    please try again                           ###"
    print "###                                                               ###"
    print "###                multiplatform sound sucks                      ###"
    print "###                                                               ###"
    print "#####################################################################"
    print "#####################################################################"

    #Load avbin
    avbin.init_avbin()

    try:
        import cocos.gl_framebuffer_object as FG
        FG.FramebufferObject().check_status()
        has_grabber = True
    except Exception:
        print 'ERROR: You should install your video card drivers.'
        print 'If you already have, your video card doesn\'t support this game\'s effects.'
        print "press enter to play without effects"
        raw_input()
        has_grabber = False
    gamescene.has_grabber = has_grabber

    # initialize cocos director
#    director.init(fullscreen=True)
    director.init(options.width, options.height, resizable=True)
    sound.init()

    director.set_3d_projection()
#    director.set_2d_projection()

    #<----- startup end - all subsystem initialized - services availables

    # FIXME: transition between scenes are not working
    scene = gg.services["s_get_intro_scene"]()
##    scene = gg.services["s_get_game_scene"]()
##    scene = gg.services["s_get_end_scene"]()
    director.run(scene)

if __name__ == '__main__':
    main()
