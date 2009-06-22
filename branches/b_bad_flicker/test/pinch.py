#!/usr/bin/env python
import sys

from pyglet.gl import *
from pyglet import window, image

import shader

w = window.Window(512, 512)
kitten = image.load('kitten.jpg')

pinch_f = '''
uniform sampler2D tex;
uniform vec2 mouse;

void main() {
    vec2 pos = gl_TexCoord[0].st;
    vec3 col = texture2D(tex, pos).rgb;

    vec2 v = mouse - gl_FragCoord.xy;
    float d = length(v);
    float a = clamp(52.0/d, 0., 1.);

    gl_FragColor = vec4(col, a);
}
'''

pinchf = shader.ShaderProgram()
pinchf.setShader(shader.FragmentShader('pinch_f', pinch_f))
#pinchf.setShader(shader.VertexShader('pinch_v', pinch_v))

pinchf.install()


@w.event
def on_mouse_motion(x, y, *args):
    pinchf.uset2F('mouse', float(x), float(y))
    #pinchf.uset2F('mouse', float(x)/kitten.width, float(y)/kitten.height)
    return True


glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
while not w.has_exit:
    w.dispatch_events()
    glClear(GL_COLOR_BUFFER_BIT)
    kitten.blit(100, 0)
    w.flip()
