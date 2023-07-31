# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt


class _TrajectoryPlotter:
    def __init__(self, data, *args, **kwargs):
        self.data = data
        self.args = args
        self.kwargs = kwargs

        self.width = kwargs.pop("width", 900)
        self.height = kwargs.pop("height", 700)
        self.figsize = kwargs.pop("figsize", None)
        self.column = kwargs.get("column", None)
        self.column = kwargs.get("c", self.column)
        self.ax = kwargs.pop("ax", None)
        self.colormap = kwargs.pop("colormap", None)
        self.colormap = kwargs.pop("column_to_color", self.colormap)
        self.clim = self.kwargs.pop("clim", None)

        self.min_value = kwargs.get("vmin", None)
        self.max_value = kwargs.get("vmax", None)

        self.overlay = None
        self.hvplot_is_geo = kwargs.pop("geo", True)
        self.hvplot_tiles = kwargs.pop("tiles", "OSM")

        self.marker_size = kwargs.pop("marker_size", 200)
        self.marker_color = kwargs.pop("marker_color", None)
        self.line_width = kwargs.pop("line_width", 3.0)
        self._speeds = []

    def get_min_max_values(self):
        column_names = self.data.get_column_names()
        speed_column_name = self.data.get_speed_column_name()
        if self.column == speed_column_name and self.column not in column_names:
            min_value, max_value = self.get_min_max_speed()
        else:
            min_value = self.data.get_min(self.column)
            max_value = self.data.get_max(self.column)
        self.min_value = self.kwargs.pop("vmin", min_value)
        self.max_value = self.kwargs.pop("vmax", max_value)
        return min_value, max_value

    def get_min_max_speed(self):
        for traj in self.get_traj_list():
            temp = traj.copy()
            temp.add_speed(overwrite=True)
            self._speeds.append(temp.df[self.column])
        min_value = min([min(s.tolist()) for s in self._speeds])
        max_value = max([max(s.tolist()) for s in self._speeds])
        return min_value, max_value

    def plot(self):
        if not self.ax:
            self.ax = plt.figure(figsize=self.figsize).add_subplot(1, 1, 1)
        tc = self.preprocess_data()
        line_plot = self.plot_lines(tc)
        return line_plot

    def preprocess_data(self):
        tc = self.data
        speed_col_name = tc.get_speed_column_name()
        if (
            self.column == speed_col_name
            and speed_col_name not in tc.get_column_names()
        ):
            tc = tc.copy()
            tc.add_speed(overwrite=True)

        if self.column:
            (min_val, max_val) = self.get_min_max_values()
            if self.clim is None:
                self.clim = (min_val, max_val)

        return tc

    def get_traj_list(self):
        try:
            return self.data.trajectories
        except AttributeError:
            return [self.data]

    def plot_lines(self, tc):
        line_gdf = tc.to_line_gdf()

        if self.column and self.colormap:
            line_gdf["color"] = "grey"
            line_gdf["color"] = line_gdf[self.column].apply(lambda x: self.colormap[x])
            return line_gdf.plot(
                ax=self.ax, color=line_gdf["color"], *self.args, **self.kwargs
            )
        else:
            self.kwargs.pop("vmin", None)
            self.kwargs.pop("vmax", None)
            return line_gdf.plot(
                ax=self.ax,
                vmin=self.min_value,
                vmax=self.max_value,
                *self.args,
                **self.kwargs
            )

    def hvplot(self):  # noqa F811
        try:
            import hvplot.pandas  # noqa F401, seems necessary for the following import to work
            from holoviews import opts
        except ImportError as error:
            raise ImportError(
                "Missing optional dependencies. To use interactive plotting, "
                "install hvplot and GeoViews (see "
                "https://hvplot.holoviz.org/getting_started/installation.html and "
                "https://geoviews.org)."
            ) from error

        opts.defaults(
            opts.Overlay(
                width=self.width, height=self.height, active_tools=["wheel_zoom"]
            )
        )

        tc = self.preprocess_data()

        if self.colormap:
            self.kwargs["colormap"] = self.colormap
        if not self.column:
            self.kwargs["c"] = tc.get_traj_id_column_name()
            self.kwargs["cmap"] = "Category10"

        line_plot = self.hvplot_lines(tc)
        pt_plot = self.hvplot_end_points(tc)

        if self.overlay:
            return self.overlay * line_plot * pt_plot
        else:
            return line_plot * pt_plot

    def hvplot_end_points(self, tc):
        from holoviews import dim

        direction_column_name = tc.get_direction_column_name()
        try:
            end_pts = tc.get_end_locations(with_direction=True)
        except AttributeError:
            tc.add_direction(name=direction_column_name, overwrite=True)
            end_pts = tc.df.tail(1).copy()

        end_pts["triangle_angle"] = ((end_pts[direction_column_name] * -1.0)).astype(
            float
        )

        hover_cols = self.kwargs.pop("hover_cols", None)

        self.kwargs["hover_cols"] = ["triangle_angle"]
        if hover_cols:
            self.kwargs["hover_cols"] = self.kwargs["hover_cols"] + hover_cols
        if self.marker_color:
            self.kwargs["color"] = self.marker_color
        if self.column:
            self.kwargs["hover_cols"] = self.kwargs["hover_cols"] + [self.column]

        if self.hvplot_is_geo and not tc.is_latlon and tc.get_crs() is not None:
            end_pts = end_pts.to_crs(epsg=4326)
        return end_pts.hvplot(
            geo=self.hvplot_is_geo,
            tiles=None,
            marker="triangle",
            angle=dim("triangle_angle"),
            size=self.marker_size,
            clim=self.clim,
            *self.args,
            **self.kwargs
        )

    def hvplot_lines(self, tc):
        line_gdf = tc.to_line_gdf()

        if self.hvplot_is_geo and not tc.is_latlon and tc.get_crs() is not None:
            line_gdf = line_gdf.to_crs(epsg=4326)
        return line_gdf.hvplot(
            line_width=self.line_width,
            geo=self.hvplot_is_geo,
            tiles=self.hvplot_tiles,
            clim=self.clim,
            *self.args,
            **self.kwargs
        )
