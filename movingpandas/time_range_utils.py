# -*- coding: utf-8 -*-


class TemporalRange:
    def __init__(self, t_0, t_n):
        self.t_0 = t_0
        self.t_n = t_n


class SpatioTemporalRange:
    def __init__(self, pt_0, pt_n, t_0, t_n):
        self.pt_0 = pt_0
        self.pt_n = pt_n
        self.t_0 = t_0
        self.t_n = t_n


class TemporalRangeWithTrajId:
    def __init__(self, t_0, t_n, traj_id):
        self.t_0 = t_0
        self.t_n = t_n
        self.traj_id = traj_id
