import cocos
from cocos.director import director
from cocos.sprite import Sprite
from cocos.euclid import Vector2
import pyglet

def wpt_help():
    print 'waypoint editos binding'
    print 'movimientos como en juego'
    print 'F5   save private'
    print 'F8   load private'
    print 'SPACE add waypoint at the player position'
    print 'h    repeats this screen'

wpt_help()

# de momento solo interesa la posicion del waypoint
def wpt_from_privateX(fname):
    # el mismo nombre que map agregada extension wpt
    f=open(fname,'rb')        
    linenum = -1
    wpts = []
    for line in f:
        linenum += 1
        line = line.strip(' ').rstrip(' \r\n')
        print 'line:'
        if len(line)==0:
            continue
        li = line.split(' ')
        if len(li)!=2:
            print 'err parsing %s at line %d: expected <num> <num>\\n'%(fname,linenum)
        else:
            x = int(li[0])
            y = int(li[1])
            wpts.append((x,y))
    f.close()
    return wpts

def wpt_to_privateX(wpt_list, fname):
    f = open(fname,'wb')
    for e in wpt_list:
        f.write("%s %s\n"%(int(e[0]),int(e[1]))) #x,y
    f.close()

class WptLayer(cocos.layer.Layer):
    def __init__(self,mapname):
        super(WptLayer,self).__init__()
        self.mapname = mapname
        self.modified = False
        self.node_selected = None

    def clear(self):
        for e in self.get_children():
            self.remove(e)
        self.modified = False

    def spawn_many(self,wpt_list):
        for e in wpt_list:
            b = Sprite('data/wpt.png')
            b.x = e[0]
            b.y = e[1]
            self.add(b)

    def save_private(self):        
        wpts = self.get_wpt_list()
        self.wpt_to_private(wpts)
        self.modified = False
        print 'wpt save private'

    def load_private(self):
        self.clear()
        wpts = self.wpt_from_private()
        self.spawn_many(wpts)
        print 'wpt load private'
        
    def wpt_from_private(self):
        # el mismo nombre que map agregada extension wpt
        fname = self.mapname + '.wpt'
        f=open(fname,'rb')        
        linenum = -1
        wpts = []
        for line in f:
            linenum += 1
            line = line.strip(' ').rstrip(' \r\n')
            print 'line:'
            if len(line)==0:
                continue
            li = line.split(' ')
            if len(li)!=2:
                print 'err parsing %s at line %d: expected <num> <num>\\n'%(fname,linenum)
            else:
                x = int(li[0])
                y = int(li[1])
                wpts.append((x,y))
        f.close()
        return wpts
            
    def wpt_to_private(self, wpt_list):
        f = open(self.mapname + '.wpt','wb')
        for e in wpt_list:
            f.write("%s %s\n"%(int(e[0]),int(e[1]))) #x,y
        f.close()

    def get_wpt_list(self):
        wpts = []
        for e in self.get_children():
            x , y = e.position
            wpts.append((x,y))
        return wpts

    def help(self):
        wpt_help()
        
def test_dire_load_save():
    wpts = [(0,1),(5,7)]
    fname = 'dire.json.wpt'
    wpt_to_privateX(wpts, fname)
    reloaded = wpt_from_privateX(fname)
    print 'wpts:',wpts
    print 'reloaded:',reloaded
    assert(wpts==reloaded)
    

def test_load_save():
    # fix pyglet resource path
    import os
    pyglet.resource.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
    pyglet.resource.reindex()
    director.init(width=640, height=480)

    mapname = 'data/testwptmap.json'
    layer = WptLayer(mapname)
    wpts = [(0,1),(5,7)]
    layer.spawn_many(wpts)
    res=layer.get_wpt_list()
##    print 'wpts:',wpts
##    print 'res:',res
    assert(wpts==res)

    
    
    layer.save_private()
    layer.clear()
    assert(len(layer.children)==0)
    assert(layer.modified==False)
    layer.load_private()
    reloaded = layer.get_wpt_list()
    print 'wpts:',wpts
    print 'reloaded:',res
    assert(wpts==reloaded)


    main_scene = cocos.scene.Scene (layer)
    director.run (main_scene)

if __name__ == "__main__":
    test_load_save()    
    #test_dire_load_save()        
