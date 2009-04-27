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
from cocos.euclid import Vector2 as V2

bignum = 1.0e+40
print bignum

class WaypointNav:
    def __init__(self,points,fn_visibles):
        """
        points: waypoints; all points in the map should have at least uone waypoint in sight
        fn_visibles(a,b) True if point b is visible from point a
        Interfase:
        .get_dest(a,b): give a good intermediate point for going from a to b
        """
        self.fn_visibles = fn_visibles
        self.points = [V2(tuple(p)) for p in points] 
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
                   

    def get_dest(self, a, b):
        """
        returns a point visible from a, in a good (short) route to b
        Basically will head to b if visible or to a waypoint in a
        minimal path from a waypoint A near a to a Waypoint B near b
        """
        if not isinstance(a,V2):
            a = V2(a[0],a[1])
        if not isinstance(b,V2):
            a = V2(b[0],b[1])
        if self.fn_visibles(a,b):
            return b
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
        if not len(candidates_a):
            print '*** WARNING: no waypoint near', a
            return a

        #get 3 ( if posible ) waypoints near b
        points = self.points
        lia = [(abs(b-p),i) for i,p in enumerate(points)]
        lia.sort()
        cnt = 0; candidates_b = []
        for d,i in lia:
            if self.fn_visibles(b, points[i]):
                candidates_b.append(i)
                cnt += 1
                if cnt>=3:
                    break
        if not len(candidates_b):
            print '*** WARNING: no waypoint near', b
            return a

        #choose the best combo
        paths = []
        for i in candidates_a:
            for j in candidates_b:
                kpath = (abs(a-point[i])+self.min_dist[i,j]+abs(points[j]-b),
                         i,j)
                paths.append(kpath)
        path.sort()
        d, i, j = path[0]

        #advance in the waypoint route to b while waypoint is visible
        while 1:
            last_visible = i
            i = self._next_waypoint(i,j)
            if self.fn_visibles(points[i],points[j]):
                break
        return points[last_visible]
    
            
        
        
        
        
