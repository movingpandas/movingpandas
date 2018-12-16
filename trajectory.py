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
import numpy as np
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString, Polygon
from shapely.affinity import translate
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__))

import overlay
from geometry_utils import azimuth, calculate_initial_compass_bearing, measure_distance_spherical, measure_distance_euclidean


def to_unixtime(t):
    return (t - datetime(1970,1,1,0,0,0)).total_seconds() 


class Trajectory():
    def __init__(self, id, df):
        self.id = id
        self.df = df
        self.crs = df.crs['init']
        
    def __str__(self):
        return "Trajectory {1} ({2} to {3}) | Size: {0}\n{4}".format(
            self.df.geometry.count(), self.id, self.get_start_time(), 
            self.get_end_time(), self.to_linestring().wkt)

    def set_crs(self, crs):
        self.crs = crs            
        
    def is_valid(self):
        if len(self.df) < 2:
            return False
        if not self.get_start_time() < self.get_end_time():
            return False
        return True
        
    def to_linestring(self):
        return self.make_line(self.df)
    
    def to_linestringm_wkt(self):
        # Shapely only supports x, y, z. Therfore, this is a bit hacky!
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
        
    def get_position_at(self, t, method='nearest'):
        row = self.get_row_at(t, method)
        try:
            return row.geometry[0]
        except:
            return row.geometry     
        
    def get_linestring_between(self, t1, t2):
        try:
            return self.make_line(self.get_segment_between(t1, t2))
        except RuntimeError:
            raise RuntimeError("Cannot generate linestring between {0} and {1}".format(t1, t2))
        
    def get_segment_between(self, t1, t2):
        #start_time = self.get_start_time()
        #if t1 < self.get_start_time():
        #    raise ValueError("First time parameter ({}) has to be equal or later than trajectory start time ({})!".format(t1, start_time))
        segment = Trajectory(self.id, self.df[t1:t2])
        if not segment.is_valid():
            raise RuntimeError("Failed to extract valid trajectory segment between {} and {}".format(t1, t2))
        return segment

    def compute_heading(self, row):
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
        
    def compute_speed(self, row):
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
        return dist_meters / row['delta_t'].total_seconds()  
            
    def add_heading(self):
        self.df['prev_pt'] = self.df.geometry.shift()
        self.df['heading'] = self.df.apply(self.compute_heading, axis=1)
        self.df.at[self.get_start_time(),'heading'] = self.df.iloc[1]['heading']
        
    def add_meters_per_sec(self):
        self.df['prev_pt'] = self.df.geometry.shift()
        self.df['t'] = self.df.index
        self.df['prev_t'] = self.df['t'].shift()
        self.df['delta_t'] = self.df['t'] - self.df['prev_t'] 
        self.df['meters_per_sec'] = self.df.apply(self.compute_speed, axis=1)
        self.df.at[self.get_start_time(),'meters_per_sec'] = self.df.iloc[1]['meters_per_sec']
        
    def make_line(self, df):
        if df.size > 1:
            return df.groupby([True]*len(df)).geometry.apply(
                lambda x: LineString(x.tolist())).values[0]
        else:
            raise RuntimeError('Dataframe needs at least two points to make line!') 
    
    def clip(self, polygon):
        return overlay.clip(self, polygon)
    
    def intersection(self, feature):
        return overlay.intersection(self, feature)
    