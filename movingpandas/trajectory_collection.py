# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
from copy import copy
from geopandas import GeoDataFrame

sys.path.append(os.path.dirname(__file__))

from .trajectory import Trajectory, SPEED_COL_NAME
from .trajectory_plotter import _TrajectoryCollectionPlotter


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

        Examples
        --------
        >>> import geopandas as read_file
        >>> import movingpandas as mpd
        >>>
        >>> gdf = read_file('data.gpkg')
        >>> gdf['t'] = pd.to_datetime(gdf['t'])
        >>> gdf = gdf.set_index('t')
        >>> trajectory_collection = mpd.TrajectoryCollection(gdf, 'trajectory_id')
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

    def __iter__(self):
        """
        Iterator for trajectories in this collection

        Examples
        --------
        >>>  for traj in trajectory_collection:
        >>>      print(traj)
        """
        for traj in self.trajectories:
            if len(traj.df) >= 2:
                yield traj
            else:
                raise ValueError(f"Trajectory with length >= 2 expected: "
                                 f"got length {len(traj.df)}")

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
            trajectory.crs = df.crs
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
        for traj in self:
            if traj.id == traj_id:
                return traj

    def get_locations_at(self, t):
        """
        Returns GeoDataFrame with trajectory locations at the specified timestamp

        Parameters
        ----------
        t : datetime.datetime
        columns : list[string]
            List of column names that should be copied from the trajectory's dataframe to the output

        Returns
        -------
        GeoDataFrame
            Trajectory locations at timestamp t
        """
        gdf = GeoDataFrame()
        for traj in self:
            if t == 'start':
                x = traj.get_row_at(traj.get_start_time())
            elif t == 'end':
                x = traj.get_row_at(traj.get_end_time())
            else:
                if t < traj.get_start_time() or t > traj.get_end_time():
                    continue
                x = traj.get_row_at(t)
            gdf = gdf.append(x)
        return gdf

    def get_start_locations(self):
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
        return self.get_locations_at('start')

    def get_end_locations(self):
        """
        Returns GeoDataFrame with trajectory end locations

        Parameters
        ----------
        columns : list[string]
            List of column names that should be copied from the trajectory's dataframe to the output

        Returns
        -------
        GeoDataFrame
            Trajectory end locations
        """
        return self.get_locations_at('end')

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
        for traj in self:
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
        for traj in self:
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
        for traj in self:
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
        for traj in self:
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

        A property is a value in the df that is constant for the whole traj. The filter only checks if the value
        on the first row equals the requested property value.

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

        Examples
        --------
        >>> filtered = trajectory_collection.filter('object_type', 'TypeA')
        """
        filtered = []
        for traj in self:
            if traj.df.iloc[0][property_name] in property_values:
                filtered.append(traj)
        result = copy(self)
        result.trajectories = filtered
        return result

    def add_speed(self, overwrite=False):
        """
        Add speed column and values to the trajectories.

        Speed is calculated as CRS units per second, except if the CRS is geographic (e.g. EPSG:4326 WGS84)
        then speed is calculated in meters per second.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing speed values (default: False)
        """
        for traj in self:
            traj.add_speed(overwrite)

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
        return min([traj.df[column].min() for traj in self])

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
        return max([traj.df[column].max() for traj in self])

    def plot(self, *args, **kwargs):
        """
        Generate a plot.

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter

        Examples
        --------
        Plot speed along trajectories (with legend and specified figure size):

        >>> trajectory_collection.plot(column='speed', legend=True, figsize=(9,5))
        """
        return _TrajectoryCollectionPlotter(self, *args, **kwargs).plot()

    def hvplot(self, *args, **kwargs):
        """
        Generate an interactive plot.

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter

        Examples
        --------
        Plot speed along trajectories (with legend and specified figure size):

        >>> trajectory_collection.hvplot(c='speed', line_width=7.0, width=700, height=400, colorbar=True)
        """
        return _TrajectoryCollectionPlotter(self, *args, **kwargs).hvplot()


def _get_location_at(traj, t, columns=None):
    loc = {'t': t, 'geometry': traj.get_position_at(t),
           'traj_id': traj.id, 'obj_id': traj.obj_id}
    if columns and columns != [None]:
        for column in columns:
            loc[column] = traj.df.iloc[traj.df.index.get_loc(t, method='nearest')][column]
    return loc