# -*- coding: utf-8 -*-
import warnings

from pandas import concat
from copy import copy
from geopandas import GeoDataFrame
from .trajectory import (
    Trajectory,
    SPEED_COL_NAME,
    DIRECTION_COL_NAME,
    DISTANCE_COL_NAME,
    ACCELERATION_COL_NAME,
    ANGULAR_DIFFERENCE_COL_NAME,
    TIMEDELTA_COL_NAME,
)
from .trajectory_plotter import _TrajectoryPlotter
from .unit_utils import UNITS
from .io import gdf_to_mf_json


@staticmethod
def traj_to_tc(traj):
    return TrajectoryCollection([traj])


class TrajectoryCollection:
    def __init__(
        self,
        data,
        traj_id_col=None,
        obj_id_col=None,
        t=None,
        x=None,
        y=None,
        crs="epsg:4326",
        min_length=0,
        min_duration=None,
    ):
        """
        Create TrajectoryCollection from list of trajectories or GeoDataFrame

        Parameters
        ----------
        data : list[Trajectory] or GeoDataFrame or DataFrame
            List of Trajectory objects or a GeoDataFrame with trajectory IDs,
            point geometry column and timestamp index
        traj_id_col : string
            Name of the GeoDataFrame column containing trajectory IDs
        obj_id_col : string
            Name of the GeoDataFrame column containing moving object IDs
        t : string
            Name of the DataFrame column containing the timestamp
        x : string
            Name of the DataFrame column containing the x coordinate
        y : string
            Name of the DataFrame column containing the y coordinate
        crs : string
            CRS of the x/y coordinates
        min_length : numeric
            Desired minimum length of trajectories. Length is calculated using
            CRS units, except if the CRS is geographic (e.g. EPSG:4326 WGS84)
            then length is calculated in meters.
            (Shorter trajectories are discarded.)
        min_duration : timedelta
            Desired minimum duration of trajectories. (Shorter trajectories are
            discarded.)

        Examples
        --------
        >>> import geopandas as read_file
        >>> import movingpandas as mpd
        >>>
        >>> gdf = read_file('data.gpkg')
        >>> collection = mpd.TrajectoryCollection(gdf, 'trajectory_id', t='t')
        """
        self.min_length = min_length
        self.min_duration = min_duration
        self.t = t
        if type(data) == list:
            if min_length > 0:
                self.trajectories = [
                    traj for traj in data if traj.is_long_enough(min_length)
                ]
            else:
                self.trajectories = data
            if min_duration:
                self.trajectories = [
                    traj
                    for traj in self.trajectories
                    if traj.get_duration() >= min_duration
                ]
        else:
            self.trajectories = self._df_to_trajectories(
                data, traj_id_col, obj_id_col, t, x, y, crs
            )

    def __len__(self):
        return len(self.trajectories)

    def __str__(self):
        return f"TrajectoryCollection with {self.__len__()} trajectories"

    def __repr__(self):
        return self.__str__()

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
                raise ValueError(
                    f"Trajectory with length >= 2 expected: "
                    f"got length {len(traj.df)}"
                )

    def copy(self):
        """
        Return a copy of the trajectory collection.

        Returns
        -------
        TrajectoryCollection
        """
        trajectories = [traj.copy() for traj in self.trajectories]
        # NOTE: traj_id_col and obj_id_col not needed since trajectories are
        # already preprocessed on __init__().
        return TrajectoryCollection(trajectories, min_length=self.min_length)

    def drop(self, **kwargs):
        """
        Drop columns or rows from the trajectories' DataFrames

        Examples
        --------

        >>> tc.drop(columns=['abc','def'])
        """
        for traj in self.trajectories:
            traj.drop(**kwargs)

    def to_point_gdf(self):
        """
        Return the trajectories' points as GeoDataFrame.

        Returns
        -------
        GeoDataFrame
        """
        gdfs = [traj.to_point_gdf() for traj in self.trajectories]
        return concat(gdfs)

    def to_line_gdf(self, columns=None):
        """
        Return the trajectories' line segments as GeoDataFrame.

        Returns
        -------
        GeoDataFrame
        """
        gdfs = [traj.to_line_gdf(columns) for traj in self.trajectories]
        gdf = concat(gdfs)
        gdf.reset_index(drop=True, inplace=True)
        return gdf

    def to_traj_gdf(self, wkt=False, agg=False):
        """
        Return a GeoDataFrame with one row per Trajectory within the
        TrajectoryCollection

        Returns
        -------
        GeoDataFrame
        """
        gdfs = [traj.to_traj_gdf(wkt, agg) for traj in self.trajectories]
        gdf = concat(gdfs)
        gdf.reset_index(drop=True, inplace=True)
        return gdf

    def to_mf_json(self, datetime_to_str=True, temporal_columns=None):
        """
        Converts a TrajectoryCollection to a dictionary compatible with the Moving
        Features JSON (MF-JSON) specification.

        Examples
        --------

        >>> tc.to_mf_json()

        Returns:
            dict: The MF-JSON representation of the GeoDataFrame as a dictionary.
        """
        tmp = self.to_point_gdf()
        t = tmp.index.name
        mf_json = gdf_to_mf_json(
            tmp.reset_index(),
            self.get_traj_id_col(),
            t,
            datetime_to_str=datetime_to_str,
            temporal_columns=temporal_columns,
        )
        return mf_json

    def _df_to_trajectories(self, df, traj_id_col, obj_id_col, t, x, y, crs):
        trajectories = []
        for traj_id, values in df.groupby(traj_id_col):
            if len(values) < 2:
                continue
            if obj_id_col in values.columns:
                obj_id = values.iloc[0][obj_id_col]
            else:
                obj_id = None
            trajectory = Trajectory(
                values,
                traj_id,
                traj_id_col=traj_id_col,
                obj_id=obj_id,
                t=t,
                x=x,
                y=y,
                crs=crs,
            )
            if self.min_duration:
                if trajectory.get_duration() < self.min_duration:
                    continue
            if len(trajectory.df) < 2:
                continue
            if self.min_length > 0:
                if trajectory.get_length() < self.min_length:
                    continue
            if isinstance(df, GeoDataFrame):
                trajectory.crs = df.crs
            else:
                trajectory.crs = crs
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

    def get_trajectories(self, obj_id):
        """
        Return the trajectories of the requested moving object

        Parameters
        ----------
        obj_id : any
            Moving object ID

        Returns
        -------
        TrajectoryCollection
        """
        trajs = []
        for traj in self:
            if traj.obj_id == obj_id:
                trajs.append(traj)
        return TrajectoryCollection(trajs)

    def get_crs(self):
        """
        Return the CRS of the trajectories
        """
        return self.trajectories[0].get_crs()

    def is_latlon(self):
        """
        Return True if the trajectory CRS is geographic (e.g. EPSG:4326 WGS84)
        """
        return self.trajectories[0].is_latlon()

    def get_column_names(self):
        """
        Return the list of column names

        Returns
        -------
        list
        """
        return self.trajectories[0].df.columns

    def get_traj_id_col(self):
        """
        Return name of the trajectory ID column

        Returns
        -------
        string
        """
        return self.trajectories[0].get_traj_id_col()

    def get_geom_col(self):
        """
        Return name of the geometry column

        Returns
        -------
        string
        """
        return self.trajectories[0].get_geom_col()

    def get_speed_col(self):
        """
        Return name of the speed column

        Returns
        -------
        string
        """
        return self.trajectories[0].get_speed_col()

    def get_direction_col(self):
        """
        Return name of the direction column

        Returns
        -------
        string
        """
        return self.trajectories[0].get_direction_col()

    def get_locations_at(self, t, with_direction=False):
        """
        Returns GeoDataFrame with trajectory locations at the specified timestamp

        Parameters
        ----------
        t : datetime.datetime
            Timestamp to extract trajectory locations for

        Returns
        -------
        GeoDataFrame
            Trajectory locations at timestamp t
        """
        result = []

        if with_direction:
            direction_col = self.get_direction_col()
            direction_missing = direction_col not in self.get_column_names()

        for traj in self:
            if t == "start":
                tmp = traj.copy()
                if with_direction and direction_missing:
                    tmp.df = tmp.df.head(2)
                    tmp.add_direction(name=direction_col)
                x = tmp.get_row_at(tmp.get_start_time())
            elif t == "end":
                tmp = traj.copy()
                if with_direction and direction_missing:
                    tmp.df = tmp.df.tail(2)
                    tmp.add_direction(name=direction_col)
                x = tmp.get_row_at(tmp.get_end_time())
            else:
                if t < traj.get_start_time() or t > traj.get_end_time():
                    continue
                tmp = traj.copy()
                if with_direction and direction_missing:
                    tmp.add_direction(name=direction_col)
                x = tmp.get_row_at(t)
            result.append(x.to_frame().T)

        if result:
            df = concat(result)
            # Move temporal index to column t
            t = self.t or "t"
            df.reset_index(inplace=True)
            df.rename(columns={"index": t}, inplace=True)

            gdf = GeoDataFrame(df)
            gdf.set_crs(self.get_crs(), inplace=True)
        else:
            gdf = GeoDataFrame()
        return gdf

    def get_start_locations(self, with_direction=False):
        """
        Returns GeoDataFrame with trajectory start locations

        Returns
        -------
        GeoDataFrame
            Trajectory start locations
        """
        return self.get_locations_at("start", with_direction)

    def get_end_locations(self, with_direction=False):
        """
        Returns GeoDataFrame with trajectory end locations

        Returns
        -------
        GeoDataFrame
            Trajectory end locations
        """
        return self.get_locations_at("end", with_direction)

    def get_segments_between(self, t1, t2):
        """
        Return Trajectory segments between times t1 and t2.

        Parameters
        ----------
        t1 : datetime.datetime
            Start time for the segments
        t2 : datetime.datetime
            End time for the segments

        Returns
        -------
        TrajectoryCollection
            Extracted trajectory segments
        """
        segments = []
        for traj in self:
            if t1 > traj.get_end_time() or t2 < traj.get_start_time():
                continue
            try:
                seg = traj.get_segment_between(t1, t2)
            except ValueError:
                continue
            segments.append(seg)
        result = copy(self)
        result.trajectories = segments
        return result

    def get_intersecting(self, polygon):
        """
        Return trajectories that intersect the given polygon.

        Parameters
        ----------
        polygon : shapely.geometry.Polygon
            Polygon to intersect with
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
            except:  # noqa E722
                pass
        result = copy(self)
        result.trajectories = intersecting
        return result

    def intersection(self, feature, point_based=False):
        """
        Intersect trajectories with the given polygon feature.

        Feature attributes are appended to the trajectory's DataFrame.

        By default, the trajectory's line representation is clipped by the
        polygon. If pointbased=True, the trajectory's point representation is
        used instead, leading to shorter segments.

        Parameters
        ----------
        feature : shapely Feature
            Feature to intersect with
        point_based : bool
            Clipping method

        Returns
        -------
        TrajectoryCollection
            Intersecting trajectory segments
        """
        intersections = []
        for traj in self:
            try:
                for intersect in traj.intersection(feature, point_based):
                    if (
                        intersect.get_length() >= self.min_length
                    ):  # TODO also test min_duration
                        intersections.append(intersect)
            except:  # noqa E722
                pass
        result = copy(self)
        result.trajectories = intersections
        return result

    def clip(self, polygon, point_based=False):
        """
        Clip trajectories by the given polygon.

        Parameters
        ----------
        polygon : shapely.geometry.Polygon
            Polygon to clip with
        point_based : bool
            Clipping method

        Returns
        -------
        TrajectoryCollection
            Resulting clipped trajectory segments
        """
        clipped = []
        for traj in self:
            try:
                for intersect in traj.clip(polygon, point_based):
                    if (
                        intersect.get_length() >= self.min_length
                    ):  # TODO also test min_duration
                        clipped.append(intersect)
            except:  # noqa E722
                pass
        result = copy(self)
        result.trajectories = clipped
        return result

    def filter(self, property_name, property_values):
        """
        Filter trajectories by property

        A property is a value in the df that is constant for the whole trajectory.
        The filter only checks if the value on the first row equals the requested
        property value.

        Parameters
        ----------
        property_name : string
            Name of the DataFrame column containing the property
        property_values : list(any)
            Desired property values

        Returns
        -------
        TrajectoryCollection
            Trajectories that fulfill the filter criteria

        Examples
        --------
        >>> filtered = trajectory_collection.filter('object_type', ['TypeA', 'TypeB'])
        """
        filtered = []
        for traj in self:
            if type(property_values) == list:
                if traj.df.iloc[0][property_name] in property_values:
                    filtered.append(traj)
            else:
                if traj.df.iloc[0][property_name] == property_values:
                    filtered.append(traj)

        result = copy(self)
        result.trajectories = filtered
        return result

    def add_speed(
        self,
        overwrite=False,
        name=SPEED_COL_NAME,
        units=UNITS(),
        n_processes=1,
        **kwargs,
    ):
        """
        Add speed column and values to the trajectories.

        Speed is calculated as CRS units per second, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then speed is calculated in meters per second.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing speed values (default: False)
        name : str
            Name of the speed column (default: speed)
        units : tuple(str)
            Units in which to calculate speed

            distance : str
                Abbreviation for the distance unit
                (default: CRS units, or metres if geographic)
            time : str
                Abbreviation for the time unit (default: seconds)

            For more info, check the list of supported units at
            https://movingpandas.org/units
        n_processes : int or None, optional
            Number of processes to use for computation (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing.
        n_threads : int, optional
            DEPRECATED. Use `n_processes` instead. This parameter will be
            removed in a future version.

        Raises
        ------
        ValueError
            If both `n_processes` and the deprecated `n_threads` are provided.
        """
        n_processes = self._add_deprecation_warning_for_n_threads(
            n_processes=n_processes, **kwargs
        )

        if n_processes > 1 or n_processes is None:
            self._multiprocess(self._add_speed, n_processes, name, units, overwrite)
        else:
            self._add_speed(self.trajectories, name, units, overwrite)
        return self

    def _add_speed(self, trajs, name, units, overwrite):
        for traj in trajs:
            traj.add_speed(name=name, units=units, overwrite=overwrite)
        return trajs

    def _multiprocess(self, fun, n_processes, name, units, overwrite):
        from multiprocessing import Pool
        from itertools import repeat
        from movingpandas.tools._multi_threading import split_list

        p = Pool(n_processes)
        data = split_list(self.trajectories, n_processes)
        self.trajectories = []
        args_iter = zip(data, repeat(name), repeat(units), repeat(overwrite))
        results = []
        for added in p.starmap(fun, args_iter):
            results.extend(added)
        self.trajectories = results
        return results

    def add_direction(
        self, overwrite=False, name=DIRECTION_COL_NAME, n_processes=1, **kwargs
    ):
        """
        Add direction column and values to the trajectories.

        The direction is calculated between consecutive locations.
        Direction values are in degrees, starting North turning clockwise.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing direction values (default: False)
        name : str
            Name of the direction column (default: "direction")
        n_processes : int or None, optional
            Number of processes to use for computation (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing.
        n_threads : int, optional
            DEPRECATED. Use `n_processes` instead. This parameter will be
            removed in a future version.
        """
        n_processes = self._add_deprecation_warning_for_n_threads(
            n_processes=n_processes, **kwargs
        )

        if n_processes > 1 or n_processes is None:
            self._multiprocess(
                self._add_direction,
                n_processes,
                name,
                UNITS(),
                overwrite,
            )
        else:
            self._add_direction(self.trajectories, name, UNITS(), overwrite)

        return self

    def _add_direction(self, trajs, name, units, overwrite):
        for traj in trajs:
            traj.add_direction(overwrite=overwrite, name=name)
        return trajs

    def add_angular_difference(
        self, overwrite=False, name=ANGULAR_DIFFERENCE_COL_NAME, n_processes=1, **kwargs
    ):
        """
        Add angular difference to the trajectory's DataFrame.

        Angular difference is calculated as the absolute smaller angle
        between direction for points along the trajectory.
        Values are [0, 180.0]

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing angular difference values (default: False)
        name : str
            Name of the angular_difference column (default: "angular_difference")
        n_processes : int or None, optional
            Number of processes to use for computation (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing.
        n_threads : int, optional
            DEPRECATED. Use `n_processes` instead. This parameter will be
            removed in a future version.
        """
        n_processes = self._add_deprecation_warning_for_n_threads(
            n_processes=n_processes, **kwargs
        )

        if n_processes > 1 or n_processes is None:
            self._multiprocess(
                self._add_angular_difference, n_processes, name, UNITS(), overwrite
            )
        else:
            self._add_angular_difference(self.trajectories, name, UNITS(), overwrite)

        return self

    def _add_angular_difference(self, trajs, name, units, overwrite):
        for traj in trajs:
            traj.add_angular_difference(overwrite=overwrite, name=name)
        return trajs

    def add_acceleration(
        self,
        overwrite=False,
        name=ACCELERATION_COL_NAME,
        units=UNITS(),
        n_processes=1,
        **kwargs,
    ):
        """
        Add acceleration column and values to the trajectories.

        Acceleration is calculated as CRS units per second squared,
        except if the CRS is geographic (e.g. EPSG:4326 WGS84) then acceleration is
        calculated in meters per second squared.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing acceleration values (default: False)
        name : str
            Name of the acceleration column (default: "acceleration")
        units : tuple(str)
            Units in which to calculate acceleration

            distance : str
                Abbreviation for the distance unit
                (default: CRS units, or metres if geographic)
            time : str
                Abbreviation for the time unit (default: seconds)
            time2 : str
                Abbreviation for the second time unit (default: seconds)

            For more info, check the list of supported units at
            https://movingpandas.org/units
        n_processes : int or None, optional
            Number of processes to use for computation (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing.
        n_threads : int, optional
            DEPRECATED. Use `n_processes` instead. This parameter will be
            removed in a future version.
        """
        n_processes = self._add_deprecation_warning_for_n_threads(
            n_processes=n_processes, **kwargs
        )

        if n_processes > 1 or n_processes is None:
            self._multiprocess(
                self._add_acceleration, n_processes, name, units, overwrite
            )
        else:
            self._add_acceleration(self.trajectories, name, units, overwrite)

        return self

    def _add_acceleration(self, trajs, name, units, overwrite):
        for traj in trajs:
            traj.add_acceleration(overwrite=overwrite, name=name, units=units)
        return trajs

    def add_distance(
        self,
        overwrite=False,
        name=DISTANCE_COL_NAME,
        units=None,
        n_processes=1,
        **kwargs,
    ):
        """
        Add distance column and values to the trajectories.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing distance values (default: False)
        name : str
            Name of the distance column (default: "distance")
        units : str
            Units in which to calculate distance values (default: CRS units)
            For more info, check the list of supported units at
            https://movingpandas.org/units
        n_processes : int or None, optional
            Number of processes to use for computation (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing.
        n_threads : int, optional
            DEPRECATED. Use `n_processes` instead. This parameter will be
            removed in a future version.
        """
        n_processes = self._add_deprecation_warning_for_n_threads(n_processes, **kwargs)

        if n_processes > 1 or n_processes is None:
            self._multiprocess(self._add_distance, n_processes, name, units, overwrite)
        else:
            self._add_distance(self.trajectories, name, units, overwrite)
        return self

    def _add_distance(self, trajs, name, units, overwrite):
        for traj in trajs:
            traj.add_distance(overwrite=overwrite, name=name, units=units)
        return trajs

    def add_timedelta(
        self, overwrite=False, name=TIMEDELTA_COL_NAME, n_processes=1, **kwargs
    ):
        """
        Add timedelta column and values to the trajectories.

        Timedelta is calculated as the time difference between the current
        and the previous row. Values are instances of datetime.timedelta.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing timedelta values (default: False)
        name : str
            Name of the timedelta column (default: "timedelta")
        n_processes : int or None, optional
            Number of processes to use for computation (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing.
        n_threads : int, optional
            DEPRECATED. Use `n_processes` instead. This parameter will be
            removed in a future version.
        """
        n_processes = self._add_deprecation_warning_for_n_threads(
            n_processes=n_processes, **kwargs
        )

        if n_processes > 1 or n_processes is None:
            self._multiprocess(
                self._add_timedelta, n_processes, name, UNITS(), overwrite
            )
        else:
            self._add_timedelta(self.trajectories, name, UNITS(), overwrite)
        return self

    def _add_timedelta(self, trajs, name, units, overwrite):
        for traj in trajs:
            traj.add_timedelta(overwrite=overwrite, name=name)
        return trajs

    def add_traj_id(self, overwrite=False):
        """
        Add trajectory id column and values to the trajectories.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing trajectory id values (default: False)
        """
        for traj in self:
            traj.add_traj_id(overwrite)
        return self

    def get_min(self, column):
        """
        Return minimum value in the provided DataFrame column over all trajectories

        Parameters
        ----------
        column : string
            Name of the DataFrame column

        Returns
        -------
        Sortable
            Minimum value
        """
        return min([traj.df[column].min() for traj in self])

    def get_max(self, column):
        """
        Return maximum value in the provided DataFrame column over all trajectories

        Parameters
        ----------
        column : string
            Name of the DataFrame column

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

        Plot speed along trajectories (scaling the colormap to specific min/max values):

        >>> trajectory_collection.plot(column='speed', vmin=0, vmax=20)
        """
        return _TrajectoryPlotter(self, *args, **kwargs).plot()

    def explore(self, *args, **kwargs):
        """
        Generate a plot using GeoPandas explore (folium/leaflet.js)
        https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.explore.html

        Parameters
        ----------
        args :
            These parameters will be passed to GeoPandas explore
        kwargs :
            These parameters will be passed to GeoPandas explore

        Returns
        -------
        m : folium.folium.Map
            folium Map instance

        Examples
        --------
        Plot speed along trajectory (with legend and specified figure size):

        >>> trajectory_collection.explore(column='speed', vmax=20, tiles="CartoDB positron")
        """  # noqa: E501
        return _TrajectoryPlotter(self, *args, **kwargs).explore()

    def hvplot(self, *args, **kwargs):
        """
        Generate an interactive trajectory plot.

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter

            To customize the plots, check the list of supported colormaps:
            https://holoviews.org/user_guide/Colormaps.html#available-colormaps

        Examples
        --------
        Plot speed along trajectories (with legend and specified figure size):

        >>> collection.hvplot(c='speed', line_width=7.0, width=700, height=400,
                              colorbar=True)

        Plot speed along trajectories (scaling the colormap to specific min/max values):

        >>> trajectory_collection.plot(column='speed', clim=(0,20))
        """  # noqa: E501
        return _TrajectoryPlotter(self, *args, **kwargs).hvplot()

    def hvplot_pts(self, *args, **kwargs):
        """
        Generate an interactive plot of trajectory points.

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter

            To customize the plots, check the list of supported colormaps:
            https://holoviews.org/user_guide/Colormaps.html#available-colormaps

        Examples
        --------
        Plot points colored by speed (with legend and specified figure size):

        >>> collection.hvplot_pts(c='speed', width=700, height=400, colorbar=True)
        """  # noqa: E501
        return _TrajectoryPlotter(self, *args, **kwargs).hvplot_pts()

    def _add_deprecation_warning_for_n_threads(self, n_processes, **kwargs):
        """Add a deprecation warning if `n_threads` is used and return `n_processes.`"""
        n_threads = kwargs.pop("n_threads", None)

        if n_threads is not None and n_processes != 1:
            raise ValueError(
                "You cannot pass both `n_threads` (deprecated) and `n_processes`. "
                "Please use only `n_processes`."
            )
        if n_threads is not None:
            warnings.warn(
                "`n_threads` is deprecated and will be removed in a future version. "
                "Please use `n_processes` instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            n_processes = n_threads

        return n_processes


def _get_location_at(traj, t, columns=None):
    loc = {
        "t": t,
        "geometry": traj.get_position_at(t),
        "traj_id": traj.id,
        "obj_id": traj.obj_id,
    }
    if columns and columns != [None]:
        for column in columns:
            loc[column] = traj.df.iloc[traj.df.index.get_loc(t, method="nearest")][
                column
            ]
    return loc
