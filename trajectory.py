# -*- coding: utf-8 -*-

"""
***************************************************************************
    trajectory.py
    ---------------------
    Date                 : December 2018
    Copyright            : (C) 2018 by Anita Graser
    Email                : anitagraser@gmx.at
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import sys
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
#from shapely.affinity import translate
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

import overlay
from geometry_utils import azimuth, calculate_initial_compass_bearing, measure_distance_spherical, measure_distance_euclidean


SPEED_COL_NAME = 'speed'
DIRECTION_COL_NAME = 'direction'


def to_unixtime(t):
    return (t - datetime(1970,1,1,0,0,0)).total_seconds()


class Trajectory():
    def __init__(self, traj_id, df, parent=None):
        if len(df) < 2:
            raise ValueError("Trajectory dataframe must have at least two rows!")

        self.id = traj_id
        df.sort_index(inplace=True)
        self.df = df[~df.index.duplicated(keep='first')]
        self.crs = df.crs['init']
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

    def set_crs(self, crs):
        self.crs = crs

    def is_valid(self):
        if len(self.df) < 2:
            return False
        if not self.get_start_time() < self.get_end_time():
            return False
        return True

    def has_parent(self):
        return self.parent != None

    def to_linestring(self):
        try:
            return self._make_line(self.df)
        except RuntimeError:
            raise RuntimeError("Cannot generate linestring")

    def to_linestringm_wkt(self):
        # Shapely only supports x, y, z. Therefore, this is a bit hacky!
        coords = ''
        for index, row in self.df.iterrows():
            pt = row.geometry
            t = to_unixtime(index)
            coords += "{} {} {}, ".format(pt.x, pt.y, t)
        wkt = "LINESTRING M ({})".format(coords[:-2])
        return wkt

    def get_start_location(self):
        return self.df.head(1).geometry[0]

    def get_end_location(self):
        return self.df.tail(1).geometry[0]

    def get_bbox(self):
        return self.to_linestring().bounds # (minx, miny, maxx, maxy)

    def get_start_time(self):
        return self.df.index.min().to_pydatetime()

    def get_end_time(self):
        return self.df.index.max().to_pydatetime()

    def get_duration(self):
        return self.get_end_time() - self.get_start_time()

    def get_row_at(self, t, method='nearest'):
        try:
            return self.df.loc[t]
        except:
            return self.df.iloc[self.df.index.sort_values().drop_duplicates().get_loc(t, method=method)]

    def interpolate_position_at(self, t):
        prev = self.get_row_at(t, 'ffill')
        next = self.get_row_at(t, 'bfill')
        t_diff = next.name - prev.name
        t_diff_at = t - prev.name
        line = LineString([prev.geometry, next.geometry])
        if t_diff == 0 or line.length == 0:
            return prev.geometry
        interpolated_position = line.interpolate(t_diff_at/t_diff*line.length)
        return interpolated_position

    def get_position_at(self, t, method='interpolated'):
        if method not in ['nearest', 'interpolated', 'ffill', 'bfill']:
            raise ValueError('Invalid split mode {}. Must be one of [nearest, interpolated, ffill, bfill]'.format(method))
        if method == 'interpolated':
            return self.interpolate_position_at(t)
        else:
            row = self.get_row_at(t, method)
            try:
                return row.geometry[0]
            except:
                return row.geometry

    def get_linestring_between(self, t1, t2):
        try:
            return self._make_line(self.get_segment_between(t1, t2))
        except RuntimeError:
            raise RuntimeError("Cannot generate linestring between {0} and {1}".format(t1, t2))

    def get_segment_between(self, t1, t2):
        #start_time = self.get_start_time()
        #if t1 < self.get_start_time():
        #    raise ValueError("First time parameter ({}) has to be equal or later than trajectory start time ({})!".format(t1, start_time))
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
        if self.crs == '4326' or self.crs == 'epsg:4326':
            dist_meters = measure_distance_spherical(pt0, pt1)
        else: # The following distance will be in CRS units that might not be meters!
            dist_meters = measure_distance_euclidean(pt0, pt1)
        return dist_meters  
    
    def get_length(self):
        self.df['prev_pt'] = self.df.geometry.shift()
        self.df['dist_to_prev'] = self.df.apply(self._compute_distance, axis=1)
        return self.df['dist_to_prev'].sum() 

    def get_direction(self):
        pt0 = self.get_start_location()
        pt1 = self.get_end_location()
        if self.crs == '4326':
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
        if self.crs == '4326':
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
        if self.crs == '4326' or self.crs == 'epsg:4326':
            dist_meters = measure_distance_spherical(pt0, pt1)
        else: # The following distance will be in CRS units that might not be meters!
            dist_meters = measure_distance_euclidean(pt0, pt1)
        return dist_meters / row['delta_t'].total_seconds()

    def add_direction(self, overwrite=False):
        if DIRECTION_COL_NAME in self.df.keys() and not overwrite:
            raise RuntimeError('Trajectory already has direction values! Use overwrite=True to overwrite exiting values.')
        self.df['prev_pt'] = self.df.geometry.shift()
        self.df[DIRECTION_COL_NAME] = self.df.apply(self._compute_heading, axis=1)
        self.df.at[self.get_start_time(), DIRECTION_COL_NAME] = self.df.iloc[1][DIRECTION_COL_NAME]

    def add_speed(self, overwrite=False):
        if SPEED_COL_NAME in self.df.keys() and not overwrite:
            raise RuntimeError('Trajectory already has speed values! Use overwrite=True to overwrite exiting values.')
        self.df['prev_pt'] = self.df.geometry.shift()
        self.df['t'] = self.df.index
        self.df['prev_t'] = self.df['t'].shift()
        self.df['delta_t'] = self.df['t'] - self.df['prev_t']
        try:
            self.df[SPEED_COL_NAME] = self.df.apply(self._compute_speed, axis=1)
        except ValueError as e:
            raise e
        self.df.at[self.get_start_time(), SPEED_COL_NAME] = self.df.iloc[1][SPEED_COL_NAME]

    def _make_line(self, df):
        if len(df) > 1:
            return df.groupby([True]*len(df)).geometry.apply(
                lambda x: LineString(x.tolist())).values[0]
        else:
            raise RuntimeError('Dataframe needs at least two points to make line!')

    def clip(self, polygon, pointbased=False):
        return overlay.clip(self, polygon, pointbased)

    def intersection(self, feature):
        return overlay.intersection(self, feature)
        
    def split(self, mode='daybreak'):
        result = []
        if mode == 'daybreak':
            dfs = [group[1] for group in self.df.groupby(self.df.index.date)]
            for i, df in enumerate(dfs):
                result.append(Trajectory('{}_{}'.format(self.id, i), df))
        else:
            raise ValueError('Invalid split mode {}. Must be one of [daybreak]'.format(mode))
        return result
        
    def apply_offset_seconds(self, column, offset):
        self.df[column] = self.df[column].shift(offset, freq='1s')

    def apply_offset_minutes(self, column, offset):
        self.df[column] = self.df[column].shift(offset, freq='1min')

