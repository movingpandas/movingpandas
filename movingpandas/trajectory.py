# -*- coding: utf-8 -*-

import os
import sys

from shapely.affinity import translate
from shapely.geometry import Point, LineString
from datetime import datetime
from pandas import Grouper
try:
    from pyproj import CRS
except ImportError:
    from fiona.crs import from_epsg

sys.path.append(os.path.dirname(__file__))

from .overlay import clip, intersection, intersects, SpatioTemporalRange, create_entry_and_exit_points
from .geometry_utils import azimuth, calculate_initial_compass_bearing, measure_distance_spherical, \
                                        measure_distance_euclidean
from .trajectory_plotter import _TrajectoryPlotter


SPEED_COL_NAME = 'speed'
DIRECTION_COL_NAME = 'direction'


class Trajectory:
    def __init__(self, df, traj_id, obj_id=None, parent=None):
        """
        Create Trajectory from GeoDataFrame.

        Parameters
        ----------
        df : GeoDataFrame
            GeoDataFrame with point geometry column and timestamp index
        traj_id : any
            Trajectory ID
        obj_id : any
            Moving object ID
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
        """
        if len(df) < 2:
            raise ValueError("Trajectory dataframe must have at least two rows!")

        self.id = traj_id
        self.obj_id = obj_id
        df.sort_index(inplace=True)
        self.df = df[~df.index.duplicated(keep='first')]
        self.crs = df.crs
        self.parent = parent
        try:
            crs = CRS.from_user_input(self.crs)
            self.is_latlon = crs.is_geographic
        except NameError:
            self.is_latlon = self.crs['init'] == from_epsg(4326)['init']

    def __str__(self):
        try:
            line = self.to_linestring()
        except RuntimeError:
            return "Invalid trajectory!"
        return "Trajectory {1} ({2} to {3}) | Size: {0} | Length: {6:.1f}m\nBounds: {5}\n{4}".format(
            self.df.geometry.count(), self.id, self.get_start_time(),
            self.get_end_time(), line.wkt[:100], self.get_bbox(), self.get_length())

    def __eq__(self, other):
        # TODO: make bullet proof
        return str(self) == str(other) and self.crs == other.crs and self.parent == other.parent

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
        Generate a plot using geopandas default plotting (matplotlib).

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
        Generate an interactive plot using Holoviews.

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
        """
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

        Returns
        -------
        Trajectory
        """
        temp = self.copy()
        temp.crs = crs
        temp.df = temp.df.to_crs(crs)
        if type(crs) == CRS:
            temp.is_latlon = crs.is_geographic
        else:
            temp.is_latlon = crs['init'] == from_epsg(4326)['init']
        return temp

    def get_speed_column_name(self):
        """
        Return name of the speed column

        Returns
        -------
        string
        """
        return SPEED_COL_NAME

    def to_linestring(self):
        """
        Return trajectory geometry as LineString.

        Returns
        -------
        shapely LineString
        """
        try:
            return point_gdf_to_linestring(self.df)
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
        coords = ''
        for index, row in self.df.iterrows():
            pt = row.geometry
            t = to_unixtime(index)
            coords += "{} {} {}, ".format(pt.x, pt.y, t)
        wkt = "LINESTRING M ({})".format(coords[:-2])
        return wkt

    def get_start_location(self):
        """
        Return the trajectory's start location.

        Returns
        -------
        shapely Point
            Trajectory start location
        """
        return self.df.head(1).geometry[0]

    def get_end_location(self):
        """Return the trajectory's end location.

        Returns
        -------
        shapely Point
            Trajectory end location
        """
        return self.df.tail(1).geometry[0]

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

    def get_row_at(self, t, method='nearest'):
        """
        Return row of the trajectory's dataframe at time t.

        Parameters
        ----------
        t : datetime.datetime
            Timestamp to extract a row for
        method : str
            Pandas get_loc method

        Returns
        -------
        Pandas series
            Row of the dataframe at time t
        """
        try:
            return self.df.loc[t]
        except KeyError:
            return self.df.iloc[self.df.index.sort_values().drop_duplicates().get_loc(t, method=method)]

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
        prev_row = self.get_row_at(t, 'ffill')
        next_row = self.get_row_at(t, 'bfill')
        t_diff = next_row.name - prev_row.name
        t_diff_at = t - prev_row.name
        line = LineString([prev_row.geometry, next_row.geometry])
        if t_diff == 0 or line.length == 0:
            return prev_row.geometry
        interpolated_position = line.interpolate(t_diff_at/t_diff*line.length)
        return interpolated_position

    def get_position_at(self, t, method='interpolated'):
        """
        Compute and return position at time t.

        Parameters
        ----------
        t : datetime.datetime
            Timestamp to extract a row for
        method : str
            Access method

        Returns
        -------
        shapely Point
            Position at time t

        Examples
        --------
        If the trajectory contains a position at the given timestamp, it is returned:

        >>> traj.get_position_at(datetime(2018, 1, 1, 12, 6))
        Point (6 0)

        If there is no trajectory position for the given timestamp, the default behaviour is to interpolate the location:

        >>> traj.get_position_at(datetime(2018, 1, 1, 12, 9))
        POINT (6 4.5)

        To get the trajectory position closest to the given timestamp, specify method='nearest':

        >>> traj.get_position_at(datetime(2018, 1, 1, 12, 9), method='nearest')
        POINT (6 6)
        """
        if method not in ['nearest', 'interpolated', 'ffill', 'bfill']:
            raise ValueError('Invalid method {}. Must be one of [nearest, interpolated, ffill, bfill]'.
                             format(method))
        if method == 'interpolated':
            return self.interpolate_position_at(t)
        else:
            row = self.get_row_at(t, method)
            try:
                return row.geometry[0]
            except TypeError:
                return row.geometry

    def get_linestring_between(self, t1, t2, method='interpolated'):
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
        if method not in ['interpolated', 'within']:
            raise ValueError('Invalid split method {}. Must be one of [interpolated, within]'.format(method))
        if method == 'interpolated':
            st_range = SpatioTemporalRange(self.get_position_at(t1), self.get_position_at(t2), t1, t2)
            temp_df = create_entry_and_exit_points(self, st_range)
            temp_df = temp_df[t1:t2]
            return point_gdf_to_linestring(temp_df)
        else:
            try:
                return point_gdf_to_linestring(self.get_segment_between(t1, t2).df)
            except RuntimeError:
                raise RuntimeError("Cannot generate linestring between {0} and {1}".format(t1, t2))

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
        segment = Trajectory(self.df[t1:t2], self.id, parent=self)
        if not segment.is_valid():
            raise RuntimeError("Failed to extract valid trajectory segment between {} and {}".format(t1, t2))
        return segment

    def _compute_distance(self, row):
        pt0 = row['prev_pt']
        pt1 = row['geometry']
        if type(pt0) != Point:
            return 0.0
        if pt0 == pt1:
            return 0.0
        if self.is_latlon:
            dist_meters = measure_distance_spherical(pt0, pt1)
        else:  # The following distance will be in CRS units that might not be meters!
            dist_meters = measure_distance_euclidean(pt0, pt1)
        return dist_meters

    def _add_prev_pt(self, force=True):
        """
        Create a shifted geometry column with previous positions.
        """
        if 'prev_pt' not in self.df.columns or force:
            # TODO: decide on default enforcement behavior
            self.df = self.df.assign(prev_pt=self.df.geometry.shift())

    def get_length(self):
        """
        Return the length of the trajectory.

        Length is calculated using CRS units, except if the CRS is geographic (e.g. EPSG:4326 WGS84)
        then length is calculated in metres.

        Returns
        -------
        float
            Length of the trajectory
        """
        temp_df = self.df.assign(prev_pt=self.df.geometry.shift())
        temp_df = temp_df.assign(dist_to_prev=temp_df.apply(self._compute_distance, axis=1))
        return temp_df['dist_to_prev'].sum()

    def get_direction(self):
        """
        Return the direction of the trajectory.

        The direction is calculated between the trajectory's start and end location.
        Direction values are in degrees, starting North turning clockwise.

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
        pt0 = row['prev_pt']
        pt1 = row['geometry']
        if type(pt0) != Point:
            return 0.0
        if pt0 == pt1:
            return 0.0
        if self.is_latlon:
            return calculate_initial_compass_bearing(pt0, pt1)
        else:
            return azimuth(pt0, pt1)

    def _compute_speed(self, row):
        pt0 = row['prev_pt']
        pt1 = row['geometry']
        if type(pt0) != Point:
            return 0.0
        if type(pt1) != Point:
            raise ValueError('Invalid trajectory! Got {} instead of point!'.format(pt1))
        if pt0 == pt1:
            return 0.0
        if self.is_latlon:
            dist_meters = measure_distance_spherical(pt0, pt1)
        else:  # The following distance will be in CRS units that might not be meters!
            dist_meters = measure_distance_euclidean(pt0, pt1)
        return dist_meters / row['delta_t'].total_seconds()

    @staticmethod
    def _connect_prev_pt_and_geometry(row):
        pt0 = row['prev_pt']
        pt1 = row['geometry']
        if type(pt0) != Point:
            return None
        if type(pt1) != Point:
            raise ValueError('Invalid trajectory! Got {} instead of point!'.format(pt1))
        if pt0 == pt1:
            # to avoid intersection issues with zero length lines
            pt1 = translate(pt1, 0.00000001, 0.00000001)
        return LineString(list(pt0.coords) + list(pt1.coords))

    def add_direction(self, overwrite=False):
        """
        Add direction column and values to the trajectory's dataframe.

        The direction is calculated between the trajectory's start and end location.
        Direction values are in degrees, starting North turning clockwise.
        """
        if DIRECTION_COL_NAME in self.df.columns and not overwrite:
            raise RuntimeError('Trajectory already has direction values! Use overwrite=True to overwrite exiting values.')
        self._add_prev_pt()
        self.df[DIRECTION_COL_NAME] = self.df.apply(self._compute_heading, axis=1)
        self.df.at[self.get_start_time(), DIRECTION_COL_NAME] = self.df.iloc[1][DIRECTION_COL_NAME]

    def add_speed(self, overwrite=False):
        """
        Add speed column and values to the trajectory's dataframe.

        Speed is calculated as CRS units per second, except if the CRS is geographic (e.g. EPSG:4326 WGS84)
        then speed is calculated in meters per second.
        """
        if SPEED_COL_NAME in self.df.columns and not overwrite:
            raise RuntimeError('Trajectory already has speed values! Use overwrite=True to overwrite exiting values.')
        self.df = self._get_df_with_speed()

    def _get_df_with_speed(self):
        temp_df = self.df.copy()
        temp_df = temp_df.assign(prev_pt=temp_df.geometry.shift())
        if 't' in temp_df.columns:
            times = temp_df.t
        else:
            times = temp_df.reset_index().t
        temp_df = temp_df.assign(delta_t=times.diff().values)
        try:
            temp_df[SPEED_COL_NAME] = temp_df.apply(self._compute_speed, axis=1)
        except ValueError as e:
            raise e
        # set the speed in the first row to the speed of the second row
        temp_df.at[self.get_start_time(), SPEED_COL_NAME] = temp_df.iloc[1][SPEED_COL_NAME]
        temp_df = temp_df.drop(columns=['prev_pt', 'delta_t'])
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

    def clip(self, polygon, pointbased=False):
        """
        Return trajectory clipped by the given polygon.

        By default, the trajectory's line representation is clipped by the polygon.
        If pointbased=True, the trajectory's point representation is used instead, leading to shorter
        segments.

        Parameters
        ----------
        polygon : shapely Polygon
            Polygon to clip with
        pointbased : bool
            Clipping method

        Returns
        -------
        list
            Clipped trajectory segments
        """
        return clip(self, polygon, pointbased)

    def intersection(self, feature, pointbased=False):
        """
        Return the trajectory segment that intersects the given feature.

        Feature attributes are appended to the trajectory's dataframe.

        By default, the trajectory's line representation is clipped by the polygon.
        If pointbased=True, the trajectory's point representation is used instead, leading to shorter
        segments.

        Parameters
        ----------
        feature : shapely Feature
            Feature to intersect with
        pointbased : bool
            Clipping method

        Returns
        -------
        Trajectory
            Trajectory segment intersecting with the feature
        """
        return intersection(self, feature, pointbased)

    def split_by_date(self, mode='day'):
        """
        Split trajectory into subtrajectories using regular time intervals.

        Parameters
        ----------
        mode : str
            Split mode

        Returns
        -------
        list
            List of trajectories
        """
        result = []
        if mode == 'day':
            grouped = self.df.groupby(Grouper(freq="D"))
        elif mode == 'month':
            grouped = self.df.groupby(Grouper(freq="M"))
        elif mode == 'year':
            grouped = self.df.groupby(Grouper(freq="Y"))
        else:
            raise ValueError('Invalid split mode {}. Must be one of [day, month, year]'.format(mode))
        for key, values in grouped:
            if len(values) > 1:
                result.append(Trajectory(values, '{}_{}'.format(self.id, key)))
        return result

    def split_by_observation_gap(self, gap):
        """
        Split the trajectory into subtrajectories whenever there is a gap in the observations.

        Parameters
        ----------
        gap : datetime.timedelta
            Time gap threshold

        Returns
        -------
        list
            List of trajectories
        """
        result = []
        temp_df = self.df.copy()
        temp_df['t'] = temp_df.index
        temp_df['gap'] = temp_df['t'].diff() > gap
        temp_df['gap'] = temp_df['gap'].apply(lambda x: 1 if x else 0).cumsum()
        dfs = [group[1] for group in temp_df.groupby(temp_df['gap'])]
        for i, df in enumerate(dfs):
            df = df.drop(columns=['t', 'gap'])
            if len(df) > 1:
                result.append(Trajectory(df, '{}_{}'.format(self.id, i)))
        return result

    def apply_offset_seconds(self, column, offset):
        """
        Shift column by the specified offset in seconds.

        Parameters
        ----------
        column : str
            Name of the column to shift
        offset : int
            Number of seconds to shift by, can be positive or negative.
        """
        self.df[column] = self.df[column].shift(offset, freq='1s')

    def apply_offset_minutes(self, column, offset):
        """
        Shift column by the specified offset in minutes.

        Parameters
        ----------
        column : str
            Name of the column to shift
        offset : int
            Number of minutes to shift by, can be positive or negative.
        """
        self.df[column] = self.df[column].shift(offset, freq='1min')

    def generalize(self, mode, tolerance):
        """
        Generalize the trajectory.

        Supported generalization modes include:

        * 'douglas-peucker' (tolerance as float in CRS units or meters if CRS is geographic, e.g. EPSG:4326 WGS84)
        * 'min-time-delta' (tolerance as datetime.timedelta)
        * 'min-distance' (tolerance as float in CRS units or meters if CRS is geographic, e.g. EPSG:4326 WGS84)

        Parameters
        ----------
        mode : str
            Generalization mode
        tolerance : any type
            Tolerance threshold, differs by generalization mode

        Returns
        -------
        Trajectory
            Generalized trajectory
        """
        if mode == 'douglas-peucker':
            return self.generalize_douglas_peucker(tolerance)
        elif mode == 'min-time-delta':
            return self.generalize_min_time_delta(tolerance)
        elif mode == 'min-distance':
            return self.generalize_min_distance(tolerance)
        else:
            raise ValueError('Invalid generalization mode {}. Must be one of [douglas-peucker, min-time-delta, min-distance]'.format(mode))

    def generalize_min_distance(self, tolerance):
        """
        Generalize the trajectory based on distance.

        This generalization ensures that consecutive locations are at least a certain distance apart.

        Parameters
        ----------
        tolerance : float
            Desired minimum distance between consecutive points

        Returns
        -------
        Trajectory
            Generalized trajectory
        """
        temp_df = self.df.copy()
        prev_pt = temp_df.iloc[0]['geometry']
        keep_rows = [0]
        i = 0

        for index, row in temp_df.iterrows():
            pt = row['geometry']
            if self.is_latlon:
                dist = measure_distance_spherical(pt, prev_pt)
            else:
                dist = measure_distance_euclidean(pt, prev_pt)
            if dist >= tolerance:
                keep_rows.append(i)
                prev_pt = pt
            i += 1

        keep_rows.append(len(self.df)-1)
        new_df = self.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, self.id)
        return new_traj


    def generalize_min_time_delta(self, tolerance):
        """
        Generalize the trajectory based on time.

        This generalization ensures that consecutive rows are at least a certain timedelta apart.

        Parameters
        ----------
        tolerance : datetime.timedelta
            Desired minimum time difference between consecutive rows

        Returns
        -------
        Trajectory
            Generalized trajectory
        """
        temp_df = self.df.copy()
        temp_df['t'] = temp_df.index
        prev_t = temp_df.head(1)['t'][0]
        keep_rows = [0]
        i = 0

        for index, row in temp_df.iterrows():
            t = row['t']
            tdiff = t - prev_t
            if tdiff >= tolerance:
                keep_rows.append(i)
                prev_t = t
            i += 1

        keep_rows.append(len(self.df)-1)
        new_df = self.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, self.id)
        return new_traj

    def generalize_douglas_peucker(self, tolerance):
        """
        Generalize the trajectory using Douglas-Peucker algorithm.

        Parameters
        ----------
        tolerance : float
            Distance tolerance

        Returns
        -------
        Trajectory
            Generalized trajectory
        """
        prev_pt = None
        pts = []
        keep_rows = []
        i = 0

        for index, row in self.df.iterrows():
            current_pt = row.geometry
            if prev_pt is None:
                prev_pt = current_pt
                keep_rows.append(i)
                continue
            line = LineString([prev_pt, current_pt])
            for pt in pts:
                if line.distance(pt) > tolerance:
                    prev_pt = current_pt
                    pts = []
                    keep_rows.append(i)
                    continue
            pts.append(current_pt)
            i += 1

        keep_rows.append(i)
        new_df = self.df.iloc[keep_rows]
        new_traj = Trajectory(new_df, self.id)
        return new_traj

    def _to_line_df(self):
        line_df = self.df.copy()
        line_df['prev_pt'] = line_df['geometry'].shift()
        line_df['t'] = self.df.index
        line_df['prev_t'] = line_df['t'].shift()
        line_df['line'] = line_df.apply(self._connect_prev_pt_and_geometry, axis=1)
        return line_df.set_geometry('line')[1:]


def to_unixtime(t):
    """
    Return float of total seconds since Unix time.
    """
    return (t - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()


def point_gdf_to_linestring(df):
    """
    Convert GeoDataFrame of Points to shapely LineString
    """
    if len(df) > 1:
        return df.groupby([True] * len(df)).geometry.apply(
            lambda x: LineString(x.tolist())).values[0]
    else:
        raise RuntimeError('Dataframe needs at least two points to make line!')
