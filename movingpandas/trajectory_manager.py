# -*- coding: utf-8 -*-

import os, sys
import numpy as np
import pandas as pd
from copy import copy
from geopandas import GeoDataFrame

sys.path.append(os.path.dirname(__file__))

from .trajectory import Trajectory
from .trajectory_plotter import TrajectoryPlotter


class TrajectoryManager:
    def __init__(self, df, trajectory_id, min_length=0):
        self.min_length = min_length
        self.trajectories = self.df_to_trajectories(df, trajectory_id)

    def __len__(self):
        return len(self.trajectories)

    def __str__(self):
        return 'TrajectoryManager with {} trajectories'.format(self.__len__())

    def df_to_trajectories(self, df, trajectory_id):
        trajectories = []
        for key, values in df.groupby([trajectory_id]):
            if len(values) < 2:
                continue
            trajectory = Trajectory(key, values)
            if trajectory.get_length() < self.min_length:
                continue
            trajectories.append(trajectory)
        return trajectories

    def get_trajectory(self, traj_id):
        for traj in self.trajectories:
            if traj.id == traj_id:
                return traj

    def get_start_locations(self, columns=None):
        starts = []
        for traj in self.trajectories:
            crs = traj.crs
            traj_start = {'geometry': traj.get_start_location(), 'id': traj.id, 't': traj.get_start_time()}
            if columns:
                for column in columns:
                    try:
                        max_value = traj.df[column].max()
                        if np.isnan(max_value):
                            max_value = 'undefined'
                        traj_start[column] = max_value
                    except TypeError:
                        most_common = traj.df[column].value_counts().argmax()
                        traj_start[column] = most_common
            starts.append(traj_start)
        starts = GeoDataFrame(pd.DataFrame(starts), crs=crs)
        return starts

    def split_by_date(self, mode):
        trips = []
        for traj in self.trajectories:
            for x in traj.split_by_date(mode):
                if x.get_length() > self.min_length:
                    trips.append(x)
        result = copy(self)
        result.trajectories = trips
        return result

    def split_by_observation_gap(self, gap_timedelta):
        trips = []
        for traj in self.trajectories:
            for x in traj.split_by_observation_gap(gap_timedelta):
                if x.get_length() > self.min_length:
                    trips.append(x)
        result = copy(self)
        result.trajectories = trips
        return result

    def clip(self, polygon):
        clipped = []
        for traj in self.trajectories:
            try:
                for intersect in traj.clip(polygon):
                    clipped.append(intersect)
            except:
                pass
        result = copy(self)
        result.trajectories = clipped
        return result

    def filter(self, property_name, property_values):
        filtered = []
        for traj in self.trajectories:
            if traj.df[property_name].max() in property_values:
                filtered.append(traj)
        result = copy(self)
        result.trajectories = filtered
        return result

    def get_min(self, column):
        return min([traj.df[column].min() for traj in self.trajectories])

    def get_max(self, column):
        return max([traj.df[column].max() for traj in self.trajectories])

    def plot_with_basemap(self, property=None, property_to_color=None, *args, **kwargs):
        TrajectoryPlotter.plot_with_basemap(self, property, property_to_color, *args, **kwargs)
        """
        figsize = kwargs.pop('figsize', None)
        zoom = kwargs.pop('zoom', None)
        column = kwargs.get('column', None)
        ax = kwargs.pop('ax', None)
        min_value, max_value = None, None
        if column:
            min_value = self.get_min(column)
            max_value = self.get_max(column)
        if not ax:
            ax = plt.figure(figsize=figsize).add_subplot(1, 1, 1)
        for traj in self.trajectories:
            if property and property_to_color:
                try:
                    color = property_to_color[traj.df[property].max()]
                except KeyError:
                    color = 'grey'
                ax = traj.plot(ax=ax, for_basemap=True, color=color, *args, **kwargs)
            else:
                ax = traj.plot(ax=ax, for_basemap=True, vmin=min_value, vmax=max_value, *args, **kwargs)
            kwargs['legend'] = False  # otherwise we get multiple legends

        column = kwargs.pop('column', None)  # otherwise there's an error in the following plot call if we don't remove column from kwargs
        ax = self.get_start_locations([property]).to_crs(epsg=3857).plot(ax=ax, column=property, color='white', *args, **kwargs)

        if zoom:
            ctx.add_basemap(ax, zoom=zoom)
        else:
            ctx.add_basemap(ax)
        return ax
        """
