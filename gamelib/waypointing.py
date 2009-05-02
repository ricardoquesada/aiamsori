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
        self.points = [V2(x,y) for x,y in points]
        self.min_dist = {}
        self.adj = [] # adj[i] -> list of nodes directly reacheables from i
        self._init_min_dist()
        self._floyd()


    def _init_min_dist(self):
        """
        builds the graph, joining those points with clear line of sight
        calcs the 1 step distance for each pair (bignum if not in sight)
        """
        points = self.points
        n = len(points)
        fn = self.fn_visibles
        m = self.min_dist
        for j in xrange(n):
            adj_j = []
            for i in xrange(n):
                if i==j:
                    m[i,j]=0
                    continue
                ix0, jx0 = i,j
                if fn(points[i],points[j]):
                    ix1, jx1 = i,j
                    assert((points[ix0]==points[ix1]) and
                           (points[jx0]==points[jx1]))
                    m[i,j] =  abs(points[i]-points[j])
                    adj_j.append(i)
                else:
                    m[i,j] = bignum
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

    def _next_waypoint(self,i,j):
        """
        returns the next index in a minimal path from i to j , i if i==j
        """
        if i==j:
            print "last node"
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
                if cnt>=1:
                    break
        return candidates_a
        if not len(candidates_a):
            #print '*** WARNING: no waypoint near', a
            return a

    def best_pair(self, a, candidates_a, b, candidates_b):

        paths = []
        for i in candidates_a:
            for j in candidates_b:
                kpath = (abs(a-self.points[i])+self.min_dist[i,j]+abs(self.points[j]-b),
                         i,j)
                paths.append(kpath)
        paths.sort()
        d, i, j = paths[0]
        return d, i, j

    def get_path(self, a, b):
        a = self.points.index(a)
        b = self.points.index(b)
        return self.get_path_indexed(self, a, b)

    def get_path_indexed(self, a, b):
        path = []
        path.append(a)
        while 1:
            a = self._next_waypoint(a,b)
            path.append(a)
            if a == b:
                break

        return path

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
            print '*** WARNING: no waypoint near SOURCE', a
            return b
        print "first", candidates_a
        #get 3 ( if posible ) waypoints near b
        candidates_b = self.get_near_wps(b)
        if not len(candidates_b):
            print '*** WARNING: no waypoint near GOAL', b
            return b

        #choose the best combo
        d, i, j = self.best_pair( a, candidates_a, b, candidates_b)
        #advance in the waypoint route to b while waypoint is visible
        while 1:
            last_visible = i
            i = self._next_waypoint(i,j)
            if not self.fn_visibles(a,points[i]):
                break
            if i == j:
                break
        return points[last_visible]
