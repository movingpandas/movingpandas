# -*- coding: utf-8 -*-

from pandas import concat
from copy import copy
from geopandas import GeoDataFrame
from .trajectory import Trajectory
from .trajectory_plotter import _TrajectoryCollectionPlotter


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
            Desired minimum length of trajectories. (Shorter trajectories are
            discarded.)
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
        if type(data) == list:
            self.trajectories = [
                traj for traj in data if traj.get_length() >= min_length
            ]
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
        return "TrajectoryCollection with {} trajectories".format(self.__len__())

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

    def to_point_gdf(self):
        """
        Return the trajectories' points as GeoDataFrame.

        Returns
        -------
        GeoDataFrame
        """
        gdfs = [traj.to_point_gdf() for traj in self.trajectories]
        return concat(gdfs)

    def to_line_gdf(self):
        """
        Return the trajectories' line segments as GeoDataFrame.

        Returns
        -------
        GeoDataFrame
        """
        gdfs = [traj.to_line_gdf() for traj in self.trajectories]
        gdf = concat(gdfs)
        gdf.reset_index(drop=True, inplace=True)
        return gdf

    def to_traj_gdf(self, wkt=False):
        """
        Return a GeoDataFrame with one row per Trajectory within the
        TrajectoryCollection

        Returns
        -------
        GeoDataFrame
        """
        gdfs = [traj.to_traj_gdf(wkt) for traj in self.trajectories]
        gdf = concat(gdfs)
        gdf.reset_index(drop=True, inplace=True)
        return gdf

    def _df_to_trajectories(self, df, traj_id_col, obj_id_col, t, x, y, crs):
        trajectories = []
        for traj_id, values in df.groupby([traj_id_col]):
            if len(values) < 2:
                continue
            if obj_id_col in values.columns:
                obj_id = values.iloc[0][obj_id_col]
            else:
                obj_id = None
            trajectory = Trajectory(
                values, traj_id, obj_id=obj_id, t=t, x=x, y=y, crs=crs
            )
            if self.min_duration:
                if trajectory.get_duration() < self.min_duration:
                    continue
            if (
                trajectory.get_length() < self.min_length
                or trajectory.df.geometry.count() < 2
            ):
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

    def get_geom_column_name(self):
        """
        Return name of the geometry column

        Returns
        -------
        string
        """
        return self.trajectories[0].get_geom_column_name()

    def get_locations_at(self, t):
        """
        Returns GeoDataFrame with trajectory locations at the specified timestamp

        Parameters
        ----------
        t : datetime.datetime

        Returns
        -------
        GeoDataFrame
            Trajectory locations at timestamp t
        """
        gdf = GeoDataFrame()
        for traj in self:
            if t == "start":
                x = traj.get_row_at(traj.get_start_time())
            elif t == "end":
                x = traj.get_row_at(traj.get_end_time())
            else:
                if t < traj.get_start_time() or t > traj.get_end_time():
                    continue
                x = traj.get_row_at(t)
            gdf = gdf.append(x)
        return GeoDataFrame(gdf)

    def get_start_locations(self):
        """
        Returns GeoDataFrame with trajectory start locations

        Returns
        -------
        GeoDataFrame
            Trajectory start locations
        """
        return self.get_locations_at("start")

    def get_end_locations(self):
        """
        Returns GeoDataFrame with trajectory end locations

        Returns
        -------
        GeoDataFrame
            Trajectory end locations
        """
        return self.get_locations_at("end")

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

    def add_speed(self, overwrite=False):
        """
        Add speed column and values to the trajectories.

        Speed is calculated as CRS units per second, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then speed is calculated in meters per second.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing speed values (default: False)
        """
        for traj in self:
            traj.add_speed(overwrite)

    def add_direction(self, overwrite=False):
        """
        Add direction column and values to the trajectories.

        The direction is calculated between consecutive locations.
        Direction values are in degrees, starting North turning clockwise.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing speed values (default: False)
        """
        for traj in self:
            traj.add_direction(overwrite)

    def add_traj_id(self, overwrite=False):
        """
        Add trajectory id column and values to the trajectories.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing speed values (default: False)
        """
        for traj in self:
            traj.add_traj_id(overwrite)

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

        >>> collection.hvplot(c='speed', line_width=7.0, width=700, height=400,
                              colorbar=True)
        """
        return _TrajectoryCollectionPlotter(self, *args, **kwargs).hvplot()


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
