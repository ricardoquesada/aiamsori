
from waypointing import *
from cocos.euclid import Vector2 as V2
from geom import dist_point_to_segment

fe = 1.0e-4 #float error allowed in assert

def rotate(v,degs):
    return V2(v.x*math.cos(math.radians(degs))-v.y*math.sin(math.radians(degs)),
              v.x*math.sin(math.radians(degs))+v.y*math.cos(math.radians(degs)))

def translate(v,offset):
    return v+offset

def sort2v2ip(li2): # lista de V2 no compara bien con .sort()
    if len(li2)<2:
        return
    a1 , a2 = li2[0]
    b1 , b2 = li2[1]
    if (a1>b1) or ((a1==b1) and (a2>b2)):
        li2[0] = li2[1]
        li2[1]  = V2(a1,a2)    
################
def line_circle_intersection(p0,p1,center,r):
    v = p1-p0
    
    a = v.dot(v)
    b = 2.0*v.dot(p0-center)
    c = (p0-center).dot(p0-center)-r*r

    disc = b*b-4*a*c
    if disc<0.0:
        return []
    if disc == 0.0:
        return [p0 - (b/(2.0*a))*v]
    disc = math.sqrt(disc)
    return [ p0 + ( (-b-disc)/(2.0*a))*v,
             p0 + ( (-b+disc)/(2.0*a))*v]

def test_line_circle_intersection():
    center = V2(0,0)
    r = 1.0

    p0 = V2(-1,1)
    p1 = V2(1,1)
    res = line_circle_intersection(p0,p1,center,r)
##    print res
    for p in res:
        assert(abs(p-V2(0.0 , 1.0))<fe)
    
    center = (p0+p1)/2.0
    r = 0.5
    results = [V2(-0.5, 1),V2(0.5, 1)]
    res = line_circle_intersection(p0,p1,center,r)
    sort2v2ip(results)
    sort2v2ip(res)
##    print res
##    print results
    assert((abs(res[0]-results[0])+abs(res[1]-results[1]))<2*fe) # fails with 1e-3

    center = V2(0,0)
    r = 2.0
    p0 = V2(1,-1)
    p1 = V2(3,1)
    results = [V2(2, 0),V2(0, -2)]
    res = line_circle_intersection(p0,p1,center,r)
    sort2v2ip(results)
    sort2v2ip(res)
##    print res
##    print results
    assert((abs(res[0]-results[0])+abs(res[1]-results[1]))<2*fe)
    print 'test line_circle_colision ok'

################
def ray_circle_intersection(p0,p1,center,r):#ray goes from p0 passing over p1
    v = p1-p0
    
    a = v.dot(v)
    b = 2.0*v.dot(p0-center)
    c = (p0-center).dot(p0-center)-r*r

    disc = b*b-4*a*c
    res = []
    if disc == 0.0:
        t = - b/(2.0*a)
        if t>=0.0:
            res.append(p0 + t*v)
    elif disc>0:
        disc = math.sqrt(disc)
        t = (-b-disc)/(2.0*a)
        if t>=0:
            res.append(p0+t*v)
        t = (-b+disc)/(2.0*a)
        if t>=0:
            res.append(p0+t*v)
    return res    

def test_ray_circle_intersection():
    center = V2(0,0)
    r = 1.0

    p0 = V2(-1,1)
    p1 = V2(1,1)
    res = ray_circle_intersection(p0,p1,center,r)
    for p in res:
        assert(abs(p-V2(0.0 , 1.0))<fe)
##    print ray_circle_intersection(p0,p1,center,r)
    
    center = (p0+p1)/2.0
    r = 0.5
    results = [V2(-0.5, 1),V2(0.5, 1)]
    res = ray_circle_intersection(p0,p1,center,r)
    sort2v2ip(results)
    sort2v2ip(res)
    assert((abs(res[0]-results[0])+abs(res[1]-results[1]))<fe)

    center = V2(0,0)
    r = 2.0
    p0 = V2(1,-1)
    p1 = V2(3,1)
    res = ray_circle_intersection(p0,p1,center,r)
##    print res
    assert(len(res)==1 and abs(res[0]-V2(2,0))<fe)     
    print 'test ray_circle_colision ok'

################
def segment_circle_intersection(p0,p1,center,r):

    u = (p0+p1)/2.0
    v = p1-p0

    a = v.dot(v)
    b = 2.0*v.dot(u-center)
    c = (u-center).dot(u-center)-r*r

    disc = b*b-4*a*c
    res = []
    if disc == 0.0:
        t = - b/(2.0*a)
        if abs(t)<=0.5:
            res.append(u +t*v)
    elif disc>0.0:
        disc = math.sqrt(disc)
        t = (-b-disc)/(2.0*a)
        if abs(t)<=0.5:
            res.append(u + t*v)
        t = (-b+disc)/(2.0*a)
        if abs(t)<=0.5:
            res.append(u + t*v)
    return res

