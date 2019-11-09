# -*- coding: utf-8 -*-

import contextily as ctx
import matplotlib.pyplot as plt


class TrajectoryPlotter:

    def __init__(self, data, *args, **kwargs):
        self.data = data
        self.args = args
        self.kwargs = kwargs

        self.figsize = kwargs.pop('figsize', None)
        self.zoom = kwargs.pop('zoom', None)
        self.column = kwargs.get('column', None)
        self.ax = kwargs.pop('ax', None)
        self.column_to_color = kwargs.pop('column_to_color', None)
        self.with_basemap = kwargs.pop('with_basemap', False)

        self.min_value = None
        self.max_value = None

        if self.column:
            self.min_value = self.data.get_min(self.column)
            self.max_value = self.data.get_max(self.column)
        if not self.ax:
            self.ax = plt.figure(figsize=self.figsize).add_subplot(1, 1, 1)

    def _add_basemap(self, ax):
        if self.zoom:
            ctx.add_basemap(ax, zoom=self.zoom)
        else:
            ctx.add_basemap(ax)

    def _plot_trajectory(self, traj):
        if self.column and self.column_to_color:
            try:
                color = self.column_to_color[traj.df[self.column].max()]
            except KeyError:
                color = 'grey'
            return traj.plot(ax=self.ax, for_basemap=self.with_basemap, color=color, *self.args, **self.kwargs)
        else:
            return traj.plot(ax=self.ax, for_basemap=self.with_basemap, vmin=self.min_value, vmax=self.max_value, *self.args, **self.kwargs)

    def plot(self):
        for traj in self.data.trajectories:
            ax = self._plot_trajectory(traj)
            self.kwargs['legend'] = False  # has to be removed after the first iteration, otherwise we get multiple legends!

        self.kwargs.pop('column', None)  # has to be popped, otherwise there's an error in the following plot call if we don't remove column from kwargs

        start_locs = self.data.get_start_locations([self.column])
        if self.with_basemap:
            start_locs = start_locs.to_crs(epsg=3857)

        ax = start_locs.plot(ax=ax, column=self.column, color='white', *self.args, **self.kwargs)

        if self.with_basemap:
            self._add_basemap(ax)
        return ax
