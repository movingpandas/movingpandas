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
        self.colorbar = self.kwargs.pop("colorbar", True)

        self.min_value = kwargs.get("vmin", None)
        self.max_value = kwargs.get("vmax", None)

        self.overlay = None
        self.hvplot_is_geo = kwargs.pop("geo", True)
        self.hvplot_tiles = kwargs.pop("tiles", "OSM")

        self.marker_size = kwargs.pop("marker_size", 200)
        self.marker_color = kwargs.pop("marker_color", None)
        self.line_width = kwargs.pop("line_width", 3.0)

        self.column_names = data.get_column_names()
        self.traj_id_col_name = data.get_traj_id_col()
        self.speed_col_name = data.get_speed_col()
        self.direction_col_name = data.get_direction_col()
        self.geom_col_name = data.get_geom_col()
        self.speed_col_missing = self.speed_col_name not in self.column_names

        self.hv_defaults = {
            "width": self.width,
            "height": self.height,
            "active_tools": ["wheel_zoom"],
        }

    def get_min_max_values(self):
        min_value = self.data.get_min(self.column)
        max_value = self.data.get_max(self.column)
        self.min_value = self.kwargs.pop("vmin", min_value)
        self.max_value = self.kwargs.pop("vmax", max_value)
        return min_value, max_value

    def plot(self):
        if not self.ax:
            self.ax = plt.figure(figsize=self.figsize).add_subplot(1, 1, 1)
        tc = self.preprocess_data()
        line_plot = self.plot_lines(tc)

        to_drop = [x for x in tc.get_column_names() if x not in self.column_names]
        tc.drop(columns=to_drop)

        return line_plot

    def preprocess_data(self):
        tc = self.data

        if self.column is None:
            return tc

        if self.column:
            if self.column == self.speed_col_name and self.speed_col_missing:
                tc.add_speed(overwrite=True)

            (min_val, max_val) = self.get_min_max_values()
            if self.clim is None:
                self.clim = (min_val, max_val)

        return tc

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

        opts.defaults(opts.Overlay(**self.hv_defaults))

        tc = self.preprocess_data()
        self.set_default_cmaps()

        plot = self.hvplot_lines(tc)
        if self.marker_size > 0:
            plot = plot * self.hvplot_end_points(tc)

        to_drop = [x for x in tc.get_column_names() if x not in self.column_names]
        tc.drop(columns=to_drop)

        if self.overlay:
            return self.overlay * plot
        else:
            return plot

    def set_default_cmaps(self):
        from bokeh.palettes import all_palettes, Turbo256

        if self.colormap:
            self.kwargs["colormap"] = self.colormap
        elif not self.column and self.traj_id_col_name is not None:
            self.kwargs["c"] = self.traj_id_col_name
            if "cmap" not in self.kwargs:
                try:
                    n = len(self.data)
                except TypeError:  # len(Trajectory) will return a float
                    n = 1
                if n <= 10:
                    self.kwargs["cmap"] = all_palettes["Category10"][max(3, n)]
                elif n <= 20:
                    self.kwargs["cmap"] = all_palettes["Category20"][max(3, n)]
                else:
                    self.kwargs["cmap"] = Turbo256[max(3, n)]
        elif self.column == self.speed_col_name and "cmap" not in self.kwargs:
            self.kwargs["cmap"] = "Plasma"

    def hvplot_end_points(self, tc):
        from holoviews import dim

        try:
            end_pts = tc.get_end_locations(with_direction=True)
        except AttributeError:
            tc.add_direction(name=self.direction_col_name, overwrite=True)
            end_pts = tc.df.tail(1).copy()

        end_pts["triangle_angle"] = ((end_pts[self.direction_col_name] * -1.0)).astype(
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
        cols = [self.traj_id_col_name, self.geom_col_name]
        if "hover_cols" in self.kwargs:
            cols = cols + self.kwargs["hover_cols"]
        if self.column:
            cols = cols + [self.column]
        line_gdf = tc.to_line_gdf(columns=cols)

        if self.hvplot_is_geo and not tc.is_latlon and tc.get_crs() is not None:
            line_gdf = line_gdf.to_crs(epsg=4326)
        return line_gdf.hvplot(
            line_width=self.line_width,
            geo=self.hvplot_is_geo,
            tiles=self.hvplot_tiles,
            clim=self.clim,
            colorbar=self.colorbar,
            *self.args,
            **self.kwargs
        )
