""" Waypointing

doing:
un poco de test heuristicos para debugear.
considerando mejorar algunas cosas, hay partes bastante brute force
"""




##FLOYD'S ALGORITHM (int **m, int size)
##{
##    int i,j,k;
##    for ( k = 0; k < size; k++ )
##        for ( i = 0; i < size; i++ )
##            for ( j = 0; j < size; j++ )
##                if ( m[i][k] + m[k][j] < m[i][j] )
##                    m[i][j] = m[i][k] + m[k][j];
##}
import math
from cocos.euclid import Vector2 as V2

bignum = 1.0e+40

class WaypointNav:
    def __init__(self,points,fn_visibles):
        """
        points: waypoints; all points in the map should have at least one waypoint in sight
        fn_visibles(a,b) True if point b is visible from point a

        Interfase Stateless:
        .get_dest(a,b): give a good intermediate point for going from a to b
                        warn: it is better to use the voucher interfase

        InterfaseVoucher: ( talk to the voucher object to navigate )  
        CreateVoucherChase( chaser_actor, chaser_pos_getter,
                            target_actor, target_pos_getter )
        CreateVoucherMoveTo( actor, actor_pos_getter, target_point)

        Later crowding info can be available. 
        """
        self.fn_visibles = fn_visibles
        self.points = [V2(tuple(p)) for p in points] 
        self.min_dist = {}
        self.adj = [] # adj[i] -> list of nodes directly reacheables from i 
        self._init_min_dist()
        self._floyd()
        #self.voucher_refs=

    def CreateVoucherChase( self, chaser_actor, target_actor, initial_wpt=None):
        """
        initial_wpt: if the spawn point is a waypoint, you can provide the
            waypoint to save cpu
        """
        target_pos = target.position # reemplazar por el miembro/method-call adecuado
        is_moving_target = True #maybe actor can have .is_steady_position
        voucher = Voucher(self, chaser_actor, start_pos,
                                target_actor, target_pos, is_moving_target) 
        #? register the voucher in self to track crowding ?
        return voucher

    def CreateVoucherMoveTo( self, actor, target_point, initial_waypoint=None, dest_waypoint=None):
        """
        initial_wpt: if the spawn point is a waypoint, you can provide the
            waypoint to save cpu
        dest_wpt: if the target would not move and is a waypoint and the index
            is known,  you can provide de wpt to save CPU. (then the param
            target_point will be set to points[dest_wpt] )
        """
        target_actor = None
        is_moving_target = False
        voucher = Voucher(self, actor, start_pos,
                                target_actor, target_point, is_moving_target) 
        #? register the voucher in self to track crowding ?
        return voucher
    
    def _init_min_dist(self):
        """
        builds the graph, joining those points with clear line of sight
        calcs the 1 step distance for each pair (bignum if not in sight)
        """
        points = self.points
        n = len(points)
        fn = self.fn_visible()
        m = self.min_dist
        adj_j = []
        for j in xrange(n):
            for i in xrange(n):
                if fn(i,j):
                    m[i,j] = abs(points[i]-points[j])
                    adj_j.append(i)
                else:
                    m[i,j] = m[j,i] = bignum
            self.adj.append(adj_j)

    def _floyd(self):
        """
        knowing the distance between adjacents, the Floyd-Warshalls algo
        calcs the min distance between any two pair of nodes. O(n^3)
        """
        n = len(self.points)
        m = self.min_dist        
        for k in xrange(n):
            for i in xrange(n):
                for j in xrange(n):
                    if ( m[i,k] + m[k,j] < m[i,j] ):
                        m[i,j] = m[i,k] + m[k,j]

    def _next_waypoint(i,j):
        """
        returns the next index in a minimal path from i to j , i if i==j
        """
        if i==j:
            return i
        dmin = self.min_dist[i,j]
        for k in self.adj[i]:
            # the first that allow min dist is as good as anyother
            if abs(dmin-(abs(self.points[i]-self.points[k])+self.min_dist[k,j]))<1.0e-4:
                return k
        #must not get there
        assert(0) #TODO: remove for release
        return i
                   
    def get_near_wps(self,a):
        if not isinstance(a,V2):
            a = V2(a[0],a[1])
        #get 3 ( if posible ) waypoints near a
        points = self.points
        lia = [(abs(a-p),i) for i,p in enumerate(points)]
        lia.sort()
        cnt = 0; candidates_a = []
        for d,i in lia:
            if self.fn_visibles(a, points[i]):
                candidates_a.append(i)
                cnt += 1
                if cnt>=3:
                    break
        return candidates_a
        if not len(candidates_a):
            print '*** WARNING: no waypoint near', a
            return a
        
    def best_pair(self, a, candidates_a, b, candidates_b):
        paths = []
        for i in candidates_a:
            for j in candidates_b:
                kpath = (abs(a-point[i])+self.min_dist[i,j]+abs(self.points[j]-b),
                         i,j)
                paths.append(kpath)
        path.sort()
        d, i, j = path[0]
        return d, i, j
        
    def get_dest(self, a, b):
        """
        for direct use without voucher, inneficient.
        returns a point visible from a, in a good (short) route to b
        Basically will head to b if visible or to a waypoint in a
        minimal path from waypoint A near a to Waypoint B near b
        """
        if not isinstance(a,V2):
            a = V2(a[0],a[1])
        if not isinstance(b,V2):
            b = V2(b[0],b[1])
        if self.fn_visibles(a,b):
            return b
        points = self.points

        #get 3 ( if posible ) waypoints near a
        candidates_a = self.get_near_wps(a)
        if not len(candidates_a):
            print '*** WARNING: no waypoint near', a
            return a

        #get 3 ( if posible ) waypoints near b
        candidates_b = self.get_near_wps(b)
        if not len(candidates_b):
            print '*** WARNING: no waypoint near', b
            return a

        #choose the best combo
        d, i, j = self.best_pair( a, candidates_a, b, candidates_b)
        
        #advance in the waypoint route to b while waypoint is visible
        while 1:
            last_visible = i
            i = self._next_waypoint(i,j)
            if self.fn_visibles(points[i],points[j]):
                break
        return points[last_visible]
        
