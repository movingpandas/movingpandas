# -*- coding: utf-8 -*-

from copy import copy
from shapely.geometry import LineString

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import measure_distance_spherical, measure_distance_euclidean


class TrajectoryGeneralizer:
    """
    Class for generalizing Trajectories and TrajectoryCollections
    """

    @staticmethod
    def generalize(traj, mode, tolerance):
        """
        Generalize the input Trajectory/TrajectoryCollection.

        Supported generalization modes are:

        * 'douglas-peucker' (tolerance as float in CRS units or meters if CRS is geographic, e.g. EPSG:4326 WGS84)
        * 'min-time-delta' (tolerance as datetime.timedelta)
        * 'min-distance' (tolerance as float in CRS units or meters if CRS is geographic, e.g. EPSG:4326 WGS84)

        Parameters
        ----------
        mode : str
            Generalization mode
        tolerance : any type
            Tolerance threshold, differs by generalization mode

        Returns
        -------
        Trajectory/TrajectoryCollection
            Generalized Trajectory or TrajectoryCollection
        """

        if isinstance(traj, Trajectory):
            return TrajectoryGeneralizer._generalize_traj(traj, mode, tolerance)
        elif isinstance(traj, TrajectoryCollection):
            return TrajectoryGeneralizer._generalize_traj_collection(traj, mode, tolerance)
        else:
            raise TypeError

    @staticmethod
    def _generalize_traj_collection(traj_collection, mode, tolerance):
        generalized = []
        for traj in traj_collection.trajectories:
            generalized.append(TrajectoryGeneralizer._generalize_traj(traj, mode, tolerance))
        result = copy(traj_collection)
        result.trajectories = generalized
        return result

    @staticmethod
    def _generalize_traj(traj, mode, tolerance):
        if mode == 'douglas-peucker':
            return TrajectoryGeneralizer._douglas_peucker(traj, tolerance)
        elif mode == 'min-time-delta':
            return TrajectoryGeneralizer._min_time_delta(traj, tolerance)
        elif mode == 'min-distance':
            return TrajectoryGeneralizer._min_distance(traj, tolerance)
        else:
            raise ValueError('Invalid generalization mode {}. Must be one of [douglas-peucker, min-time-delta, min-distance]'.format(mode))

    @staticmethod
    def _min_distance(traj, tolerance):
        """
        Generalize the trajectory based on distance.

        This generalization ensures that consecutive locations are at least a certain distance apart.

        Parameters
        ----------
        tolerance : float
            Desired minimum distance between consecutive points

        Returns
        -------
        Trajectory
            Generalized trajectory
        """
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

    @staticmethod
    def _min_time_delta(traj, tolerance):
        """
        Generalize the trajectory based on time.

        This generalization ensures that consecutive rows are at least a certain timedelta apart.

        Parameters
        ----------
        tolerance : datetime.timedelta
            Desired minimum time difference between consecutive rows

        Returns
        -------
        Trajectory
            Generalized trajectory
        """
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

    @staticmethod
    def _douglas_peucker(traj, tolerance):
        """
        Generalize the trajectory using Douglas-Peucker algorithm.

        Parameters
        ----------
        tolerance : float
            Distance tolerance

        Returns
        -------
        Trajectory
            Generalized trajectory
        """
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
