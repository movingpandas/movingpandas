# -*- coding: utf-8 -*-

from copy import copy
from shapely.geometry import LineString

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import measure_distance_spherical, measure_distance_euclidean


class TrajectoryGeneralizer:
    """
    Generalizer base class
    """
    def __init__(self, traj):
        """
        Create TrajectoryGeneralizer

        Parameters
        ----------
        traj : Trajectory/TrajectoryCollection
        """
        self.traj = traj

    def generalize(self, tolerance):
        """
        Generalize the input Trajectory/TrajectoryCollection.

        Parameters
        ----------
        tolerance : any type
            Tolerance threshold, differs by generalizer

        Returns
        -------
        Trajectory/TrajectoryCollection
            Generalized Trajectory or TrajectoryCollection
        """
        if isinstance(self.traj, Trajectory):
            return self._generalize_traj(self.traj, tolerance)
        elif isinstance(self.traj, TrajectoryCollection):
            return self._generalize_traj_collection(tolerance)
        else:
            raise TypeError

    def _generalize_traj_collection(self, tolerance):
        generalized = []
        for traj in self.traj:
            generalized.append(self._generalize_traj(traj, tolerance))
        result = copy(self.traj)
        result.trajectories = generalized
        return result

    def _generalize_traj(self, traj, tolerance):
        return traj


class MinDistanceGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes based on distance.

    This generalization ensures that consecutive locations are at least a certain distance apart.

    tolerance : float
        Desired minimum distance between consecutive points

    Examples
    --------

    >>> mpd.MinDistanceGeneralizer(traj).generalize(tolerance=1.0)
    """

    def _generalize_traj(self, traj, tolerance):
        temp_df = traj.df.copy()
        prev_pt = temp_df.iloc[0][traj.get_geom_column_name()]
        keep_rows = [0]
        i = 0

        for index, row in temp_df.iterrows():
            pt = row[traj.get_geom_column_name()]
            if traj.is_latlon:
                dist = measure_distance_spherical(pt, prev_pt)
            else:
                dist = measure_distance_euclidean(pt, prev_pt)
            if dist >= tolerance:
                keep_rows.append(i)
                prev_pt = pt
            i += 1

        keep_rows.append(len(traj.df)-1)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id)
        return new_traj


class MinTimeDeltaGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes based on time.

    This generalization ensures that consecutive rows are at least a certain timedelta apart.

    tolerance : datetime.timedelta
        Desired minimum time difference between consecutive rows

    Examples
    --------

    >>> mpd.MinTimeDeltaGeneralizer(traj).generalize(tolerance=timedelta(minutes=10))
    """

    def _generalize_traj(self, traj, tolerance):
        temp_df = traj.df.copy()
        temp_df['t'] = temp_df.index
        prev_t = temp_df.head(1)['t'][0]
        keep_rows = [0]
        i = 0

        for index, row in temp_df.iterrows():
            t = row['t']
            tdiff = t - prev_t
            if tdiff >= tolerance:
                keep_rows.append(i)
                prev_t = t
            i += 1

        keep_rows.append(len(traj.df)-1)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id)
        return new_traj


class MaxDistanceGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes based on distance.

    Similar to Douglas-Peuker. Single-pass implementation that checks whether the provided distance threshold
    is exceed.

    tolerance : float
        Distance tolerance

    Examples
    --------

    >>> mpd.MaxDistanceGeneralizer(traj).generalize(tolerance=1.0)
    """

    def _generalize_traj(self, traj, tolerance):
        prev_pt = None
        pts = []
        keep_rows = []
        i = 0

        for index, row in traj.df.iterrows():
            current_pt = row[traj.get_geom_column_name()]
            if prev_pt is None:
                prev_pt = current_pt
                keep_rows.append(i)
                continue
            line = LineString([prev_pt, current_pt])
            for pt in pts:
                if line.distance(pt) > tolerance:
                    prev_pt = current_pt
                    pts = []
                    keep_rows.append(i)
                    continue
            pts.append(current_pt)
            i += 1

        keep_rows.append(i)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id)
        return new_traj


class DouglasPeuckerGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes using Douglas-Peucker algorithm.

    tolerance : float
        Distance tolerance

    Examples
    --------

    >>> mpd.DouglasPeuckerGeneralizer(traj).generalize(tolerance=1.0)
    """

    def _generalize_traj(self, traj, tolerance):
        keep_rows = []
        i = 0
        simplified = traj.to_linestring().simplify(tolerance).coords

        for index, row in traj.df.iterrows():
            current_pt = row[traj.get_geom_column_name()]
            if current_pt.coords[0] in simplified:
                keep_rows.append(i)
            i += 1

        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id)
        return new_traj
