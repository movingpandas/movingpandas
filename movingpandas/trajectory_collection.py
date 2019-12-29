# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
from copy import copy
from geopandas import GeoDataFrame

sys.path.append(os.path.dirname(__file__))

from .trajectory import Trajectory
from .trajectory_plotter import TrajectoryCollectionPlotter


class TrajectoryCollection:
    def __init__(self, data, traj_id_col=None, obj_id_col=None, min_length=0):
        """
        Create TrajectoryCollection from list of trajectories or GeoDataFrame

        Parameters
        ----------
        data : list[Trajectory] or GeoDataFrame
            List of Trajectory objects or a GeoDataFrame with trajectory IDs, point geometry column and timestamp index
        traj_id_col : string
            Name of the GeoDataFrame column containing trajectory IDs
        obj_id_col : string
            Name of the GeoDataFrame column containing moving object IDs
        min_length : numeric
            Desired minimum length of trajectories. (Shorter trajectories are discarded.)
        """
        self.min_length = min_length
        if type(data) == list:
            self.trajectories = data
        else:
            self.trajectories = self._df_to_trajectories(data, traj_id_col, obj_id_col)

    def __len__(self):
        return len(self.trajectories)

    def __str__(self):
        return 'TrajectoryCollection with {} trajectories'.format(self.__len__())

    def _df_to_trajectories(self, df, traj_id_col, obj_id_col):
        trajectories = []
        for traj_id, values in df.groupby([traj_id_col]):
            if len(values) < 2:
                continue
            if obj_id_col in values.columns:
                obj_id = values.iloc[0][obj_id_col]
            else:
                obj_id = None
            trajectory = Trajectory(values, traj_id, obj_id=obj_id)
            if trajectory.get_length() < self.min_length:
                continue
            trajectories.append(trajectory)
        return trajectories

    def get_trajectory(self, traj_id):
        """
        Return the Trajectory with the requested ID

        Parameters
        ----------
        traj_id : any
            Trajectory ID

        Returns
        -------
        Trajectory
        """
        for traj in self.trajectories:
            if traj.id == traj_id:
                return traj

    def get_start_locations(self, columns=None):
        """
        Returns GeoDataFrame with trajectory start locations

        Parameters
        ----------
        columns : list[string]
            List of column names that should be copied from the trajectory's dataframe to the output

        Returns
        -------
        GeoDataFrame
            Trajectory start locations
        """
        starts = []
        for traj in self.trajectories:
            crs = traj.crs
            traj_start = {'t': traj.get_start_time(), 'geometry': traj.get_start_location(),
                          'traj_id': traj.id, 'obj_id': traj.obj_id}
            if columns and columns != [None]:
                for column in columns:
                    traj_start[column] = traj.df.iloc[0][column]
            starts.append(traj_start)
        starts = GeoDataFrame(pd.DataFrame(starts), crs=crs)
        return starts

    def split_by_date(self, mode):
        """
        Split trajectories into subtrajectories using regular time intervals.

        Resulting subtrajectories that are shorter than the TrajectoryCollection's
        min_length threshold are discarded.

        Parameters
        ----------
        mode : str
            Split mode

        Returns
        -------
        TrajectoryCollection
            Resulting split subtrajectories
        """
        trips = []
        for traj in self.trajectories:
            for x in traj.split_by_date(mode):
                if x.get_length() > self.min_length:
                    trips.append(x)
        result = copy(self)
        result.trajectories = trips
        return result

    def split_by_observation_gap(self, gap_timedelta):
        """
        Split trajectories into subtrajectories whenever there is a gap in the observations.

        Resulting subtrajectories that are shorter than the TrajectoryCollection's
        min_length threshold are discarded.

        Parameters
        ----------
        gap : datetime.timedelta
            Time gap threshold

        Returns
        -------
        TrajectoryCollection
            Resulting split subtrajectories
        """
        trips = []
        for traj in self.trajectories:
            for x in traj.split_by_observation_gap(gap_timedelta):
                if x.get_length() > self.min_length:
                    trips.append(x)
        result = copy(self)
        result.trajectories = trips
        return result

    def get_intersecting(self, polygon):
        """
        Return trajectories that intersect the given polygon.

        Parameters
        ----------
        polygon : shapely Polygon
            Polygon to clip with
        Returns
        -------
        TrajectoryCollection
            Resulting intersecting trajectories
        """
        intersecting = []
        for traj in self.trajectories:
            try:
                if traj.intersects(polygon):
                    intersecting.append(traj)
            except:
                pass
        result = copy(self)
        result.trajectories = intersecting
        return result

    def clip(self, polygon, pointbased=False):
        """
        Clip trajectories by the given polygon.

        Parameters
        ----------
        polygon : shapely Polygon
            Polygon to clip with
        pointbased : bool
            Clipping method

        Returns
        -------
        TrajectoryCollection
            Resulting clipped trajectory segments
        """
        clipped = []
        for traj in self.trajectories:
            try:
                for intersect in traj.clip(polygon, pointbased):
                    clipped.append(intersect)
            except:
                pass
        result = copy(self)
        result.trajectories = clipped
        return result

    def filter(self, property_name, property_values):
        """
        Filter trajectories by property

        TODO: explain concept of property, i.e. a value in the df that is constant for the whole traj

        Parameters
        ----------
        property_name : string
            Name of the dataframe column containing the property
        property_values : any
            Desired property value

        Returns
        -------
        TrajectoryCollection
            Trajectories that fulfill the filter criteria
        """
        filtered = []
        for traj in self.trajectories:
            if traj.df.iloc[0][property_name] in property_values:
                filtered.append(traj)
        result = copy(self)
        result.trajectories = filtered
        return result

    def get_min(self, column):
        """
        Return minimum value in the provided dataframe column over all trajectories

        Parameters
        ----------
        column : string
            Name of the dataframe column

        Returns
        -------
        Sortable
            Minimum value
        """
        return min([traj.df[column].min() for traj in self.trajectories])

    def get_max(self, column):
        """
        Return maximum value in the provided dataframe column over all trajectories

        Parameters
        ----------
        column : string
            Name of the dataframe column

        Returns
        -------
        Sortable
            Maximum value
        """
        return max([traj.df[column].max() for traj in self.trajectories])

    def plot(self, *args, **kwargs):
        """
        Generate a plot.

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter
        """
        return TrajectoryCollectionPlotter(self, *args, **kwargs).plot()

    def hvplot(self, *args, **kwargs):
        """
        Generate an interactive plot.

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter
        """
        return TrajectoryCollectionPlotter(self, *args, **kwargs).hvplot()
