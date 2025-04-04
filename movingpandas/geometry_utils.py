# -*- coding: utf-8 -*-

from math import atan2, cos, degrees, pi, radians, sin, sqrt

import shapely
from geopy import distance
from geopy.distance import geodesic
from packaging.version import Version
from shapely.geometry import LineString, Point

from movingpandas.tools._warnings import deprecated

try:
    SHAPELY_GE_2 = Version(shapely.__version__) >= Version("2.0.0")
except TypeError:
    SHAPELY_GE_2 = False

R_EARTH = 6371000  # radius of earth in meters
C_EARTH = 2 * R_EARTH * pi  # circumference


def _is_point(input):
    if not isinstance(input, Point):
        raise TypeError(
            f"Only Points are supported as arguments, got {input} {type(input)}"
        )


@deprecated
def measure_distance_spherical(point1, point2):
    """
    Return spherical distance between two shapely Points as a float.
    """
    _is_point(point1)
    _is_point(point2)
    lon1 = float(point1.x)
    lon2 = float(point2.x)
    lat1 = float(point1.y)
    lat2 = float(point2.y)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    a = sin(delta_lat / 2) * sin(delta_lat / 2) + cos(radians(lat1)) * cos(
        radians(lat2)
    ) * sin(delta_lon / 2) * sin(delta_lon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    dist = R_EARTH * c
    return dist


def measure_distance_euclidean(point1, point2):
    """
    Return euclidean distance between two shapely Points as float.
    """
    _is_point(point1)
    _is_point(point2)
    return point1.distance(point2)


def measure_distance_geodesic(point1, point2):
    """
    This function calculates the geodesic distance between two points
    as a float of (SI) unit meters.

    Parameters
    ----------
    point1 : shapely.geometry.Point
        point object containing latitude / longitude defining a starting location
    point2 : shapely.geometry.Point
        object containing latitude / longitude defining a termination location

    Returns
    -------
    dist : float
        geodesic distance (on a WGS84 ellipsoid) in meters
    """
    _is_point(point1)
    _is_point(point2)
    lon1 = float(point1.x)
    lon2 = float(point2.x)
    lat1 = float(point1.y)
    lat2 = float(point2.y)
    dist = distance.distance(
        (lat1, lon1), (lat2, lon2)
    ).meters  # uses geodesic dist and defaults to WGS84
    return dist


def measure_distance(point1, point2, geodesic=False, conversion=None):
    """
    Convenience function that returns either euclidean or geodesic distance
    between two points
    """
    if geodesic:
        d = measure_distance_geodesic(point1, point2)
    else:
        d = measure_distance_euclidean(point1, point2)
    if conversion:
        d = d * conversion.crs / conversion.distance
    return d


def measure_distance_line(linestring, other, conversion):
    """
    Returns the euclidean distance between a linestring and other geometry
    """
    d = linestring.distance(other)
    return d / conversion.distance


def measure_length(geoseries, spherical=False, conversion=None):
    """
    Returns the total distance between the points of the geoseries
    """
    pt_tuples = [(pt.y, pt.x) for pt in geoseries.tolist()]
    if spherical:
        length = geodesic(*pt_tuples).m
    else:  # The following distance will be in CRS units that might not be meters!
        length = LineString(pt_tuples).length

    if conversion:
        length = length / conversion.distance

    return length


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
    _is_point(point1)
    _is_point(point2)
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
    _is_point(point1)
    _is_point(point2)
    angle = atan2(point2.x - point1.x, point2.y - point1.y)
    azimuth = degrees(angle)
    if angle < 0:
        azimuth += 360
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
    Calculate the length of the diagonal of the minimum rotated rectangle of
    the input geometry.
    """
    if isinstance(geom, Point):
        return 0
    _geom = geom.geoms if SHAPELY_GE_2 else geom
    if len(_geom) == 2:
        return measure_distance(_geom[0], _geom[1], spherical)
    mrr = geom.minimum_rotated_rectangle
    try:  # usually mrr is a Polygon
        x, y = mrr.exterior.coords.xy
    except AttributeError:  # thrown if mrr is a LineString
        return measure_distance(Point(mrr.coords[0]), Point(mrr.coords[-1]), spherical)
    return measure_distance(Point(x[0], y[0]), Point(x[2], y[2]), spherical)


def point_gdf_to_linestring(df, geom_col_name):
    """
    Convert GeoDataFrame of Points to shapely LineString
    """
    if len(df) > 1:
        return LineString(df[geom_col_name].tolist())
    else:
        raise RuntimeError("DataFrame needs at least two points to make line!")
