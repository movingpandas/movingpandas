# -*- coding: utf-8 -*-

from copy import copy
from functools import partial
from multiprocessing import Pool
from pandas import Grouper
from geopandas import GeoDataFrame
import numpy as np
import warnings

from .trajectory_stop_detector import TrajectoryStopDetector
from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .trajectory_utils import convert_time_ranges_to_segments
from .spatiotemporal_utils import TRange
from .geometry_utils import angular_difference


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

    def split(self, n_processes=1, **kwargs):
        """
        Split the input Trajectory/TrajectoryCollection.

        Parameters
        ----------
        n_processes : int or None, optional
            Number of processes to use for computation when splitting on a
            `TrajectoryCollection` (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing. This argument will be ignored when used
            with a `Trajectory` object.
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
            if n_processes > 1 or n_processes is None:
                return self._split_traj_collection_multiprocessing(
                    n_processes, **kwargs
                )
            else:
                return self._split_traj_collection(self.traj, **kwargs)
        else:
            raise TypeError

    def _split_traj_collection(self, trajs, **kwargs):
        trips = []

        for traj in trajs:
            for x in self._split_traj(traj, **kwargs):
                if x.get_length() > self.traj.min_length:
                    trips.append(x)
        result = copy(self.traj)
        result.trajectories = trips
        return result

    def _split_traj_collection_multiprocessing(self, n_processes, **kwargs):
        from movingpandas.tools._multi_threading import split_list

        p = Pool(n_processes)
        data = split_list(self.traj.trajectories, n_processes)
        data = [d for d in data]

        split_traj_collection_with_kwargs = partial(
            self._split_traj_collection, **kwargs
        )

        splits = []
        for split in p.map(split_traj_collection_with_kwargs, data):
            splits.extend(split)

        result = copy(self.traj)
        result.trajectories = splits
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
        modes = {"hour": "h", "day": "D", "month": "ME", "year": "YE"}
        if mode in modes.keys():
            mode = modes[mode]
        grouped = traj.df.groupby(Grouper(freq=mode))
        dfs = []
        show_warning = False
        for _, values in grouped:
            if len(values) == 0:
                show_warning = True
            else:
                dfs.append(values)
        if show_warning:
            warnings.warn(
                f"Temporal splitting results contain observation gaps that exceed your "
                f"split size of {mode}. Consider running the ObservationGapSplitter to "
                f"further clean the results."
            )

        for i, df in enumerate(dfs):
            if i < len(dfs) - 1:
                next_index = dfs[i + 1].iloc[0].name
                next_values = dfs[i + 1].iloc[0].to_dict()
                df.loc[next_index] = next_values
                df = df.sort_index(ascending=True)
            if len(df) > 1:
                result.append(
                    Trajectory(
                        df,
                        f"{traj.id}_{i}",
                        traj_id_col=traj.get_traj_id_col(),
                        x=traj.x,
                        y=traj.y,
                    )
                )
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
                result.append(
                    Trajectory(
                        df,
                        f"{traj.id}_{i}",
                        traj_id_col=traj.get_traj_id_col(),
                        x=traj.x,
                        y=traj.y,
                    )
                )
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
        speed_col_name = traj.get_speed_col()
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
        items = [traj.get_start_time()]
        for stop_range in stop_ranges:
            items.append(stop_range.t_0)
            items.append(stop_range.t_n)
        items.append(traj.get_end_time())
        result = [TRange(*items[x : x + 2]) for x in range(0, len(items), 2)]
        return result


class AngleChangeSplitter(TrajectorySplitter):
    """
    Split trajectories into subtrajectories whenever there is a specified change in
    the heading angle.

    Parameters
    ----------
    min_angle : float
        Minimum angle change
    min_speed: float
        Min speed threshold at which points are considered for angle change.
        (Speed is calculated as CRS units per second, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then speed is calculated in meters per second.)
    min_length : numeric
        Desired minimum length of trajectories. Shorter trajectories are discarded.
        (Length is calculated using CRS units, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then length is calculated in metres.)

    Examples
    --------

    >>> mpd.AngleSplitter(traj).split(min_angle=45, min_speed=15)
    """

    def _split_traj(self, traj, min_angle=45, min_speed=0, min_length=0):
        result = []
        traj = traj.copy()

        direction_col_name = traj.get_direction_col()
        if direction_col_name not in traj.df.columns:
            traj.add_direction(overwrite=True)

        speed_col_name = traj.get_speed_col()
        if speed_col_name not in traj.df.columns:
            traj.add_speed(overwrite=True)

        comp_dir = traj.df[direction_col_name].iloc[0]
        traj.df["dirChange"] = -1
        dir_group = 0

        for i, (direction, speed) in enumerate(
            zip(traj.df[direction_col_name].tolist(), traj.df[speed_col_name].tolist())
        ):
            if speed >= min_speed:
                if angular_difference(comp_dir, direction) >= min_angle:
                    comp_dir = direction
                    dir_group += 1

            traj.df.iloc[i, traj.df.columns.get_loc("dirChange")] = dir_group

        dfs = [group[1] for group in traj.df.groupby(traj.df["dirChange"])]
        for i, df in enumerate(dfs):
            df = df.drop(columns=["dirChange"])
            if len(df) > 1:
                prev_index = dfs[i - 1].iloc[-1].name
                prev_values = dfs[i - 1].iloc[-1].to_dict()
                if i > 0:
                    df.loc[prev_index] = prev_values
                    df = df.sort_index(ascending=True)

                result.append(
                    Trajectory(
                        df,
                        f"{traj.id}_{i}",
                        traj_id_col=traj.get_traj_id_col(),
                        x=traj.x,
                        y=traj.y,
                    )
                )

        return TrajectoryCollection(result, min_length=min_length)


class ValueChangeSplitter(TrajectorySplitter):
    """
    Split trajectories into subtrajectories whenever there is a change in
    the specified column values.

    Parameters
    ----------
    col_name : string
        Name of the col to monitor for changes in consecutive values
    min_length : numeric
        Desired minimum length of trajectories. Shorter trajectories are discarded.
        (Length is calculated using CRS units, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then length is calculated in metres.)

    Examples
    --------

    >>> mpd.ValueChangeSplitter(traj).split(col_name='column1')
    """

    def _split_traj(self, traj, col_name, min_length=0):
        result = []
        temp_df = traj.df.copy()
        temp_df["t"] = temp_df.index
        temp_df["change"] = temp_df[col_name].shift() != temp_df[col_name]
        temp_df["change"] = temp_df["change"].apply(lambda x: 1 if x else 0).cumsum()
        dfs = [group[1] for group in temp_df.groupby(temp_df["change"])]
        for i, df in enumerate(dfs):
            df = df.drop(columns=["t", "change"])
            if i < (len(dfs) - 1):
                next_index = dfs[i + 1].iloc[0].name
                next_values = dfs[i + 1].iloc[0].to_dict()
                df.loc[next_index] = next_values
                df = df.sort_index(ascending=True)
            if len(df) > 1:
                df = GeoDataFrame(df).set_crs(traj.df.crs)
                traj = Trajectory(
                    df,
                    f"{traj.id}_{i}",
                    traj_id_col=traj.get_traj_id_col(),
                    x=traj.x,
                    y=traj.y,
                )
                result.append(traj)
        return TrajectoryCollection(result, min_length=min_length)