class Voucher:
    """routing state. allows savings in get_dest."""
    def __init__(self, wpnav, chaser_actor, target_actor, target_pos,
                 steady_target, initial_waypoint, dest_waypoint, allow_direct_walk ):
        """
        services:
        .deviation() : distance to the planed path
        .get_dest() : point toward the actor must move to arrive at target
        
        state of possible interest:
        .comming : last position where a retarget was done
        .going : temporal target pos, usually a waypoint or target_actor last known position
        .going_wpt : if headed to a waypoint, the wpt index, else None
        .path_dist : distance along the path at the last retarget
        .ultimate_wpt : last wpt before reaching target
        .target_actor : None if not chasing, else the actor chased
        .target_pos : the ultimate target position
        """
        self.allow_direct_walk = True
        self.wpnav = wpnav
        self.steady_target = steady_target
        self.chaser_actor = chaser_actor
        self.target_actor = target_actor

        start_pos = chaser_actor.position # reemplazar por el miembro/method-call adecuado 
        self.comming = start_pos
        
        if initial_wpt is None:
            candidates_a = wpnav.get_near_wps(start_pos)
        else:
            candidates_a = [initial_wpt]
            
        if dest_wpt is None:
            candidates_b = wpnav.get_near_wps(target_pos)
        else:
            target_pos = wpnav.points[dest_wpt]
        self.target_pos = target_pos

        d,i,j = self.best_pair(a, candidates_a, b,candidates_b)
        self.path_dist = d
        self.going_wpt = i
        self.going = wpnav.points[i]
        self.ultimate_wpt = j    

    ##point to segment distance (dumbed down here to point to line) 
    ##http://www.codeguru.com/forum/showthread.php?t=194400
    ##Philip Nicoletti
    ##A= comming, B=going, C=apos
    def deviation(self):
            "distance from chaser to _line_ comming-going"
            apos = self.chaser_actor.position 
            if not isinstance(apos,V2):
                apos = V2(apos[0],apos[1])
            segl2 = (self.going-self.comming).magnitude_squared()
            if segl2<1.0e-3:
                return abs(apos-self.comming)
            #r = (apos-self.acomming).dot(self.going-self.comming)/segl2
            return abs((self.comming-apos).cross().dot(self.going-self.comming)/math.sqrt(segl2))
        
        
    def get_dest(self):
        return self.going

    def retarget_to_chase(new_target_actor,steady_actor=None):
        self.steady_actor = steady_actor
        if id(target_actor)==id(new_target_actor):
            return self.going
        self.target_actor = new_target_actor
        self.target_pos = new_target_actor.position
        #? fast, if time allow we recycle some info
        if ( self.allow_direct_walk
             and wpnav.fn_visibles(self.chaser_actor_position,self.target_actor)):
            self.going = self.target_actor
            self.visual_chase = True
            return self.going
        candidates_a = wpnav.get_near_wps(self.chaser_actor.position)
        candidates_b = wpnav.get_near_wps(self.target_pos)
        d,i,j = self.best_pair(self.chaser_actor_position, candidates_a, self.target_pos,candidates_b)
        self.path_dist = d
        self.going_wpt = i
        self.going = wpnav.points[i]
        self.ultimate_wpt = j
        self.visual_chase = False
        if ( abs(self.target_actor_position-self.chaser_position)<abs(self.going-self.chaser_position) and
             wpnav.fn_visibles(self.target_position, self.chaser_position)):
            self.going = self.target_position
            self.visual_chase = True
        return self.going

    def retarget_to_moveto(new_target_position, dest_wpt=None):
        self.steady_actor = steady_actor
        if id(target_actor)==id(new_target_actor):
            return
        self.target_actor = None
        #? provisional code, if time allow we recycle some info
        candidates_a = wpnav.get_near_wps(self.chaser_actor.position)
        if not (dest_wpt is None):
            self.target_pos = wpnav.points[dest_wpt]
            candidates_b = [dest_wpt]
        else:
            self.target_pos = new_target_position            
            candidates_b = wpnav.get_near_wps(self.target_pos)
        d,i,j = self.best_pair(self.chaser_actor_position, candidates_a, self.target_pos,candidates_b)
        self.path_dist = d
        self.going_wpt = i
        self.going = wpnav.points[i]
        self.ultimate_wpt = j
        return self.going


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
        return V2(v.x*math.cos(math.radians(45.0))-v.y*math.sin(math.radians(45.0)),
                  v.x*math.sin(math.radians(45.0))+v.y*math.cos(math.radians(45.0)))

    def translate3_5(v):
        return v+V2(3,5)
                               
            
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

if __name__ == '__main__':
    test_deviation()
