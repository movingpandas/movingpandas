# -*- coding: utf-8 -*-

from math import sin, cos, atan2, radians, degrees, sqrt, pi
from shapely.geometry import Point, LineString
from geopy import distance


R_EARTH = 6371000  # radius of earth in meters
C_EARTH = 2 * R_EARTH * pi  # circumference


def measure_distance_spherical(point1, point2):
    """
    Return spherical distance between two shapely Points as a float.
    """
    if (type(point1) != Point) or (type(point2) != Point):
        raise TypeError("Only Points are supported as arguments, got {} and {}".format(point1, point2))
    lon1 = float(point1.x)
    lon2 = float(point2.x)
    lat1 = float(point1.y)
    lat2 = float(point2.y)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = sin(delta_lat/2) * sin(delta_lat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lon/2) * sin(delta_lon/2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    dist = R_EARTH * c
    return dist


def measure_distance_euclidean(point1, point2):
    """
    Return euclidean distance between two shapely Points as float.
    """
    if (not isinstance(point1, Point)) or (not isinstance(point2, Point)):
        raise TypeError("Only Points are supported as arguments, got {} and {}".format(point1, point2))
    return point1.distance(point2)

def measure_distance_geodesic(point1, point2):
    """
    Return the geodesic distance between two points as a float of (SI) unit meters.
    """
    if (type(point1) != Point) or (type(point2) != Point):
        raise TypeError("Only Points are supported as arguments, got {} and {}".format(point1, point2))
    lon1 = float(point1.x)
    lon2 = float(point2.x)
    lat1 = float(point1.y)
    lat2 = float(point2.y)
    dist = distance.distance((lat1,lon1), (lat2,lon2)).meters #uses geodesic dist and defaults to WGS84
    return dist


def _measure_distance(point1, point2, spherical=False):
    """
    Convenience function that returns either euclidean or spherical distance between two points
    """
    if spherical:
        return measure_distance_spherical(point1, point2)
    else:
        return measure_distance_geodesic(point1, point2)


def calculate_initial_compass_bearing(point1, point2):
    """
    Calculate the bearing between two points.

    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `point1: shapely Point
      - `point2: shapely Point
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (not isinstance(point1, Point)) or (not isinstance(point2, Point)):
        raise TypeError("Only Points are supported as arguments, got {} and {}".format(point1, point2))
    lat1 = radians(point1.y)
    lat2 = radians(point2.y)
    delta_lon = radians(point2.x - point1.x)
    x = sin(delta_lon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - (sin(lat1) * cos(lat2) * cos(delta_lon))
    initial_bearing = atan2(x, y)
    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


def azimuth(point1, point2):
    """
    Calculates euclidean bearing of line between two points.
    """
    if (not isinstance(point1, Point)) or (not isinstance(point2, Point)):
        raise TypeError("Only Points are supported as arguments, got {} and {}".format(point1, point2))
        
    angle = atan2(point2.x - point1.x, point2.y - point1.y) 
    azimuth = degrees(angle)    
    if angle < 0:
        azimuth += 360
    #print("{}->{}: angle={} azimuth={}".format(point1, point2, angle, azimuth))
    return azimuth


def angular_difference(degrees1, degrees2):
    """
    Calculates the smaller angle between the provided bearings / headings.
    """
    diff = abs(degrees1 - degrees2)
    if diff > 180:
        diff = abs(diff - 360)
    return diff 


def mrr_diagonal(geom, spherical=False):
    """
    Calculate the length of the diagonal of the minimum rotated rectangle of the input geometry.
    """
    if len(geom) == 1:
        return 0
    if len(geom) == 2:
        return _measure_distance(geom[0], geom[1], spherical)
    mrr = LineString(geom).minimum_rotated_rectangle
    try:  # usually mrr is a Polygon
        x, y = mrr.exterior.coords.xy
    except AttributeError:  # thrown if mrr is a LineString
        return _measure_distance(Point(mrr.coords[0]), Point(mrr.coords[-1], spherical))
    return _measure_distance(Point(x[0], y[0]), Point(x[2], y[2]), spherical)
