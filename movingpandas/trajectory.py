# -*- coding: utf-8 -*-

import os
import sys

import contextily as ctx

from shapely.affinity import translate
from shapely.geometry import Point, LineString
from fiona.crs import from_epsg
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

from movingpandas import overlay
from movingpandas.geometry_utils import azimuth, calculate_initial_compass_bearing, measure_distance_spherical, \
                                        measure_distance_euclidean


SPEED_COL_NAME = 'speed'
DIRECTION_COL_NAME = 'direction'


class Trajectory:
    def __init__(self, traj_id, df, parent=None):
        if len(df) < 2:
            raise ValueError("Trajectory dataframe must have at least two rows!")

        self.id = traj_id
        df.sort_index(inplace=True)
        self.df = df[~df.index.duplicated(keep='first')]
        self.crs = df.crs
        self.parent = parent
        self.context = None

    def __str__(self):
        try:
            line = self.to_linestring()
        except RuntimeError:
            return "Invalid trajectory!"
        return "Trajectory {1} ({2} to {3}) | Size: {0} | Length: {6:.1f}m\nBounds: {5}\n{4}".format(
            self.df.geometry.count(), self.id, self.get_start_time(),
            self.get_end_time(), line.wkt[:100], self.get_bbox(), self.get_length())

    def plot(self, with_basemap=False, *args, **kwargs):
        temp_df = self.df.copy()
        if 'column' in kwargs:
            if kwargs['column'] == SPEED_COL_NAME and SPEED_COL_NAME not in self.df.columns:
                temp_df = self.get_df_with_speed()
        temp_df = temp_df.assign(prev_pt=temp_df.geometry.shift())
        temp_df['line'] = temp_df.apply(self._connect_prev_pt_and_geometry, axis=1)
        if with_basemap:
            if 'url' in kwargs and 'zoom' in kwargs:
                url = kwargs.pop('url')
                zoom = kwargs.pop('zoom')
                ax = temp_df.set_geometry('line')[1:].to_crs(epsg=3857).plot(*args, **kwargs)
                return ctx.add_basemap(ax, url=url, zoom=zoom)
            elif 'url' in kwargs:
                url = kwargs.pop('url')
                ax = temp_df.set_geometry('line')[1:].to_crs(epsg=3857).plot(*args, **kwargs)
                return ctx.add_basemap(ax, url=url)
            else:
                ax = temp_df.set_geometry('line')[1:].to_crs(epsg=3857).plot(*args, **kwargs)
                return ctx.add_basemap(ax)
        else:
            return temp_df.set_geometry('line')[1:].plot(*args, **kwargs)

    def set_crs(self, crs):
        """Set coordinate reference system of Trajectory using string of SRID."""
        self.crs = crs

    def is_valid(self):
        """Return Boolean of whether Trajectory meets minimum prerequisites."""
        if len(self.df) < 2:
            return False
        if not self.get_start_time() < self.get_end_time():
            return False
        return True

    def is_latlon(self):
        """Return Boolean of whether coordinate reference system is WGS 84."""
        if self.crs['init'] == from_epsg(4326)['init']:
            return True
        else:
            return False

    def has_parent(self):
        """Return Boolean of whether Trajectory object has parent."""
        return self.parent is not None

    def to_linestring(self):
        """Return shapely Linestring object of Trajectory."""
        try:
            return point_gdf_to_linestring(self.df)
        except RuntimeError:
            raise RuntimeError("Cannot generate linestring")

    def to_linestringm_wkt(self):
        """Return WKT Linestring M as string of Trajectory object."""
        # Shapely only supports x, y, z. Therefore, this is a bit hacky!
        coords = ''
        for index, row in self.df.iterrows():
            pt = row.geometry
            t = to_unixtime(index)
            coords += "{} {} {}, ".format(pt.x, pt.y, t)
        wkt = "LINESTRING M ({})".format(coords[:-2])
        return wkt

    def get_start_location(self):
        """Return shapely Point object of Trajectory's start location."""
        return self.df.head(1).geometry[0]

    def get_end_location(self):
        """Return shapely Point object of Trajectory's end location."""
        return self.df.tail(1).geometry[0]

    def get_bbox(self):
        """Return tuple of minimum & maximum x & y of Trajectory's locations."""
        return self.to_linestring().bounds  # (minx, miny, maxx, maxy)

    def get_start_time(self):
        """Return datetime.datetime object of Trajectory's start location."""
        return self.df.index.min().to_pydatetime()

    def get_end_time(self):
        """Return datetime.datetime object of Trajectory's start location."""
        return self.df.index.max().to_pydatetime()

    def get_duration(self):
        """Return datetime.timedelta object of Trajectory's duration."""
        return self.get_end_time() - self.get_start_time()

    def get_row_at(self, t, method='nearest'):
        """Return pandas series of position at given datetime object."""
        try:
            return self.df.loc[t]
        except KeyError:
            return self.df.iloc[self.df.index.sort_values().drop_duplicates().get_loc(t, method=method)]

    def interpolate_position_at(self, t):
        """Return interpolated shapely Point at given datetime object."""
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
        """Return shapely Point at given datetime object and split method."""
        if method not in ['nearest', 'interpolated', 'ffill', 'bfill']:
            raise ValueError('Invalid split method {}. Must be one of [nearest, interpolated, ffill, bfill]'.
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
        """Return shapely LineString between given datetime objects and split method."""
        if method not in ['interpolated', 'within']:
            raise ValueError('Invalid split method {}. Must be one of [interpolated, within]'.format(method))
        if method == 'interpolated':
            st_range = overlay.SpatioTemporalRange(self.get_position_at(t1), self.get_position_at(t2), t1, t2)
            temp_df = overlay.create_entry_and_exit_points(self, st_range)
            temp_df = temp_df[t1:t2]
            return point_gdf_to_linestring(temp_df)
        else:
            try:
                return point_gdf_to_linestring(self.get_segment_between(t1, t2).df)
            except RuntimeError:
                raise RuntimeError("Cannot generate linestring between {0} and {1}".format(t1, t2))

    def get_segment_between(self, t1, t2):
        """Return Trajectory object between given datetime objects."""
        segment = Trajectory(self.id, self.df[t1:t2], parent=self)
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
        if self.is_latlon():
            dist_meters = measure_distance_spherical(pt0, pt1)
        else:  # The following distance will be in CRS units that might not be meters!
            dist_meters = measure_distance_euclidean(pt0, pt1)
        return dist_meters  
    
    def add_prev_pt(self, force=True):
        """create a shifted geometry column with previous positions,
        required for several calculations
        """
        if 'prev_pt' not in self.df.columns or force:
            # TODO: decide on default enforcement behavior
            self.df = self.df.assign(prev_pt=self.df.geometry.shift())
        
    def get_length(self):
        """Return float of length of Trajectory object.

        This is calculated with the measurement unit of the CRS used, except
        when using WGS 84 when it is calculated in metres.
        """
        temp_df = self.df.assign(prev_pt=self.df.geometry.shift())
        temp_df = temp_df.assign(dist_to_prev=temp_df.apply(self._compute_distance, axis=1))
        return temp_df['dist_to_prev'].sum()

    def get_direction(self):
        """Return compass bearing as float of Trajectory object."""
        pt0 = self.get_start_location()
        pt1 = self.get_end_location()
        if self.is_latlon():
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
        if self.is_latlon():
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
        if self.is_latlon():
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
        if pt0 == pt1:
            # to avoid intersection issues with zero length lines
            pt1 = translate(pt1, 0.00000001, 0.00000001)
        return LineString(list(pt0.coords) + list(pt1.coords))

    def add_direction(self, overwrite=False):
        """Add direction column and values to Trajectory object's DataFrame."""
        if DIRECTION_COL_NAME in self.df.columns and not overwrite:
            raise RuntimeError('Trajectory already has direction values! Use overwrite=True to overwrite exiting values.')
        self.add_prev_pt()
        self.df[DIRECTION_COL_NAME] = self.df.apply(self._compute_heading, axis=1)
        self.df.at[self.get_start_time(), DIRECTION_COL_NAME] = self.df.iloc[1][DIRECTION_COL_NAME]

    def add_speed(self, overwrite=False):
        """Add speed column and values to Trajectory object's DataFrame.

        This is calculated with the measurement unit of the CRS used, except
        when using WGS 84 when it is calculated in metres. This is then divided
        by total seconds.
        """
        if SPEED_COL_NAME in self.df.columns and not overwrite:
            raise RuntimeError('Trajectory already has speed values! Use overwrite=True to overwrite exiting values.')
        self.df = self.get_df_with_speed()

    def get_df_with_speed(self):
        """Add speed column and values to Trajectory object's DataFrame.

        This is calculated with the measurement unit of the CRS used, except
        when using WGS 84 when it is calculated in metres. This is then divided
        by total seconds.
        """
        temp_df = self.df.assign(prev_pt=self.df.geometry.shift())
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
        return temp_df

    def clip(self, polygon, pointbased=False):
        """Return clipped Trajectory with polygon as Trajectory object."""
        return overlay.clip(self, polygon, pointbased)

    def intersection(self, feature):
        return overlay.intersection(self, feature)
        
    def split_by_date(self):
        """Return list of Trajectory objects split by date."""
        result = []
        dfs = [group[1] for group in self.df.groupby(self.df.index.date)]
        for i, df in enumerate(dfs):
            result.append(Trajectory('{}_{}'.format(self.id, i), df))
        return result

    def split_by_observation_gap(self, gap):
        result = []
        temp_df = self.df.copy()
        temp_df['t'] = temp_df.index
        temp_df['gap'] = temp_df['t'].diff() > gap
        temp_df['gap'] = temp_df['gap'].apply(lambda x: 1 if x else 0).cumsum()
        dfs = [group[1] for group in temp_df.groupby(temp_df['gap'])]
        for i, df in enumerate(dfs):
            try:
                df = df.drop(columns=['t', 'gap'])
                result.append(Trajectory('{}_{}'.format(self.id, i), df))
            except ValueError:
                pass
        return result

    def apply_offset_seconds(self, column, offset):
        self.df[column] = self.df[column].shift(offset, freq='1s')

    def apply_offset_minutes(self, column, offset):
        self.df[column] = self.df[column].shift(offset, freq='1min')

    def generalize(self, mode, tolerance):
        """Return new generalized Trajectory for Trajectory object."""
        if mode == 'douglas-peucker':
            return self.generalize_douglas_peucker(tolerance)
        elif mode == 'min-time-delta':
            return self.generalize_min_time_delta(tolerance)
        else:
            raise ValueError('Invalid generalization mode {}. Must be one of [douglas-peucker, min-time-delta]'.format(mode))

    def generalize_min_time_delta(self, tolerance):
        """Return new generalized Trajectory where consecutive rows are at least a certain timedelta apart."""
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
        new_traj = Trajectory(self.id, new_df)
        return new_traj

    def generalize_douglas_peucker(self, tolerance):
        """Return new generalized Trajectory using Douglas-Peucker Algorithm."""
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
        new_traj = Trajectory(self.id, new_df)
        return new_traj

    def _to_line_df(self):
        line_df = self.df.copy()
        line_df['prev_pt'] = line_df['geometry'].shift()
        line_df['t'] = self.df.index
        line_df['prev_t'] = line_df['t'].shift()
        line_df['line'] = line_df.apply(self._connect_prev_pt_and_geometry, axis=1)
        return line_df.set_geometry('line')[1:]


def to_unixtime(t):
    """Return float of total seconds since Unix time."""
    return (t - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()


def point_gdf_to_linestring(df):
    if len(df) > 1:
        return df.groupby([True] * len(df)).geometry.apply(
            lambda x: LineString(x.tolist())).values[0]
    else:
        raise RuntimeError('Dataframe needs at least two points to make line!')
