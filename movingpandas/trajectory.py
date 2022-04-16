# -*- coding: utf-8 -*-

import warnings

from shapely.affinity import translate
from shapely.geometry import Point, LineString
from datetime import datetime
from pandas import DataFrame, to_datetime
from pandas.core.indexes.datetimes import DatetimeIndex
from geopandas import GeoDataFrame

try:
    from pyproj import CRS
except ImportError:
    from fiona.crs import from_epsg

from .overlay import clip, intersection, intersects, create_entry_and_exit_points
from .time_range_utils import SpatioTemporalRange
from .geometry_utils import (
    azimuth,
    calculate_initial_compass_bearing,
    measure_distance_geodesic,
    measure_distance_euclidean,
)
from .trajectory_plotter import _TrajectoryPlotter

TRAJ_ID_COL_NAME = "traj_id"
SPEED_COL_NAME = "speed"
DIRECTION_COL_NAME = "direction"
DISTANCE_COL_NAME = "distance"


class MissingCRSWarning(UserWarning, ValueError):
    pass


class Trajectory:
    def __init__(
        self,
        df,
        traj_id,
        obj_id=None,
        t=None,
        x=None,
        y=None,
        crs="epsg:4326",
        parent=None,
    ):
        """
        Create Trajectory from GeoDataFrame or DataFrame.

        Parameters
        ----------
        df : GeoDataFrame or DataFrame
            GeoDataFrame with point geometry column and timestamp index
        traj_id : any
            Trajectory ID
        obj_id : any
            Moving object ID
        t : string
            Name of the DataFrame column containing the timestamp
        x : string
            Name of the DataFrame column containing the x coordinate
        y : string
            Name of the DataFrame column containing the y coordinate
        crs : string
            CRS of the x/y coordinates
        parent : Trajectory
            Parent trajectory

        Examples
        --------
        Creating a trajectory from scratch:

        >>> import pandas as pd
        >>> import geopandas as gpd
        >>> import movingpandas as mpd
        >>> from fiona.crs import from_epsg
        >>>
        >>> df = pd.DataFrame([
        ...     {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
        ...     {'geometry':Point(6,0), 't':datetime(2018,1,1,12,6,0)},
        ...     {'geometry':Point(6,6), 't':datetime(2018,1,1,12,10,0)},
        ...     {'geometry':Point(9,9), 't':datetime(2018,1,1,12,15,0)}
        ... ]).set_index('t')
        >>> gdf = gpd.GeoDataFrame(df, crs=from_epsg(31256))
        >>> traj = mpd.Trajectory(gdf, 1)

        For more examples, see the tutorial notebooks_.

        .. _notebooks: https://mybinder.org/v2/gh/anitagraser/movingpandas/binder-tag?filepath=tutorials/0_getting_started.ipynb
        """  # noqa: E501
        if len(df) < 2:
            raise ValueError("The input DataFrame must have at least two rows.")
        if not isinstance(df, GeoDataFrame):
            if x is None or y is None:
                raise ValueError(
                    "The input DataFrame needs to be a GeoDataFrame or x and y columns"
                    "need to be specified."
                )
            df = GeoDataFrame(
                df.drop([x, y], axis=1),
                crs=crs,
                geometry=[Point(xy) for xy in zip(df[x], df[y])],
            )
        if not isinstance(df.index, DatetimeIndex):
            if t is None:
                raise TypeError(
                    "The input DataFrame needs a DatetimeIndex or a timestamp column"
                    "needs to be specified. Use Pandas' set_index() method to create an"
                    "index or specify the timestamp column name."
                )
            df[t] = to_datetime(df[t])
            df = df.set_index(t).tz_localize(None)

        self.id = traj_id
        self.obj_id = obj_id
        df.sort_index(inplace=True)
        self.df = df[~df.index.duplicated(keep="first")]
        self.crs = df.crs
        self.parent = parent
        if self.crs is None:
            warnings.warn(
                "Trajectory generated without CRS. Computations will use Euclidean"
                "distances.",
                category=MissingCRSWarning,
            )
            self.is_latlon = False
            return
        try:
            crs = CRS.from_user_input(self.crs)
            self.is_latlon = crs.is_geographic
        except NameError:
            self.is_latlon = self.crs["init"] == from_epsg(4326)["init"]

    def __str__(self):
        try:
            line = self.to_linestring()
        except RuntimeError:
            return "Invalid trajectory!"
        return (
            "Trajectory {id} ({t0} to {tn}) | Size: {n} | Length: {len:.1f}m\n"
            "Bounds: {bbox}\n{wkt}".format(
                id=self.id,
                t0=self.get_start_time(),
                tn=self.get_end_time(),
                n=self.size(),
                wkt=line.wkt[:100],
                bbox=self.get_bbox(),
                len=self.get_length(),
            )
        )

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.get_length()

    def __eq__(self, other):
        # TODO: make bullet proof
        return (
            str(self) == str(other)
            and self.crs == other.crs
            and self.parent == other.parent
        )

    def size(self):
        """
        Returns number of rows in Trajectory.df

        Returns
        -------
        size : int
            Number of rows
        """
        return len(self.df.index)

    def copy(self):
        """
        Return a copy of the trajectory.

        Returns
        -------
        Trajectory
        """
        return Trajectory(self.df.copy(), self.id, parent=self.parent)

    def plot(self, *args, **kwargs):
        """
        Generate a plot using GeoPandas default plotting (Matplotlib).

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter

        Returns
        -------
        Matplotlib plot

        Examples
        --------
        Plot speed along trajectory (with legend and specified figure size):

        >>> trajectory.plot(column='speed', legend=True, figsize=(9,5))
        """
        return _TrajectoryPlotter(self, *args, **kwargs).plot()

    def hvplot(self, *args, **kwargs):
        """
        Generate an interactive plot using HoloViews.

        The following parameters are set by default: geo=True, tiles='OSM'.

        Parameters
        ----------
        args :
            These parameters will be passed to the TrajectoryPlotter
        kwargs :
            These parameters will be passed to the TrajectoryPlotter

        Returns
        -------
        Holoviews plot

        Examples
        --------
        Plot speed along trajectory (with legend and specified figure size):

        >>> trajectory.hvplot(c='speed', line_width=7.0, width=700, height=400, colorbar=True)
        """  # noqa: E501
        return _TrajectoryPlotter(self, *args, **kwargs).hvplot()

    def is_valid(self):
        """
        Return whether the trajectory meets minimum requirements.

        Returns
        -------
        bool
        """
        if len(self.df) < 2:
            return False
        if not self.get_start_time() < self.get_end_time():
            return False
        return True

    def to_crs(self, crs):
        """
        Returns the trajectory reprojected to the target CRS.

        Parameters
        ----------
        crs : pyproj.CRS
            Target coordinate reference system

        Returns
        -------
        Trajectory

        Examples
        --------
        Reproject a trajectory to EPSG:4088

        >>> from pyproj import CRS
        >>> reprojected = trajectory.to_crs(CRS(4088))
        """
        temp = self.copy()
        temp.crs = crs
        temp.df = temp.df.to_crs(crs)
        if type(crs) == CRS:
            temp.is_latlon = crs.is_geographic
        else:
            temp.is_latlon = crs["init"] == from_epsg(4326)["init"]
        return temp

    def get_speed_column_name(self):
        """
        Return name of the speed column

        Returns
        -------
        string
        """
        if hasattr(self, "speed_col_name"):
            return self.speed_col_name
        else:
            return SPEED_COL_NAME

    def get_distance_column_name(self):
        """
        Return name of the distance column

        Returns
        -------
        string
        """
        if hasattr(self, "distance_col_name"):
            return self.distance_col_name
        else:
            return DISTANCE_COL_NAME

    def get_direction_column_name(self):
        """
        Return name of the direction column

        Returns
        -------
        string
        """
        if hasattr(self, "direction_col_name"):
            return self.direction_col_name
        else:
            return DIRECTION_COL_NAME

    def get_geom_column_name(self):
        """
        Return name of the geometry column

        Returns
        -------
        string
        """
        return self.df.geometry.name

    def to_linestring(self):
        """
        Return trajectory geometry as LineString.

        Returns
        -------
        shapely LineString
        """
        try:
            return point_gdf_to_linestring(self.df, self.get_geom_column_name())
        except RuntimeError:
            raise RuntimeError("Cannot generate LineString")

    def to_linestringm_wkt(self):
        """
        Return the WKT string of the trajectory LineStringM representation.

        Returns
        -------
        string
            WKT of trajectory as LineStringM
        """
        # Shapely only supports x, y, z. Therefore, this is a bit hacky!
        coords = ""
        for index, row in self.df.iterrows():
            pt = row[self.get_geom_column_name()]
            t = to_unixtime(index)
            coords += "{} {} {}, ".format(pt.x, pt.y, t)
        wkt = "LINESTRING M ({})".format(coords[:-2])
        return wkt

    def to_point_gdf(self):
        """
        Return the trajectory's points as GeoDataFrame.

        Returns
        -------
        GeoDataFrame
        """
        return self.df

    def to_line_gdf(self):
        """
        Return the trajectory's line segments as GeoDataFrame.

        Returns
        -------
        GeoDataFrame
        """
        line_gdf = self._to_line_df()
        line_gdf.drop(columns=[self.get_geom_column_name(), "prev_pt"], inplace=True)
        line_gdf.reset_index(drop=True, inplace=True)
        line_gdf.rename(columns={"line": "geometry"}, inplace=True)
        line_gdf.set_geometry("geometry", inplace=True)
        return line_gdf

    def to_traj_gdf(self, wkt=False):
        """
        Return a GeoDataFrame with one row containing the trajectory as a
        single LineString.

        Returns
        -------
        GeoDataFrame
        """
        properties = {
            TRAJ_ID_COL_NAME: self.id,
            "start_t": self.get_start_time(),
            "end_t": self.get_end_time(),
            "geometry": self.to_linestring(),
            "length": self.get_length(),
            "direction": self.get_direction(),
        }
        if wkt:
            properties["wkt"] = self.to_linestringm_wkt()
        df = DataFrame([properties])
        traj_gdf = GeoDataFrame(df, crs=self.crs)
        return traj_gdf

    def get_start_location(self):
        """
        Return the trajectory's start location.

        Returns
        -------
        shapely Point
            Trajectory start location
        """
        return self.df.geometry.iloc[0]

    def get_end_location(self):
        """Return the trajectory's end location.

        Returns
        -------
        shapely Point
            Trajectory end location
        """
        return self.df.geometry.iloc[-1]

    def get_bbox(self):
        """
        Return the trajectory's bounding box.

        Returns
        -------
        tuple
            Bounding box values (minx, miny, maxx, maxy)
        """
        return self.to_linestring().bounds  # (minx, miny, maxx, maxy)

    def get_start_time(self):
        """
        Return the trajectory's start time.

        Returns
        -------
        datetime.datetime
            Trajectory start time
        """
        return self.df.index.min().to_pydatetime()

    def get_end_time(self):
        """
        Return the trajectory's end time.

        Returns
        -------
        datetime.datetime
            Trajectory end time
        """
        return self.df.index.max().to_pydatetime()

    def get_duration(self):
        """
        Return the trajectory's duration from start to end.

        Returns
        -------
        datetime.timedelta
            Trajectory duration
        """
        return self.get_end_time() - self.get_start_time()

    def get_row_at(self, t, method="nearest"):
        """
        Return row of the trajectory's DataFrame at time t.

        Parameters
        ----------
        t : datetime.datetime
            Timestamp to extract a row for
        method : str
            Interpolation method (Pandas get_loc method)

        Returns
        -------
        Pandas series
            Row of the DataFrame at time t
        """
        try:
            return self.df.loc[t]
        except KeyError:
            index = self.df.index.sort_values().drop_duplicates()
            idx = index.get_indexer([t], method=method)[0]
            return self.df.iloc[idx]

    def interpolate_position_at(self, t):
        """
        Compute and return interpolated position at time t.

        Parameters
        ----------
        t : datetime.datetime
            Timestamp to interpolate at

        Returns
        -------
        shapely Point
            Interpolated position along the trajectory at time t
        """
        prev_row = self.get_row_at(t, "ffill")
        next_row = self.get_row_at(t, "bfill")
        t_diff = next_row.name - prev_row.name
        t_diff_at = t - prev_row.name
        line = LineString(
            [
                prev_row[self.get_geom_column_name()],
                next_row[self.get_geom_column_name()],
            ]
        )
        if t_diff == 0 or line.length == 0:
            return prev_row[self.get_geom_column_name()]
        interpolated_position = line.interpolate(t_diff_at / t_diff * line.length)
        return interpolated_position

    def get_position_at(self, t, method="interpolated"):
        """
        Compute and return position at time t.

        Parameters
        ----------
        t : datetime.datetime
            Timestamp to extract a row for
        method : str
            Interpolation method

        Returns
        -------
        shapely Point
            Position at time t

        Examples
        --------
        If the trajectory contains a position at the given timestamp, it is
        returned:

        >>> traj.get_position_at(datetime(2018, 1, 1, 12, 6))
        Point (6 0)

        If there is no trajectory position for the given timestamp, the default
        behaviour is to interpolate the location:

        >>> traj.get_position_at(datetime(2018, 1, 1, 12, 9))
        POINT (6 4.5)

        To get the trajectory position closest to the given timestamp, specify
        method='nearest':

        >>> traj.get_position_at(datetime(2018, 1, 1, 12, 9), method='nearest')
        POINT (6 6)
        """
        if method not in ["nearest", "interpolated", "ffill", "bfill"]:
            raise ValueError(
                "Invalid method {}. Must be one of [nearest, interpolated, ffill,"
                "bfill]".format(method)
            )
        if method == "interpolated":
            return self.interpolate_position_at(t)
        else:
            row = self.get_row_at(t, method)
            try:
                return row[self.get_geom_column_name()][0]
            except TypeError:
                return row[self.get_geom_column_name()]

    def get_linestring_between(self, t1, t2, method="interpolated"):
        """
        Return LineString of segment between times t1 and t2.

        Parameters
        ----------
        t1 : datetime.datetime
            Start time for the segment
        t2 : datetime.datetime
            End time for the segment
        method : str
            Extraction method

        Returns
        -------
        shapely LineString
            Extracted trajectory segment
        """
        if method not in ["interpolated", "within"]:
            raise ValueError(
                "Invalid split method {}. Must be one of [interpolated, within]".format(
                    method
                )
            )
        if method == "interpolated":
            st_range = SpatioTemporalRange(
                self.get_position_at(t1), self.get_position_at(t2), t1, t2
            )
            temp_df = create_entry_and_exit_points(self, st_range)
            temp_df = temp_df[t1:t2]
            return point_gdf_to_linestring(temp_df, self.get_geom_column_name())
        else:
            try:
                return point_gdf_to_linestring(
                    self.get_segment_between(t1, t2).df, self.get_geom_column_name()
                )
            except RuntimeError:
                raise RuntimeError(
                    "Cannot generate linestring between {0} and {1}".format(t1, t2)
                )

    def get_segment_between(self, t1, t2):
        """
        Return Trajectory segment between times t1 and t2.

        Parameters
        ----------
        t1 : datetime.datetime
            Start time for the segment
        t2 : datetime.datetime
            End time for the segment

        Returns
        -------
        Trajectory
            Extracted trajectory segment
        """
        segment = Trajectory(self.df[t1:t2], "{}_{}".format(self.id, t1), parent=self)
        if not segment.is_valid():
            raise RuntimeError(
                "Failed to extract valid trajectory segment between {} and {}".format(
                    t1, t2
                )
            )
        return segment

    def _compute_distance(self, row):
        pt0 = row["prev_pt"]
        pt1 = row[self.get_geom_column_name()]
        if not isinstance(pt0, Point):
            return 0.0
        if pt0 == pt1:
            return 0.0
        if self.is_latlon:
            dist_meters = measure_distance_geodesic(pt0, pt1)
        else:  # The following distance will be in CRS units that might not be meters!
            dist_meters = measure_distance_euclidean(pt0, pt1)
        return dist_meters

    def _add_prev_pt(self, force=True):
        """
        Create a shifted geometry column with previous positions.
        """
        if "prev_pt" not in self.df.columns or force:
            # TODO: decide on default enforcement behavior
            self.df = self.df.assign(prev_pt=self.df.geometry.shift())

    def get_length(self):
        """
        Return the length of the trajectory.

        Length is calculated using CRS units, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then length is calculated in metres.

        Returns
        -------
        float
            Length of the trajectory
        """
        temp_df = self.df.assign(prev_pt=self.df.geometry.shift())
        temp_df = temp_df.assign(
            dist_to_prev=temp_df.apply(self._compute_distance, axis=1)
        )
        return temp_df["dist_to_prev"].sum()

    def get_direction(self):
        """
        Return the direction of the trajectory.

        The direction is calculated between the trajectory's start and end
        location. Direction values are in degrees, starting North turning
        clockwise.

        Returns
        -------
        float
            Direction of the trajectory in degrees
        """
        pt0 = self.get_start_location()
        pt1 = self.get_end_location()
        if self.is_latlon:
            return calculate_initial_compass_bearing(pt0, pt1)
        else:
            return azimuth(pt0, pt1)

    def _compute_heading(self, row):
        pt0 = row["prev_pt"]
        pt1 = row[self.get_geom_column_name()]
        if not isinstance(pt0, Point):
            return 0.0
        if pt0 == pt1:
            return 0.0
        if self.is_latlon:
            return calculate_initial_compass_bearing(pt0, pt1)
        else:
            return azimuth(pt0, pt1)

    def _compute_speed(self, row):
        pt0 = row["prev_pt"]
        pt1 = row[self.get_geom_column_name()]
        if not isinstance(pt0, Point):
            return 0.0
        if not isinstance(pt1, Point):
            raise ValueError("Invalid trajectory! Got {} instead of point!".format(pt1))
        if pt0 == pt1:
            return 0.0
        if self.is_latlon:
            dist_meters = measure_distance_geodesic(pt0, pt1)
        else:  # The following distance will be in CRS units that might not be meters!
            dist_meters = measure_distance_euclidean(pt0, pt1)
        return dist_meters / row["delta_t"].total_seconds()

    def _connect_prev_pt_and_geometry(self, row):
        pt0 = row["prev_pt"]
        pt1 = row[self.get_geom_column_name()]
        if not isinstance(pt0, Point):
            return None
        if not isinstance(pt1, Point):
            raise ValueError("Invalid trajectory! Got {} instead of point!".format(pt1))
        if pt0 == pt1:
            # to avoid intersection issues with zero length lines
            pt1 = translate(pt1, 0.00000001, 0.00000001)
        return LineString(list(pt0.coords) + list(pt1.coords))

    def add_traj_id(self, overwrite=False):
        """
        Add trajectory id column and values to the trajectory's DataFrame.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing trajectory id values (default: False)
        """
        if TRAJ_ID_COL_NAME in self.df.columns and not overwrite:
            raise RuntimeError(
                f"Trajectory already contains a {TRAJ_ID_COL_NAME} column! "
                f"Use overwrite=True to overwrite exiting values."
            )
        self.df[TRAJ_ID_COL_NAME] = self.id

    def add_direction(self, overwrite=False, name=DIRECTION_COL_NAME):
        """
        Add direction column and values to the trajectory's DataFrame.

        The direction is calculated between consecutive locations.
        Direction values are in degrees, starting North turning clockwise.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing direction values (default: False)
        """
        self.direction_col_name = name
        if self.direction_col_name in self.df.columns and not overwrite:
            raise RuntimeError(
                f"Trajectory already has a column named {self.direction_col_name}! "
                "Use overwrite=True to overwrite exiting values or update the "
                "name arg."
            )
        self._add_prev_pt()
        self.df[name] = self.df.apply(self._compute_heading, axis=1)
        # set the direction in the first row to the direction of the second row
        self.df.at[self.get_start_time(), name] = self.df.iloc[1][name]
        self.df.drop(columns=["prev_pt"], inplace=True)

    def add_distance(self, overwrite=False, name=DISTANCE_COL_NAME):
        """
        Add distance column and values to the trajectory's DataFrame.

        Distance is calculated as CRS units, except if the CRS is geographic
        (e.g. EPSG:4326 WGS84) then distance is calculated in meters.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing distance values (default: False)
        """
        self.distance_col_name = name
        if self.distance_col_name in self.df.columns and not overwrite:
            raise RuntimeError(
                f"Trajectory already has a column named {self.distance_col_name}! "
                "Use overwrite=True to overwrite exiting values or update the "
                "name arg."
            )
        self.df = self._get_df_with_distance(name)

    def add_speed(self, overwrite=False, name=SPEED_COL_NAME):
        """
        Add speed column and values to the trajectory's DataFrame.

        Speed is calculated as CRS units per second, except if the CRS is
        geographic (e.g. EPSG:4326 WGS84) then speed is calculated in meters
        per second.

        Parameters
        ----------
        overwrite : bool
            Whether to overwrite existing speed values (default: False)
        name : str
            Name of the speed column (default: "speed")
        """
        self.speed_col_name = name
        if self.speed_col_name in self.df.columns and not overwrite:
            raise RuntimeError(
                f"Trajectory already has a column named {self.speed_col_name}! "
                f"Use overwrite=True to overwrite exiting values or update the "
                f"name arg."
            )
        self.df = self._get_df_with_speed(name)

    def _get_df_with_distance(self, name):
        temp_df = self.df.copy()
        temp_df = temp_df.assign(prev_pt=temp_df.geometry.shift())
        try:
            temp_df[name] = temp_df.apply(self._compute_distance, axis=1)
        except ValueError as e:
            raise e
        # set the distance in the first row to zero
        temp_df.at[self.get_start_time(), name] = 0
        temp_df = temp_df.drop(columns=["prev_pt"])
        return temp_df

    def _get_df_with_speed(self, name):
        temp_df = self.df.copy()
        temp_df = temp_df.assign(prev_pt=temp_df.geometry.shift())
        temp_df["t"] = temp_df.index
        times = temp_df.t
        temp_df = temp_df.drop(columns=["t"])
        temp_df = temp_df.assign(delta_t=times.diff().values)
        try:
            temp_df[name] = temp_df.apply(self._compute_speed, axis=1)
        except ValueError as e:
            raise e
        # set the speed in the first row to the speed of the second row
        temp_df.at[self.get_start_time(), name] = temp_df.iloc[1][name]
        temp_df = temp_df.drop(columns=["prev_pt", "delta_t"])
        return temp_df

    def intersects(self, polygon):
        """
        Return whether the trajectory intersects the given polygon.

        Parameters
        ----------
        polygon : shapely Polygon
            Polygon to test for intersections

        Returns
        -------
        bool
        """
        return intersects(self, polygon)

    def clip(self, polygon, point_based=False):
        """
        Return trajectory segments clipped by the given polygon.

        By default, the trajectory's line representation is clipped by the
        polygon. If pointbased=True, the trajectory's point representation is
        used instead, leading to shorter segments.

        Parameters
        ----------
        polygon : shapely Polygon
            Polygon to clip with
        point_based : bool
            Clipping method

        Returns
        -------
        TrajectoryCollection
            Clipped trajectory segments
        """
        from .trajectory_collection import TrajectoryCollection

        segments = clip(self, polygon, point_based)
        return TrajectoryCollection(segments)

    def intersection(self, feature, point_based=False):
        """
        Return the trajectory segments that intersects the given feature.

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
            Segments intersecting with the feature
        """
        from .trajectory_collection import TrajectoryCollection

        segments = intersection(self, feature, point_based)
        return TrajectoryCollection(segments)

    def apply_offset_seconds(self, column, offset):
        """
        Shift column by the specified offset in seconds.

        Parameters
        ----------
        column : str
            Name of the column to shift
        offset : int
            Number of seconds to shift by, can be positive or negative
        """
        self.df[column] = self.df[column].shift(offset, freq="1s")

    def apply_offset_minutes(self, column, offset):
        """
        Shift column by the specified offset in minutes.

        Parameters
        ----------
        column : str
            Name of the column to shift
        offset : int
            Number of minutes to shift by, can be positive or negative
        """
        self.df[column] = self.df[column].shift(offset, freq="1min")

    def _to_line_df(self):
        """
        Convert trajectory data GeoDataFrame of points to GeoDataFrame of lines
        that connect consecutive points.

        Returns
        -------
        line_df : GeoDataFrame
            GeoDataFrame of line segments
        """
        line_df = self.df.copy()
        line_df["prev_pt"] = line_df.geometry.shift()
        line_df["t"] = self.df.index
        line_df["prev_t"] = line_df["t"].shift()
        line_df["line"] = line_df.apply(self._connect_prev_pt_and_geometry, axis=1)
        return line_df.set_geometry("line")[1:]

    def get_mcp(self):
        """Return the Minimum Convex Polygon of the trajectory data

        Returns
        -------
        mcp : Shapely object
            The polygon or line (in case of only two points)
            of the Minimum Convex Polygon
        """
        return self.df.geometry.unary_union.convex_hull


def to_unixtime(t):
    """
    Return float of total seconds since Unix time.
    """
    return (t - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()


def point_gdf_to_linestring(df, geom_col_name):
    """
    Convert GeoDataFrame of Points to shapely LineString
    """
    if len(df) > 1:
        return (
            df.groupby([True] * len(df))[geom_col_name]
            .apply(lambda x: LineString(x.tolist()))
            .values[0]
        )
    else:
        raise RuntimeError("DataFrame needs at least two points to make line!")
