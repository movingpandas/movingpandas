# -*- coding: utf-8 -*-

from copy import copy
from shapely.geometry import LineString, Point
import pandas as pd

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import measure_distance


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
        self.traj_col_name = traj.get_geom_col()

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
        prev_pt = temp_df.iloc[0][traj.get_geom_col()]
        keep_rows = [0]
        for i, pt in enumerate(temp_df[traj.get_geom_col()]):
            dist = measure_distance(pt, prev_pt, traj.is_latlon)
            if dist >= tolerance:
                keep_rows.append(i)
                prev_pt = pt

        keep_rows.append(len(traj.df) - 1)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id, traj_id_col=traj.get_traj_id_col())
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
        prev_t = temp_df["t"].iat[0]
        keep_rows = [0]

        for i, (_, row) in enumerate(temp_df.iterrows()):
            t = row["t"]
            tdiff = t - prev_t
            if tdiff >= tolerance:
                keep_rows.append(i)
                prev_t = t

        keep_rows.append(len(traj.df) - 1)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id, traj_id_col=traj.get_traj_id_col())
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
        keep_rows = [0]
        i = 0

        for current_pt in traj.df[traj.get_geom_col()]:
            if prev_pt is None:
                prev_pt = current_pt
            else:
                line = LineString([prev_pt, current_pt])
                if any(line.distance(pt) > tolerance for pt in pts):
                    prev_pt = current_pt
                    pts.clear()
                    keep_rows.append(i)
                pts.append(current_pt)
                i += 1

        keep_rows.append(i)
        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id, traj_id_col=traj.get_traj_id_col())
        return new_traj


class DouglasPeuckerGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes using Douglas-Peucker algorithm (as implemented in shapely/Geos).

    tolerance : float
        Distance tolerance in trajectory CRS units

    References
    ----------
    * Douglas, D., & Peucker, T. (1973). Algorithms for the reduction of the number
      of points required to represent a digitized line or its caricature.
      The Canadian Cartographer 10(2), 112–122. doi:10.3138/FM57-6770-U75U-7727.

    Examples
    --------

    >>> mpd.DouglasPeuckerGeneralizer(traj).generalize(tolerance=1.0)
    """

    def _generalize_traj(self, traj, tolerance):
        keep_rows = []
        simplified = (
            traj.to_linestring().simplify(tolerance, preserve_topology=False).coords
        )

        for i, current_pt in enumerate(traj.df[traj.get_geom_col()]):
            if current_pt.coords[0] in simplified:
                keep_rows.append(i)

        new_df = traj.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, traj.id, traj_id_col=traj.get_traj_id_col())
        return new_traj


class TopDownTimeRatioGeneralizer(TrajectoryGeneralizer):
    """
    Generalizes using Top-Down Time Ratio algorithm proposed by Meratnia & de By (2004).

    This is a spatiotemporal trajectory generalization algorithm. Where Douglas-Peucker
    simply measures the spatial distance between points and original line geometry,
    Top-Down Time Ratio (TDTR) measures the distance between points and their
    spatiotemporal projection on the trajectory. These projections are calculated based
    on the ratio of travel times between the segment start and end times and the point
    time.

    tolerance : float
        Distance tolerance (distance returned by shapely Point.distance function)

    References
    ----------
    * Meratnia, N., & de By, R.A. (2004). Spatiotemporal compression techniques for
      moving point objects. In International Conference on Extending Database Technology
      (pp. 765-782). Springer, Berlin, Heidelberg.

    Examples
    --------

    >>> mpd.TopDownTimeRatioGeneralizer(traj).generalize(tolerance=1.0)
    """

    def _generalize_traj(self, traj, tolerance):
        generalized = self.td_tr(traj.df.copy(), tolerance)
        return Trajectory(generalized, traj.id, traj_id_col=traj.get_traj_id_col())

    def td_tr(self, df, tolerance):
        if len(df) <= 2:
            return df
        else:
            de = (
                df.index.max().to_pydatetime() - df.index.min().to_pydatetime()
            ).total_seconds()

            t0 = df.index.min().to_pydatetime()

            pt0 = df[self.traj_col_name].iloc[0]
            ptn = df[self.traj_col_name].iloc[-1]

            dx = ptn.x - pt0.x
            dy = ptn.y - pt0.y

            dists = df.apply(
                lambda rec: self._dist_from_calced(rec, t0, pt0, de, dx, dy),
                axis=1,
            )

            if dists.max() > tolerance:
                return pd.concat(
                    [
                        self.td_tr(
                            df.iloc[: df.index.get_loc(dists.idxmax()) + 1], tolerance
                        ),
                        self.td_tr(
                            df.iloc[df.index.get_loc(dists.idxmax()) :], tolerance
                        ),
                    ]
                )
            else:
                return df.iloc[[0, -1]]

    def _dist_from_calced(self, rec, start_t, start_geom, de, dx, dy):
        di = (rec.name - start_t).total_seconds()
        calced = Point(start_geom.x + dx * di / de, start_geom.y + dy * di / de)
        return rec[self.traj_col_name].distance(calced)
