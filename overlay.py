# -*- coding: utf-8 -*-

"""
***************************************************************************
    overlay.py
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

#import os
#import sys
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString, shape
from shapely.affinity import translate
from datetime import timedelta

#sys.path.append(os.path.dirname(__file__))

class SpatioTemporalRange():
    def __init__(self, pt_0, pt_n, t_0, t_n):
        self.pt_0 = pt_0
        self.pt_n = pt_n
        self.t_0 = t_0
        self.t_n= t_n

class TemporalRange():
    def __init__(self, t_0, t_n):
        self.t_0 = t_0
        self.t_n= t_n

def _connect_points(row):
    pt0 = row['prev_pt']
    pt1 = row['geometry']
    if type(pt0) != Point:
        return None
    if pt0 == pt1:
        # to avoid intersection issues with zero length lines
        pt1 = translate(pt1, 0.00000001, 0.00000001)
    return LineString(list(pt0.coords) + list(pt1.coords))

def _to_line_df(traj):
    line_df = traj.df.copy()
    line_df['prev_pt'] = line_df['geometry'].shift()
    line_df['t'] = traj.df.index
    line_df['prev_t'] = line_df['t'].shift()
    line_df['line'] = line_df.apply(_connect_points, axis=1)
    return line_df.set_geometry('line')[1:]

def _get_spatiotemporal_ref(row):
    #print(type(row['geo_intersection']))
    if type(row['spatial_intersection']) == LineString:
        pt0 = Point(row['spatial_intersection'].coords[0])
        ptn = Point(row['spatial_intersection'].coords[-1])
        t = row['prev_t']
        t_delta = row['t'] - t
        length = row['line'].length
        t0 = t + (t_delta * row['line'].project(pt0)/length)
        tn = t + (t_delta * row['line'].project(ptn)/length)
        # to avoid intersection issues with zero length lines
        if ptn == translate(pt0, 0.00000001, 0.00000001):
            t0 = row['prev_t']
            tn = row['t']
        # to avoid numerical issues with timestamps
        if is_equal(tn, row['t']):
            tn = row['t']
        if is_equal(t0, row['prev_t']):
            t0 = row['prev_t']
        return SpatioTemporalRange(pt0, ptn, t0, tn)
    else:
        return None

def _dissolve_ranges(ranges):
    if len(ranges) == 0:
        raise ValueError("Nothing to dissolve (received empty ranges)!")
    new = []
    start = None
    end = None
    pt0 = None
    ptn = None
    for r in ranges:
        if start is None:
            start = r.t_0
            end = r.t_n
            pt0 = r.pt_0
            ptn = r.pt_n
        elif end == r.t_0:
            end = r.t_n
            ptn = r.pt_n
        elif r.t_0 > end and is_equal(r.t_0, end):
            end = r.t_n
            ptn = r.pt_n
        else:
            new.append(SpatioTemporalRange(pt0, ptn, start, end))
            start = r.t_0
            end = r.t_n
            pt0 = r.pt_0
            ptn = r.pt_n
    new.append(SpatioTemporalRange(pt0, ptn, start, end))
    return new

def is_equal(t1, t2):
    return abs(t1 - t2) < timedelta(milliseconds=10)

def intersects(traj, polygon):
    try:
        line = traj.to_linestring()
    except:
        return False
    return line.intersects(polygon)

def _create_entry_and_exit_points(traj, range):
    # Create row at entry point with attributes from previous row = pad
    row0 = traj.df.iloc[traj.df.index.get_loc(range.t_0, method='pad')]
    row0['geometry'] = range.pt_0
    # Create row at exit point
    rown = traj.df.iloc[traj.df.index.get_loc(range.t_n, method='pad')]
    rown['geometry'] = range.pt_n
    # Insert rows
    traj.df.loc[range.t_0] = row0
    traj.df.loc[range.t_n] = rown
    return traj.df.sort_index()

def _add_dummy(traj):
    traj.df['dummy_that_stops_things_from_breaking'] = 1
    return traj

def _drop_dummy(traj):
    try:
        traj.df.drop(columns=['dummy_that_stops_things_from_breaking'], axis=1, inplace=True)
    except KeyError:
        pass
    return traj

def _get_segments_for_ranges(traj, ranges):
    counter = 0
    intersections = [] # list of trajectories
    for the_range in ranges:
        if type(the_range) == SpatioTemporalRange:
            traj.df = _create_entry_and_exit_points(traj, the_range)
        try:
            intersection = traj.get_segment_between(the_range.t_0, the_range.t_n)
        except ValueError as e:
            print(e)
            continue
        intersection.id = "{}_{}".format(traj.id, counter)
        intersection = _drop_dummy(intersection)
        intersections.append(intersection)
        counter += 1
    return intersections

def _determine_time_ranges_pointbased(traj, polygon):
    df = traj.df
    df['t'] = df.index
    df['intersects'] = df.intersects(polygon)
    df['segment'] = (df['intersects'].shift(1) != df['intersects']).astype(int).cumsum()
    df = df.groupby('segment', as_index=False).agg({'t': ['min', 'max'], 'intersects': ['min']})
    df.columns = df.columns.map('_'.join)

    ranges = []
    for index, row in df.iterrows():
        if row['intersects_min']:
            ranges.append(TemporalRange(row['t_min'], row['t_max']))
    return ranges

def _get_potentially_intersecting_lines(traj, polygon):
    line_df = _to_line_df(traj)
    spatial_index = line_df.sindex
    if spatial_index:
        possible_matches_index = list(spatial_index.intersection(polygon.bounds))
        possible_matches = line_df.iloc[possible_matches_index].sort_index()
    else:
        possible_matches = line_df
    return possible_matches

def _determine_time_ranges_linebased(traj, polygon):
    # Note: If the trajectory contains consecutive rows without location change
    #       these will result in zero length lines that return an empty
    #       intersection.
    possible_matches = _get_potentially_intersecting_lines(traj, polygon)
    possible_matches['spatial_intersection'] = possible_matches.intersection(polygon)
    possible_matches['spatiotemporal_intersection'] = possible_matches.apply(_get_spatiotemporal_ref, axis=1)

    # The following for loop creates wrong results if there
    # is no other column besides the geometry column.
    if len(traj.df.columns) < 2:
        traj = _add_dummy(traj)

    ranges = []
    for index, row in possible_matches.iterrows():
        x = row['spatiotemporal_intersection']
        if x is None:
            continue
        ranges.append(x)

    return _dissolve_ranges(ranges)

def clip(traj, polygon, pointbased=False):
    #pd.set_option('display.max_colwidth', -1)
    if not intersects(traj, polygon):
        return []
    if pointbased:
        ranges = _determine_time_ranges_pointbased(traj, polygon)
    else:
        ranges = _determine_time_ranges_linebased(traj, polygon)
    return _get_segments_for_ranges(traj, ranges)

def _get_geometry_and_properties_from_feature(feature):
    if type(feature) != dict:
        raise TypeError("Trajectories can only be intersected with a Shapely feature!")
    try:
        geometry = shape(feature['geometry'])
        properties = feature['properties']
    except:
        raise TypeError("Trajectories can only be intersected with a Shapely feature!")
    return (geometry, properties)

def intersection(traj, feature, pointbased=False):
    geometry, properties = _get_geometry_and_properties_from_feature(feature)
    intersections = clip(traj, geometry, pointbased)
    result = []
    for intersection in intersections:
        for key, value in properties.items():
            intersection.df['intersecting_'+key] = value
        result.append(intersection)
    return result
