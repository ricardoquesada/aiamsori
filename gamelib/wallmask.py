

class WallMask(object):
    def __init__(self):
        self.tilesize = 20
        self.wallmask = set()

    def add(self,sprite): #only if apropiate
        padding = 2
        sx = (sprite.x - sprite.width/2)/self.tilesize - padding
        sy = (sprite.y - sprite.height/2)/self.tilesize - padding
        for x in range(sprite.width/self.tilesize+1 + padding*2):
            for y in range(sprite.height/self.tilesize+1 + padding*2):
                key = int(sx+x),int(sy+y)
                self.wallmask.add(key)


    def is_empty(self,x,y):
        key = (int(x/self.tilesize),int(y/self.tilesize))
        result = not key in self.wallmask
        return result
