# -*- coding: utf-8 -*-

import contextily as ctx
import matplotlib.pyplot as plt


class TrajectoryPlotter:

    @staticmethod
    def plot_with_basemap(traj_manager, property=None, property_to_color=None, *args, **kwargs):
        figsize = kwargs.pop('figsize', None)
        zoom = kwargs.pop('zoom', None)
        column = kwargs.get('column', None)
        ax = kwargs.pop('ax', None)
        min_value, max_value = None, None
        if column:
            min_value = traj_manager.get_min(column)
            max_value = traj_manager.get_max(column)
        if not ax:
            ax = plt.figure(figsize=figsize).add_subplot(1, 1, 1)
        for traj in traj_manager.trajectories:
            if property and property_to_color:
                try:
                    color = property_to_color[traj.df[property].max()]
                except KeyError:
                    color = 'grey'
                ax = traj.plot(ax=ax, for_basemap=True, color=color, *args, **kwargs)
            else:
                ax = traj.plot(ax=ax, for_basemap=True, vmin=min_value, vmax=max_value, *args, **kwargs)
            kwargs['legend'] = False  # otherwise we get multiple legends

        kwargs.pop('column', None)  # otherwise there's an error in the following plot call if we don't remove column from kwargs
        ax = traj_manager.get_start_locations([property]).to_crs(epsg=3857).plot(ax=ax, column=property, color='white', *args, **kwargs)

        if zoom:
            ctx.add_basemap(ax, zoom=zoom)
        else:
            ctx.add_basemap(ax)
        return ax

