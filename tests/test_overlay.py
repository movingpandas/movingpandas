# -*- coding: utf-8 -*-

"""
***************************************************************************
    test_overlay.py
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

ATTENTION!
If you use OSGeo4W, you need to run the following command first:
call C:\OSGeo4W64\bin\py3_env.bat

python3 test_overlay.py -v

or if you want to run all tests at once:

python3 -m unittest discover . -v

"""

import os 
import sys 
import unittest
import pandas as pd 
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString, Polygon
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__),'..'))

from trajectory import Trajectory 

 
class TestOverlay(unittest.TestCase):
         
    def test_clip_two_intersections_with_same_polygon(self):
        polygon = Polygon([(5,-5), (7,-5), (7,12), (5,12), (5,-5)])
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,6,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,10), 't':datetime(2018,1,1,13,0,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        intersections = traj.clip(polygon)
        # spatial 
        result = []
        for x in intersections:
            result.append(x.to_linestring().wkt)
        expected_result = ["LINESTRING (5 0, 6 0, 7 0)", "LINESTRING (7 10, 5 10)"]
        self.assertEqual(result, expected_result)
        # temporal 
        result = []
        for x in intersections:
            result.append((x.get_start_time(), x.get_end_time()))
        expected_result = [(datetime(2018,1,1,12,5,0), datetime(2018,1,1,12,7,0)),
                           (datetime(2018,1,1,12,39,0), datetime(2018,1,1,12,45,0))]
        self.assertEqual(result, expected_result) 
                
    def test_clip_with_duplicate_traj_points(self):
        polygon = Polygon([(5,-5), (7,-5), (7,5), (5,5), (5,-5)])
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,6,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,7,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,11,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,10), 't':datetime(2018,1,1,13,0,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'} )
        traj = Trajectory(1,geo_df)
        intersections = traj.clip(polygon)
        # spatial
        result = []
        for x in intersections:
            result.append(x.to_linestring())
        expected_result = [LineString([(5,0),(6,0),(6,0),(7,0)])]
        self.assertEqual(result, expected_result)
        # temporal
        result = []
        for x in intersections:
            result.append((x.get_start_time(), x.get_end_time()))
        expected_result = [(datetime(2018,1,1,12,5,0), datetime(2018,1,1,12,8,0))]
        self.assertEqual(result, expected_result) 
 
    def test_clip_with_one_intersection(self):
        polygon = Polygon([(5,-5), (7,-5), (7,5), (5,5), (5,-5)])
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,6,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,10), 't':datetime(2018,1,1,13,0,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'} )
        traj = Trajectory(1,geo_df)        
        intersections = traj.clip(polygon)
        # spatial
        result = []
        for x in intersections:
            result.append(x.to_linestring().wkt)
        expected_result = ["LINESTRING (5 0, 6 0, 7 0)"]
        self.assertEqual(result, expected_result)
        # temporal
        result = []
        for x in intersections:
            result.append((x.get_start_time(), x.get_end_time()))
        expected_result = [(datetime(2018,1,1,12,5,0), datetime(2018,1,1,12,7,0))]
        self.assertEqual(result, expected_result) 
         
    def test_clip_with_one_intersection_reversed(self):
        polygon = Polygon([(5,-5), (7,-5), (7,5), (5,5), (5,-5)])
        df = pd.DataFrame([
            {'geometry':Point(0,10), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,6,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,0), 't':datetime(2018,1,1,13,0,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'} )
        traj = Trajectory(1,geo_df)   
        intersections = traj.clip(polygon)
        # spatial
        result = []
        for x in intersections:
            result.append(x.to_linestring().wkt)
        expected_result = ["LINESTRING (7 0, 6 0, 5 0)"]
        self.assertEqual(result, expected_result)
        # temporal
        result = []
        for x in intersections:
            result.append((x.get_start_time(), x.get_end_time()))
        expected_result = [(datetime(2018,1,1,12,25,0), datetime(2018,1,1,12,35,0))]
        self.assertEqual(result, expected_result) 
         
    def test_clip_with_milliseconds(self):
        polygon = Polygon([(5,-5), (7,-5), (8,5), (5,5), (5,-5)])
        df = pd.DataFrame([
            {'geometry':Point(0,10), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,15,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,0), 't':datetime(2018,1,1,13,0,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'} )
        traj = Trajectory(1,geo_df)
        intersection = traj.clip(polygon)[0]
        # spatial
        result = intersection.to_linestring().wkt
        expected_result = "LINESTRING (7.5 0, 6 0, 5 0)"
        self.assertEqual(result, expected_result)
        # temporal
        self.assertAlmostEqual(intersection.get_start_time(), datetime(2018,1,1,12,24,22,500000), delta=timedelta(milliseconds=1))
        self.assertEqual(intersection.get_end_time(), datetime(2018,1,1,12,35,0))
         
    def test_clip_with_numerical_time_issues(self):     
        xmin, xmax, ymin, ymax = 116.36850352835575,116.37029459899574,39.904675309969896,39.90772814977718 
        polygon = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)])
        df = pd.DataFrame([
            {'geometry':Point(116.36855, 39.904926), 't':datetime(2009,3,10,11,3,35)},
            {'geometry':Point(116.368612, 39.904877), 't':datetime(2009,3,10,11,3,37)},
            {'geometry':Point(116.368644, 39.90484), 't':datetime(2009,3,10,11,3,39)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        intersection = traj.clip(polygon)[0]
        result = intersection.to_linestring().wkt
        expected_result = "LINESTRING (116.36855 39.904926, 116.368612 39.904877, 116.368644 39.90484)"
        self.assertEqual(result, expected_result)         
         
    def test_clip_with_no_intersection(self):
        polygon = Polygon([(105,-5), (107,-5), (107,12), (105,12), (105,-5)])
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,15,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,10), 't':datetime(2018,1,1,13,0,0)}]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.clip(polygon)
        expected_result = []
        self.assertEqual(result, expected_result) 
        
    def test_intersection_with_one_intersection(self):
        feature = {
            'geometry': {'type': 'Polygon', 'coordinates': [[(5,-5), (7,-5), (8,5), (5,5), (5,-5)]]},
            'properties': {'id': 1, 'name': 'foo'}  }
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,6,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,10), 't':datetime(2018,1,1,13,0,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'} )
        traj = Trajectory(1,geo_df)        
        intersections = traj.intersection(feature)
        result = list(intersections[0].df.columns)
        expected_result = ['geometry', 'intersecting_id', 'intersecting_name']
        self.assertCountEqual(result, expected_result)
        
 
if __name__ == '__main__':
    unittest.main()
    
    