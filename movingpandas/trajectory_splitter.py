# -*- coding: utf-8 -*-

from copy import copy
from pandas import Grouper
from shapely.geometry import LineString

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import measure_distance_spherical, measure_distance_euclidean


class TrajectorySplitter:
    """
    Splitter base class
    """
    def __init__(self, traj):
        """
        Create TrajectoryGeneralizer

        Parameters
        ----------
        traj : Trajectory/TrajectoryCollection
        """
        self.traj = traj

    def split(self, **kwargs):
        """
        Split the input Trajectory/TrajectoryCollection.

        Parameters
        ----------
        kwargs : any type
            Split parameters, differs by splitter

        Returns
        -------
        TrajectoryCollection
            Split trajectories
        """
        if isinstance(self.traj, Trajectory):
            return self._split_traj(self.traj, **kwargs)
        elif isinstance(self.traj, TrajectoryCollection):
            return self._split_traj_collection(**kwargs)
        else:
            raise TypeError

    def _split_traj_collection(self, **kwargs):
        trips = []
        for traj in self.traj:
            for x in self._split_traj(traj, **kwargs):
                if x.get_length() > self.traj.min_length:
                    trips.append(x)
        result = copy(self.traj)
        result.trajectories = trips
        return result

    def _split_traj(self, traj, **kwargs):
        return traj


class TemporalSplitter(TrajectorySplitter):
    """
    Split trajectories into subtrajectories using regular time intervals.

    Parameters
    ----------
    mode : str
        Split mode

    Examples
    --------

    >>> mpd.TemporalSplitter(traj).split(mode="year")
    """

    def _split_traj(self, traj, mode='day'):
        result = []
        if mode == 'day':
            grouped = traj.df.groupby(Grouper(freq="D"))
        elif mode == 'month':
            grouped = traj.df.groupby(Grouper(freq="M"))
        elif mode == 'year':
            grouped = traj.df.groupby(Grouper(freq="Y"))
        else:
            raise ValueError('Invalid split mode {}. Must be one of [day, month, year]'.format(mode))
        for key, values in grouped:
            if len(values) > 1:
                result.append(Trajectory(values, '{}_{}'.format(traj.id, key)))
        return TrajectoryCollection(result)


class ObservationGapSplitter(TrajectorySplitter):
    """
    Split trajectories into subtrajectories whenever there is a gap in the observations.

    Parameters
    ----------
    gap : datetime.timedelta
        Time gap threshold

    Examples
    --------

    >>> mpd.ObservationGapSplitter(traj).split(gap=timedelta(hours=1))
    """

    def _split_traj(self, traj, gap):
        result = []
        temp_df = traj.df.copy()
        temp_df['t'] = temp_df.index
        temp_df['gap'] = temp_df['t'].diff() > gap
        temp_df['gap'] = temp_df['gap'].apply(lambda x: 1 if x else 0).cumsum()
        dfs = [group[1] for group in temp_df.groupby(temp_df['gap'])]
        for i, df in enumerate(dfs):
            df = df.drop(columns=['t', 'gap'])
            if len(df) > 1:
                result.append(Trajectory(df, '{}_{}'.format(traj.id, i)))
        return TrajectoryCollection(result)


class SpeedSplitter(TrajectorySplitter):
    """
    Split trajectories if there are no speed measurements above the speed limit for the specified duration.

    Parameters
    ----------
    speed : float
        Speed limit
    duration : datetime.timedelta
        Minimum stop duration

    Examples
    --------

    >>> mpd.SpeedSplitter(traj).split(speed=10, duration=timedelta(minutes=5))
    """
    def _split_traj(self, traj, speed, duration):
        traj = traj.copy()
        speed_col_name = traj.get_speed_column_name()
        if speed_col_name not in traj.df.columns:
            traj.add_speed(overwrite=True)
        traj.df = traj.df[traj.df[speed_col_name] >= speed]
        return ObservationGapSplitter(traj).split(gap=duration)

