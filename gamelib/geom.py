import math
from math import hypot, pi, atan, cos, sin

def dist((x1,y1), (x2,y2)):
    return math.sqrt(
            (x2-x1)**2 +
            (y2-y1)**2
        )

def circle_intersect( (x0,y0,r0), (x1,y1,r1)):
    d = hypot( x1-x0, y1-y0 )
    if d >= r0+r1:
        angle = vector_angle( x1-x0, y1-y0 )
        nx = x0+cos( angle )*(r0)
        ny = y0+sin( angle )*(r0)
        return (nx, ny), (nx, ny)

    a = (r0**2 - r1**2 + d**2 ) / (2.0* d)
    h = math.sqrt( r0**2 - a**2 )
    x2 = x0 + a * ( x1 - x0 ) / d
    y2 = y0 + a * ( y1 - y0 ) / d

    nx1 = x2 + h * ( y1 - y0 ) / d
    ny1 = y2 - h * ( x1 - x0 ) / d

    nx2 = x2 - h * ( y1 - y0 ) / d
    ny2 = y2 + h * ( x1 - x0 ) / d

    return (nx1, ny1), (nx2, ny2)

def vector_angle(x,y):
    if x == 0:
        if y > 0:
            return pi/2
        elif (y < 0):
            return -pi/2;
        else:
            return 0
    elif y == 0:
        if x > 0:
            return 0
        else:
            return pi
    else:
        if x < 0:
            if y > 0:
                return atan(y/float(x)) + pi
            else:
                return atan(y / x) - pi
        else:
            return atan( y/float(x) )


def dist_point_to_line((px,py), (x1,y1), (x2, y2)):
    dx = x2-x1
    dy = y2-y1
    t = ((px - x1) * dx + (py - y1) * dy) / float (dx * dx + dy * dy)
    if t > 1:
        return -1
    elif t < 0:
        return -1
    else:
        nx = x1 + t*dx
        ny = y1 + t*dy
        return dist((px,py), (nx, ny))


def angle_between((px1,py1), (px2, py2)):
    angle1 = vector_angle(px1, py1)
    angle2 = vector_angle(px2, py2)
    return angle_rotation(angle1, angle2)

def angle_rotation(angle1, angle2):
    if angle1<angle2:
        if angle1+pi>angle2:
            delta = angle2-angle1
        else:
            delta = -(2*pi+angle1-angle2)
    else:
        if angle1-pi<angle2:
            delta = -(angle1-angle2)
        else:
            delta = 2*pi+angle2-angle1
    return delta

def dist_point_to_segment((px,py), (x1,y1), (x2, y2)):
    dx = x2-x1
    dy = y2-y1
    t = ((px - x1) * dx + (py - y1) * dy) / float (dx * dx + dy * dy)
    if t > 1:
        return dist((px,py),(x2,y2))
    elif t < 0:
        return dist((px,py),(x1,y1))
    else:
        nx = x1 + t*dx
        ny = y1 + t*dy
        return dist((px,py), (nx, ny))
