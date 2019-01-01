# -*- coding: utf-8 -*-

"""
***************************************************************************
    test_trajectory.py
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

python3 test_trajectory.py -v

or if you want to run all tests at once:

python3 -m unittest discover . -v

"""

import os 
import sys 
import unittest
import pandas as pd 
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__),'..'))

from trajectory import Trajectory 

 
class TestTrajectory(unittest.TestCase):

    def test_endlocation(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,6,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.get_end_location()
        expected_result = Point(10,0)
        self.assertEqual(result, expected_result)

    def test_linestring_wkt(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,6,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.to_linestring().wkt
        expected_result = "LINESTRING (0 0, 6 0, 10 0)"        
        self.assertEqual(result, expected_result) 
        
    def test_linstring_m_wkt(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(1970,1,1,0,0,1)},
            {'geometry':Point(6,0), 't':datetime(1970,1,1,0,0,2)},
            {'geometry':Point(10,0), 't':datetime(1970,1,1,0,0,3)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.to_linestringm_wkt()
        expected_result = "LINESTRING M (0.0 0.0 1.0, 6.0 0.0 2.0, 10.0 0.0 3.0)"        
        self.assertEqual(result, expected_result) 

    def test_get_position_at_existing_timestamp(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,20,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.get_position_at(datetime(2018,1,1,12,10,0))      
        expected_result = Point(6,0)
        self.assertEqual(result, expected_result)

    def test_get_position_of_nearest_timestamp(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,20,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.get_position_at(datetime(2018,1,1,12,14,0))      
        expected_result = Point(6,0)
        self.assertEqual(result, expected_result)
        result = traj.get_position_at(datetime(2018,1,1,12,15,0))      
        expected_result = Point(10,0)
        self.assertEqual(result, expected_result)
        
    def test_get_segment_between_existing_timestamps(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,15,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,0)},
            {'geometry':Point(0,10), 't':datetime(2018,1,1,13,0,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.get_segment_between(datetime(2018,1,1,12,10,0),datetime(2018,1,1,12,30,0)).df
        expected_result = pd.DataFrame([
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,15,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,0)}
            ]).set_index('t')
        pd.testing.assert_frame_equal(result, expected_result)
        expected_result = pd.DataFrame([
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,15,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,30,1)}
            ]).set_index('t')
        self.assertNotEqual(result.to_dict(), expected_result.to_dict()) 
        
    def test_get_segment_between_new_timestamps(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(20,0), 't':datetime(2018,1,1,12,20,0)},
            {'geometry':Point(30,0), 't':datetime(2018,1,1,12,30,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.get_segment_between(datetime(2018,1,1,12,5,0),datetime(2018,1,1,12,25,0,50)).df
        expected_result = pd.DataFrame([
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(20,0), 't':datetime(2018,1,1,12,20,0)}
            ]).set_index('t')
        pd.testing.assert_frame_equal(result, expected_result)              
        
    def test_add_heading(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,10,0)},
            {'geometry':Point(6,-6), 't':datetime(2018,1,1,12,20,0)},
            {'geometry':Point(-6,-6), 't':datetime(2018,1,1,12,30,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        traj.add_heading()
        result = traj.df['heading'].tolist() 
        expected_result = [90.0, 90.0, 180.0, 270]
        self.assertEqual(result, expected_result)
        
    def test_add_heading_latlon(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,10), 't':datetime(2018,1,1,12,10,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        traj.add_heading()
        result = traj.df['heading'].tolist()
        expected_result = [44.561451413257714, 44.561451413257714]
        self.assertAlmostEqual(result[0], expected_result[0], 5)
        
    def test_add_meters_per_sec(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,0,1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        traj.add_meters_per_sec()
        result = traj.df['meters_per_sec'].tolist() 
        expected_result = [6.0, 6.0]
        self.assertEqual(result, expected_result)
        
    def test_add_meters_per_sec_latlon(self):
        df = pd.DataFrame([
            {'geometry':Point(0,1), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,0,1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        traj.add_meters_per_sec()
        result = traj.df['meters_per_sec'].tolist()[0]/1000
        expected_result = 676.3
        self.assertAlmostEqual(result, expected_result, 1)
        
    def test_get_bbox(self):
        df = pd.DataFrame([
            {'geometry':Point(0,1), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,5), 't':datetime(2018,1,1,12,0,1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        result = traj.get_bbox()
        expected_result = (0,1,6,5) # (minx, miny, maxx, maxy)
        self.assertEqual(result, expected_result)
 
    def test_length_spherical(self):
        df = pd.DataFrame([
            {'geometry':Point(0,1), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,0,1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        result = traj.get_length()/1000
        expected_result = 676.3
        self.assertAlmostEqual(result, expected_result, 1)
        
    def test_length_euclidiean(self):
        df = pd.DataFrame([
            {'geometry':Point(0,2), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(6,0), 't':datetime(2018,1,1,12,0,1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1,geo_df)
        result = traj.get_length()
        expected_result = 6.3
        self.assertAlmostEqual(result, expected_result, 1)
        
if __name__ == '__main__':
    unittest.main()
    