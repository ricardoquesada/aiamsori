import shader

light_f = '''
uniform sampler2D tex;
uniform vec2 light;

void main() {
    vec2 pos = gl_TexCoord[0].st;
    vec4 col = texture2D(tex, pos).rgba;

    vec2 v = light - gl_FragCoord.xy;
    float d = length(v);
    float a = clamp(52.0/d, 0., 1.);

    gl_FragColor = vec4(col.rgb, min(col.a, a));
}
'''

class Light(object):
    def __init__(self, x, y):
        self.position = x, y
        self.shader = shader.ShaderProgram()
        self.shader.setShader(shader.FragmentShader('light_f', light_f))
        self.enabled = False

    def set_position(self, x, y):
        self.position = x, y
        if self.enabled:
            print "setting new position", x, y
            self.shader.uset2F('light', float(x), float(y))

    def enable(self):
        self.enabled = True
        self.shader.install()
        x, y = self.position
        self.shader.uset2F('light', float(x), float(y))


    def disbale(self):
        self.enabled = False
        self.shader.uninstall()
