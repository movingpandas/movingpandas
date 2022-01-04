# -*- coding: utf-8 -*-

from copy import copy
from shapely.geometry import LineString, Point
import pandas as pd

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import measure_distance_geodesic, measure_distance_euclidean


class TrajectoryGeneralizer:
    """
    Generalizer base class
    """

    def __init__(self, traj):
        """
        Create TrajectoryGeneralizer

        Parameters
        ----------
        traj : Trajectory or TrajectoryCollection
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

    This generalization ensures that consecutive locations are at least a
    certain distance apart.

    Distance is calculated using CRS units, except if the CRS is geographic
    (e.g. EPSG:4326 WGS84) then distance is calculated in metres.

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
                dist = measure_distance_geodesic(pt, prev_pt)
            else:
                dist = measure_distance_euclidean(pt, prev_pt)
            if dist >= tolerance:
                keep_rows.append(i)
                prev_pt = pt
            i += 1

        keep_rows.append(len(traj.df) - 1)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id)
        return new_traj


class MinTimeDeltaGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes based on time.

    This generalization ensures that consecutive rows are at least a certain
    timedelta apart.

    tolerance : datetime.timedelta
        Desired minimum time difference between consecutive rows

    Examples
    --------

    >>> mpd.MinTimeDeltaGeneralizer(traj).generalize(tolerance=timedelta(minutes=10))
    """

    def _generalize_traj(self, traj, tolerance):
        temp_df = traj.df.copy()
        temp_df["t"] = temp_df.index
        prev_t = temp_df.head(1)["t"][0]
        keep_rows = [0]
        i = 0

        for index, row in temp_df.iterrows():
            t = row["t"]
            tdiff = t - prev_t
            if tdiff >= tolerance:
                keep_rows.append(i)
                prev_t = t
            i += 1

        keep_rows.append(len(traj.df) - 1)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id)
        return new_traj


class MaxDistanceGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes based on distance.

    Similar to Douglas-Peuker. Single-pass implementation that checks whether
    the provided distance threshold is exceed.

    tolerance : float
        Distance tolerance in trajectory CRS units

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
    Generalizes using Douglas-Peucker algorithm (as implemented in shapely/Geos).

    tolerance : float
        Distance tolerance in trajectory CRS units

    Examples
    --------

    >>> mpd.DouglasPeuckerGeneralizer(traj).generalize(tolerance=1.0)
    """

    def _generalize_traj(self, traj, tolerance):
        keep_rows = []
        i = 0
        simplified = (
            traj.to_linestring().simplify(tolerance, preserve_topology=False).coords
        )

        for index, row in traj.df.iterrows():
            current_pt = row[traj.get_geom_column_name()]
            if current_pt.coords[0] in simplified:
                keep_rows.append(i)
            i += 1

        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id)
        return new_traj


class TopDownTimeRatioGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes using Top-Down Time Ratio algorithm proposed by Meratnia and De By (DOI: 10.1007/978-3-540-24741-8_44).

    Points are projected on the line that connects the starting point SP with the end point EP of the trajectory. These projections are
    calculated based on the ratios de and di that correspond to the travel time from SP to P and from P to EP respectively. Iterativelly,
    when the furthest point P is found (granted its distance is greater that the tolerance), that point is kept and the process is
    repeated for the two trajectories that are defined as follows: (SP,P) and (P,EP). The process is stopped when any indivudiual 
    subtrajectory is small enough (len<=2). 

    tolerance : float
        Distance tolerance (distance returned by shapely Point.distance function)

    Examples
    --------

    >>> mpd.TopDownTimeRatioGeneralizer(traj).generalize(tolerance=1.0)
    """

    def _generalize_traj(self, traj, tolerance):
        return Trajectory(self.td_tr(traj.df.copy(), tolerance), traj.id)
        
    def td_tr(self, df, tolerance):
        if len(df)<=2:
            return df
        else:
            de = (df.index.max().to_pydatetime() - df.index.min().to_pydatetime()).total_seconds()
            
            dx = df.geometry.iloc[-1].x - df.geometry.iloc[0].x
            dy = df.geometry.iloc[-1].y - df.geometry.iloc[0].y

            dists = df.apply(lambda rec: self._dist_from_calced(rec, df.index.min().to_pydatetime(), df.geometry.iloc[0], de, dx, dy), axis=1) 

            if dists.max()>tolerance:
                return pd.concat([self.td_tr(df.iloc[:df.index.get_loc(dists.idxmax())+1], tolerance), self.td_tr(df.iloc[df.index.get_loc(dists.idxmax()):], tolerance)])
            else:
                return df.iloc[[0,-1]]
    
    def _dist_from_calced(self, rec, start_t, start_geom, de, dx, dy):
        di = (rec.name - start_t).total_seconds()
        calced = Point(start_geom.x + dx * di / de, start_geom.y + dy * di / de)
        return rec.geometry.distance(calced)