def test_segment_circle_intersection():
    center = V2(0,0)
    r = 1.0

    p0 = V2(-1,1)
    p1 = V2(1,1)
    res = segment_circle_intersection(p0,p1,center,r)
##    print res
    for p in res:
        assert(abs(p-V2(0.0 , 1.0))<fe)
    
    center = (p0+p1)/2.0
    r = 0.5
    results = [V2(-0.5, 1),V2(0.5, 1)]
    res = segment_circle_intersection(p0,p1,center,r)
##    print res
    sort2v2ip(results)
    sort2v2ip(res)
    assert((abs(res[0]-results[0])+abs(res[1]-results[1]))<fe)

    center = V2(0,0)
    r = 2.0
    p0 = V2(1,-1)
    p1 = V2(3,1)
    res = segment_circle_intersection(p0,p1,center,r)
##    print res
    assert(len(res)==1 and abs(res[0]-V2(2,0))<fe)     
    print 'test segment_circle_colision ok'

################
def visiblesball_factory( center, r):
    def fn_visibles(a,b):
        res = segment_circle_intersection(a,b,center,r)
#        print 'res int:',res
        return 0==len(segment_circle_intersection(a,b,center,r))
    return fn_visibles

def test_fn_visibles():
    center = V2(0,0)
    r = 1
    fn_visibles = visiblesball_factory(center,r)

    a = V2(-1,1)
    bs = [ V2(-1,2), V2(1,-1), V2(1.10, 0) ,V2(-2,2)]
    results = [  True,     False,       False, True]
    res = [ fn_visibles(a,p) for p in bs]
##    print results
##    print res
    pairs = zip(res,results)
    for u,v in pairs:
        assert(u==v)

    # same but translated (3,5)
    def translate3_5(v):
        return translate(v,V2(3,5))
    center = V2(0,0)
    center = translate3_5(center)
    r = 1
    fn_visibles = visiblesball_factory(center,r)

    a = V2(-1,1)
    a = translate3_5(a)
    bs = [ V2(-1,2), V2(1,-1), V2(1.10, 0) ,V2(-2,2)]
    q = [ translate3_5(b) for b in bs]
    bs = q
    res = [ fn_visibles(a,p) for p in bs]
##    print results
##    print res
    pairs = zip(res,results)
    for u,v in pairs:
        assert(u==v)
    print 'test tn_visibles ok'    

################
def test_deviation():
    import math
    class MockupActor:
        def __init__(self,position):
            self.position = position
        
    class MockupVoucher(Voucher):
        def __init__(self,actor,comming,going):
            self.chaser_actor = actor
            self.comming = comming
            self.going = going

    def rotate45(v):
        return rotate(v,45)
    
    def translate3_5(v):
        return translate(v,V2(3,5))
                               
            
    actor = MockupActor(V2(0,0))
    voucher = MockupVoucher(actor,V2(-1,0),V2(1,0))

    actor.position = V2(0,7)
    print voucher.deviation()
    assert(abs(voucher.deviation()-7.0)<1.0e-3)
    actor.position = V2(0,0)
    assert(abs(voucher.deviation()-0.0)<1.0e-3)

    # same but rotated 45 deg
    actor = MockupActor(V2(0,0))
    voucher = MockupVoucher(actor,V2(-1,0),V2(1,0))

    voucher.comming = rotate45(voucher.comming)
    voucher.going = rotate45(voucher.going)
    actor.position = V2(0,7)
    actor.position = rotate45(actor.position)
    assert(abs(voucher.deviation()-7.0)<1.0e-3)
    actor.position = V2(0,0)
    actor.position = rotate45(actor.position)
    assert(abs(voucher.deviation()-0.0)<1.0e-3)

    # same but translated
    actor = MockupActor(V2(0,0))
    voucher = MockupVoucher(actor,V2(-1,0),V2(1,0))

    voucher.comming = translate3_5(voucher.comming)
    voucher.going = translate3_5(voucher.going)
    actor.position = V2(0,7)
    actor.position = translate3_5(actor.position)
    assert(abs(voucher.deviation()-7.0)<1.0e-3)
    actor.position = V2(0,0)
    actor.position = translate3_5(actor.position)
    assert(abs(voucher.deviation()-0.0)<1.0e-3)
    print 'test deviation ok'

def test_dist_point_to_segment():
    x1 = (-1,0) ; x2=(0,1)
    p = (-2,0)
    assert( abs(dist_point_to_segment(p,x1,x2)-1.0)<fe)
    print 'test dist_point_to_segment ok'
    
if __name__ == '__main__':
    test_deviation()
    test_segment_circle_intersection()
    test_line_circle_intersection()
    test_ray_circle_intersection()
    test_fn_visibles()
    test_dist_point_to_segment()
