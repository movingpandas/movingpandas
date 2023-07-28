from shapely.geometry import Point
from datetime import datetime
from .geometry_utils import measure_distance


class TPoint:
    """
    Temporal point
    """

    def __init__(self, t, pt) -> None:
        self.t = t
        self.pt = pt


class TRange:
    """
    Temporal range
    """

    def __init__(self, t_0, t_n):
        self.t_0 = t_0
        self.t_n = t_n


class STRange:
    """
    Spatiotemporal range
    """

    def __init__(self, pt_0, pt_n, t_0, t_n):
        if isinstance(type(pt_0), Point):
            raise TypeError("Input pt_0 has to be a shapely.geometry.Point!")
        if isinstance(type(pt_n), Point):
            raise TypeError("Input pt_n has to be a shapely.geometry.Point!")
        if isinstance(type(t_0), datetime):
            raise TypeError("Input t_0 has to be a datetime.datetime!")
        if isinstance(type(t_n), datetime):
            raise TypeError("Input t_n has to be a datetime.datetime!")
        self.pt_0 = pt_0
        self.pt_n = pt_n
        self.t_0 = t_0
        self.t_n = t_n


class TRangeWithTrajId:
    def __init__(self, t_0, t_n, traj_id):
        self.t_0 = t_0
        self.t_n = t_n
        self.traj_id = traj_id

    def __str__(self):
        dt = self.t_n - self.t_0
        return f"Traj {self.traj_id}: {self.t_0} - {self.t_n} (duration: {dt})"


def get_speed(tpt0, tpt1, is_latlon, conversion):
    d = measure_distance(tpt0.pt, tpt1.pt, is_latlon)
    d = d * conversion.crs / conversion.distance
    v = d / (tpt1.t - tpt0.t).total_seconds() * conversion.time
    return v


def get_speed2(pt0, pt1, delta_t, is_latlon, conversion):
    d = measure_distance(pt0, pt1, is_latlon)
    d = d * conversion.crs / conversion.distance
    v = d / delta_t.total_seconds() * conversion.time
    return v
