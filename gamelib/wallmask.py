

class WallMask(object):
    def __init__(self):
        self.tilesize = 20
        self.wallmask = set()

    def add(self,sprite): #only if apropiate
        padding = 2
        a = sprite.rotation%360
        if abs(a-90) < 45 or abs(a-270) < 45:
            w = sprite.height
            h = sprite.width
        else:
            w = sprite.width
            h = sprite.height
        sx = (sprite.x - w/2)/self.tilesize - padding
        sy = (sprite.y - h/2)/self.tilesize - padding
        for x in range(w/self.tilesize+1 + padding*2):
            for y in range(h/self.tilesize+1 + padding*2):
                key = int(sx+x),int(sy+y)
                self.wallmask.add(key)


    def is_empty(self,x,y):
        key = (int(x/self.tilesize),int(y/self.tilesize))
        result = not key in self.wallmask
        return result
