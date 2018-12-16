# -*- coding: utf-8 -*-

"""
***************************************************************************
    geometryUtils.py
    ---------------------
    Date                 : December 2018
    Copyright            : (C) 2018 by Anita Graser
    Email                : anitagraser@gmx.at
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from math import sin, cos, atan2, radians, degrees, asin, sqrt, ceil, log, tan, pi
from shapely.geometry import Point


R_EARTH = 6371000  # radius of earth in meters

def measure_distance_spherical(point1, point2):
    if (type(point1) != Point) or (type(point2) != Point):
        raise TypeError("Only Points are supported as arguments")
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
    if (type(point1) != Point) or (type(point2) != Point):
        raise TypeError("Only Points are supported as arguments")
    return point1.distance(point2)
 
def calculate_initial_compass_bearing(point1, point2):
    """
    Calculates the bearing between two points.
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
    if (type(point1) != Point) or (type(point2) != Point):
        raise TypeError("Only Points are supported as arguments")
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
    Calculates euclidean bearing of line between two points
    """
    if (type(point1) != Point) or (type(point2) != Point):
        raise TypeError("Only Points are supported as arguments")
        
    angle = atan2(point2.x - point1.x, point2.y - point1.y) 
    azimuth = degrees(angle)    
    if angle < 0:
        azimuth += 360
    #print("{}->{}: angle={} azimuth={}".format(point1, point2, angle, azimuth))
    return azimuth

def angular_difference(degrees1, degrees2):
    """
    Calculates the smaller angle between the provided bearings / headings
    """
    diff = abs(degrees1 - degrees2)
    if diff > 180:
        diff = abs(diff - 360)
    return diff 
    
    
    