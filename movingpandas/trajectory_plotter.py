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

        self.plot_lines = kwargs.pop("plot_lines", True)
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
        line_plot = self._plot_lines(tc)

        to_drop = [x for x in tc.get_column_names() if x not in self.column_names]
        tc.drop(columns=to_drop)

        return line_plot

    def explore(self):
        tc = self.preprocess_data()
        explore_plot = self._explore_lines(tc)

        to_drop = [x for x in tc.get_column_names() if x not in self.column_names]
        tc.drop(columns=to_drop)

        return explore_plot

    def _explore_lines(self, tc):
        from importlib.metadata import version

        cols = [self.traj_id_col_name, self.geom_col_name]
        if self.column:
            cols = cols + [self.column]
        cols = list(set(cols))

        if self.column is None:
            line_gdf = tc.to_line_gdf()
        else:
            line_gdf = tc.to_line_gdf(columns=cols)

        if version("geopandas") >= "1.0.0":
            return line_gdf.explore(*self.args, **self.kwargs)
        else:
            raise (
                NotImplementedError(
                    "Please install geopandas >= 1.0.0 to use this function."
                )
            )

    def preprocess_data(self):
        tc = self.data

        if self.column is None:
            return tc

        if self.column:
            if self.column == self.speed_col_name and self.speed_col_missing:
                tc.add_speed()

            (min_val, max_val) = self.get_min_max_values()
            if self.clim is None:
                self.clim = (min_val, max_val)

        return tc

    def _plot_lines(self, tc):
        line_gdf = tc.to_line_gdf()

        if self.column and self.colormap:
            line_gdf["color"] = line_gdf[self.column].apply(
                lambda x: self.colormap[x] if x in self.colormap else "grey"
            )
            self.kwargs.pop(
                "column"
            )  # to avoid gpd warning (only specify one of 'column' or 'color')
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
            import colorcet as cc
            from holoviews import opts
            from bokeh.palettes import Category10_10
        except ImportError as error:
            raise ImportError(
                "Missing optional dependencies. To use interactive plotting, "
                "install hvplot and GeoViews (see "
                "https://hvplot.holoviz.org/getting_started/installation.html and "
                "https://geoviews.org)."
            ) from error

        opts.defaults(opts.Overlay(**self.hv_defaults))
        self.MPD_PALETTE = list(Category10_10) + cc.palette["glasbey"]

        self.color = self.kwargs.pop("color", None)

        tc = self.preprocess_data()

        plot = self._hvplot_lines(tc)
        if self.marker_size > 0:
            plot = plot * self._hvplot_end_points(tc)

        to_drop = [x for x in tc.get_column_names() if x not in self.column_names]
        tc.drop(columns=to_drop)

        if self.overlay:
            return self.overlay * plot
        else:
            return plot

    def _hvplot_end_points(self, tc):
        from holoviews import dim, Overlay

        if "TrajectoryCollection" in str(type(tc)):
            end_pts = tc.get_end_locations(with_direction=True)
        else:  # Trajectory
            tc.add_direction(name=self.direction_col_name, overwrite=True)
            end_pts = tc.df.tail(1).copy()

        end_pts["triangle_angle"] = end_pts[self.direction_col_name] * -1.0
        end_pts["triangle_angle"] = end_pts["triangle_angle"].astype(float)

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

        if self.column:
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
        else:
            plots = []
            for i in range(len(end_pts)):
                tmp = end_pts.iloc[i : i + 1, :]
                tmp = tmp.hvplot(
                    geo=self.hvplot_is_geo,
                    tiles=None,
                    marker="triangle",
                    angle=dim("triangle_angle"),
                    size=self.marker_size,
                    color=self.get_color(i),
                    *self.args,
                    **self.kwargs
                )
                plots.append(tmp)
            return Overlay(plots)

    def _hvplot_lines(self, tc):
        cols = [self.traj_id_col_name, self.geom_col_name]
        if "hover_cols" in self.kwargs:
            cols = cols + self.kwargs["hover_cols"]
        if self.column:
            cols = cols + [self.column]
        cols = list(set(cols))

        if self.column is None:
            return self._hvplot_traj_gdf(tc)
        else:
            return self._hvplot_line_gdf(tc, cols)

    def get_color(self, i):
        if self.color:
            return self.color
        else:
            return self.MPD_PALETTE[i]

    def _hvplot_traj_gdf(self, tc):
        from holoviews import Cycle, Overlay

        Cycle.default_cycles["default_colors"] = self.MPD_PALETTE

        traj_gdf = tc.to_traj_gdf()
        if self.hvplot_is_geo and not tc.is_latlon and tc.get_crs() is not None:
            traj_gdf = traj_gdf.to_crs(epsg=4326)

        plots = []
        for i in range(len(traj_gdf)):
            tmp = traj_gdf.iloc[i : i + 1, :]
            tmp = tmp.hvplot(
                line_width=self.line_width,
                geo=self.hvplot_is_geo,
                tiles=self.hvplot_tiles,
                color=self.get_color(i),
                colorbar=self.colorbar,
                *self.args,
                **self.kwargs
            )
            self.hvplot_tiles = None
            plots.append(tmp)
        return Overlay(plots)

    def _hvplot_line_gdf(self, tc, cols):
        line_gdf = tc.to_line_gdf(columns=cols)

        ids = None
        if self.column is None and self.traj_id_col_name is not None:
            ids = line_gdf[self.traj_id_col_name].unique()
        self.set_default_cmaps(ids)

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

    def hvplot_pts(self):
        try:
            import hvplot.pandas  # noqa F401, seems necessary for the following import to work
            import colorcet as cc
            from holoviews import opts, dim, Overlay
            from bokeh.palettes import Category10_10
        except ImportError as error:
            raise ImportError(
                "Missing optional dependencies. To use interactive plotting, "
                "install hvplot and GeoViews (see "
                "https://hvplot.holoviz.org/getting_started/installation.html and "
                "https://geoviews.org)."
            ) from error

        opts.defaults(opts.Overlay(**self.hv_defaults))
        self.MPD_PALETTE = list(Category10_10) + cc.palette["glasbey"]
        self.color = self.kwargs.pop("color", None)

        if "TrajectoryCollection" in str(type(self.data)):
            tc = self.data.copy()
            if self.direction_col_name not in tc.trajectories[0].df.columns:
                tc.add_direction(name=self.direction_col_name)
            if self.column:
                if self.column == self.speed_col_name and self.speed_col_missing:
                    tc.add_speed()
            pts_gdf = tc.to_point_gdf()
        else:  # Trajectory
            traj = self.data.copy()
            if self.direction_col_name not in traj.df.columns:
                traj.add_direction(name=self.direction_col_name)
            if self.column:
                if self.column == self.speed_col_name and self.speed_col_missing:
                    traj.add_speed()
            pts_gdf = traj.df

        ids = None
        if self.column is None and self.traj_id_col_name is not None:
            ids = pts_gdf[self.traj_id_col_name].unique()
        self.set_default_cmaps(ids)

        pts_gdf["triangle_angle"] = pts_gdf[self.direction_col_name] * -1.0
        pts_gdf["triangle_angle"] = pts_gdf["triangle_angle"].astype(float)
        pts_gdf["dash_angle"] = ((pts_gdf[self.direction_col_name] * -1.0) + 90).astype(
            float
        )

        hover_cols = self.kwargs.pop("hover_cols", None)

        self.kwargs["hover_cols"] = ["triangle_angle", "dash_angle"]
        if hover_cols:
            self.kwargs["hover_cols"] = self.kwargs["hover_cols"] + hover_cols
        if self.marker_color:
            self.kwargs["color"] = self.marker_color
        if self.column:
            self.kwargs["hover_cols"] = self.kwargs["hover_cols"] + [self.column]

        if (
            self.hvplot_is_geo
            and not self.data.is_latlon
            and self.data.get_crs() is not None
        ):
            pts_gdf = pts_gdf.to_crs(epsg=4326)

        if self.column:
            arrow_shaft = pts_gdf.hvplot(
                geo=self.hvplot_is_geo,
                tiles=None,
                marker="dash",
                angle=dim("dash_angle"),
                size=self.marker_size * 1.7,
                line_width=self.marker_size / 70.0,
                clim=self.clim,
                *self.args,
                **self.kwargs
            )
            arrow_head = pts_gdf.hvplot(
                geo=self.hvplot_is_geo,
                tiles=None,
                marker="triangle",
                angle=dim("triangle_angle"),
                size=self.marker_size,
                clim=self.clim,
                *self.args,
                **self.kwargs
            )
            return arrow_shaft * arrow_head
        else:
            plots = []
            for i in range(len(ids)):
                tmp = pts_gdf[pts_gdf[self.traj_id_col_name] == ids[i]]
                arrow_shaft = tmp.hvplot(
                    geo=self.hvplot_is_geo,
                    tiles=None,
                    marker="dash",
                    angle=dim("dash_angle"),
                    size=self.marker_size * 1.7,
                    line_width=self.marker_size / 70.0,
                    color=self.get_color(i),
                    *self.args,
                    **self.kwargs
                )
                arrow_head = tmp.hvplot(
                    geo=self.hvplot_is_geo,
                    tiles=None,
                    marker="triangle",
                    angle=dim("triangle_angle"),
                    size=self.marker_size,
                    color=self.get_color(i),
                    *self.args,
                    **self.kwargs
                )
                plots.append(arrow_shaft * arrow_head)
            return Overlay(plots)

    def set_default_cmaps(self, ids=None):
        from holoviews import Cycle

        Cycle.default_cycles["default_colors"] = self.MPD_PALETTE
        if self.column == self.speed_col_name and "cmap" not in self.kwargs:
            self.kwargs["cmap"] = "Plasma"
        elif self.column is None and self.traj_id_col_name is not None:
            self.kwargs["c"] = self.traj_id_col_name
            if "cmap" not in self.kwargs:
                print("building colormap ...")
                self.kwargs["colormap"] = dict(zip(ids, self.MPD_PALETTE[: len(ids)]))
                print(self.kwargs["colormap"])
        if self.colormap:
            self.kwargs["colormap"] = self.colormap
        if "cmap" not in self.kwargs and "colormap" not in self.kwargs:
            self.kwargs["cmap"] = self.MPD_PALETTE
