
from math import floor


class WallMask(object):
    def __init__(self,fname,tilesize):
        self.fname = fname
        self.tilesize = float(tilesize) # square
        self.wallmask = {}

    def add(self,sprite): #only if apropiate
        if sprite.path!=self.fname: #TODO: verify adjust OS compatibility
            return
        if ((sprite.width!=self.tilesize) or
            (sprite.height!=self.tilesize)):
            print '*** Unexpected : wall tile is not square!!!'
        self.wallmask[floor(sprite.x/self.tilesize),floor(sprite.y/self.tilesize)]=1

    def _fill_gaps(self): # asumes no holes
        #calc bounds
        xs = [ x for x,y in self.wallmask]
        ys = [ y for x,y in self.wallmask]
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)

        for x in xrange(min_x,max_x):
            for y in xrange(min_y,max_y):
                if (x,y) in self.wallmask:
                    pass
                else:
                    self.wallmask[x,y]=0

    def get_mask(self):
        self._fill_gaps()
        return self.wallmask

    def is_empty(self,x,y):
        key = (floor(x/self.tilesize),floor(y/tilesize))
        return (key in self.wallmask) and self.wallmask(k)



    

