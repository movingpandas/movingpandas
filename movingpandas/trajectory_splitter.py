# -*- coding: utf-8 -*-

from copy import copy
from pandas import Grouper
import numpy as np

from .trajectory_stop_detector import TrajectoryStopDetector
from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .trajectory_utils import convert_time_ranges_to_segments
from .time_range_utils import TemporalRange


class TrajectorySplitter:
    """
    Splitter base class
    """

    def __init__(self, traj):
        """
        Create TrajectoryGeneralizer

        Parameters
        ----------
        traj : Trajectory or TrajectoryCollection
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
        Split mode. (hour, day, month or year)
    min_length : numeric
        Desired minimum length of trajectories. (Shorter trajectories are discarded.)

    Examples
    --------

    >>> mpd.TemporalSplitter(traj).split(mode="year")
    """

    def _split_traj(self, traj, mode="day", min_length=0):
        result = []
        modes = {"hour": "H", "day": "D", "month": "M", "year": "Y"}
        if mode in modes.keys():
            mode = modes[mode]
        grouped = traj.df.groupby(Grouper(freq=mode))
        for key, values in grouped:
            if len(values) > 1:
                result.append(Trajectory(values, "{}_{}".format(traj.id, key)))
        return TrajectoryCollection(result, min_length=min_length)


class ObservationGapSplitter(TrajectorySplitter):
    """
    Split trajectories into subtrajectories whenever there is a gap in the observations.

    Parameters
    ----------
    gap : datetime.timedelta
        Time gap threshold
    min_length : numeric
        Desired minimum length of trajectories. Shorter trajectories are discarded.
        (Length is calculated using CRS units, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then length is calculated in metres.)

    Examples
    --------

    >>> mpd.ObservationGapSplitter(traj).split(gap=timedelta(hours=1))
    """

    def _split_traj(self, traj, gap, min_length=0):
        result = []
        temp_df = traj.df.copy()
        temp_df["t"] = temp_df.index
        temp_df["gap"] = temp_df["t"].diff() > gap
        temp_df["gap"] = temp_df["gap"].apply(lambda x: 1 if x else 0).cumsum()
        dfs = [group[1] for group in temp_df.groupby(temp_df["gap"])]
        for i, df in enumerate(dfs):
            df = df.drop(columns=["t", "gap"])
            if len(df) > 1:
                result.append(Trajectory(df, "{}_{}".format(traj.id, i)))
        return TrajectoryCollection(result, min_length=min_length)


class SpeedSplitter(TrajectorySplitter):
    """
    Split trajectories if there are no speed measurements above the speed limit
    for the specified duration.

    Parameters
    ----------
    speed : float
        Speed limit
    duration : datetime.timedelta
        Minimum stop duration
    min_length : numeric
        Desired minimum length of trajectories. Shorter trajectories are discarded.
        (Length is calculated using CRS units, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then length is calculated in metres.)
    max_speed: float
        Max speed limit
        (Speed is calculated as CRS units per second, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then speed is calculated in meters per second.)

    Examples
    --------

    >>> mpd.SpeedSplitter(traj).split(speed=10, duration=timedelta(minutes=5))
    """

    def _split_traj(self, traj, speed, duration, min_length=0, max_speed=np.inf):
        traj = traj.copy()
        speed_col_name = traj.get_speed_column_name()
        if speed_col_name not in traj.df.columns:
            traj.add_speed(overwrite=True)
        traj.df = traj.df[traj.df[speed_col_name].between(speed, max_speed)]
        return ObservationGapSplitter(traj).split(gap=duration, min_length=min_length)


class StopSplitter(TrajectorySplitter):
    """
    Split trajectories at detected stops.
    A stop is detected if the movement stays within an area of specified size for
    at least the specified duration.

    Parameters
    ----------
    max_diameter : float
        Maximum diameter for stop detection
    min_duration : datetime.timedelta
        Minimum stop duration
    min_length : numeric
        Desired minimum length of trajectories. Shorter trajectories are discarded.
        (Length is calculated using CRS units, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then length is calculated in metres.)

    Examples
    --------

    >>> mpd.StopSplitter(traj).split(max_diameter=7, min_duration=timedelta(seconds=60))
    """

    def _split_traj(self, traj, max_diameter, min_duration, min_length=0):
        stop_detector = TrajectoryStopDetector(traj)
        stop_time_ranges = stop_detector.get_stop_time_ranges(
            max_diameter, min_duration
        )
        between_stops = self.get_time_ranges_between_stops(traj, stop_time_ranges)
        result = convert_time_ranges_to_segments(traj, between_stops)
        return TrajectoryCollection(result, min_length=min_length)

    @staticmethod
    def get_time_ranges_between_stops(traj, stop_ranges):
        result = []
        if stop_ranges:
            for i in range(0, len(stop_ranges)):
                if i == 0:
                    result.append(
                        TemporalRange(traj.get_start_time(), stop_ranges[i].t_0)
                    )
                    continue
                result.append(TemporalRange(stop_ranges[i - 1].t_n, stop_ranges[i].t_0))
            result.append(TemporalRange(stop_ranges[-1].t_n, traj.get_end_time()))
        else:
            result.append(TemporalRange(traj.get_start_time(), traj.get_end_time()))
        return result
