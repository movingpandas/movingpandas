# -*- coding: utf-8 -*-

from shapely.geometry import Point
from datetime import datetime


class TemporalRange:
    def __init__(self, t_0, t_n):
        self.t_0 = t_0
        self.t_n = t_n


class SpatioTemporalRange:
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


class TemporalRangeWithTrajId:
    def __init__(self, t_0, t_n, traj_id):
        self.t_0 = t_0
        self.t_n = t_n
        self.traj_id = traj_id

    def __str__(self):
        dt = self.t_n - self.t_0
        return f"Traj {self.traj_id}: {self.t_0} - {self.t_n} (duration: {dt})"
