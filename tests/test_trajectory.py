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
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__),'..'))

from trajectory import Trajectory, DIRECTION_COL_NAME, SPEED_COL_NAME

 
class TestTrajectory(unittest.TestCase):

    def test_endlocation(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 6, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 10, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_end_location()
        expected_result = Point(10, 0)
        self.assertEqual(expected_result, result)

    def test_linestring_wkt(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 6, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 10, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.to_linestring().wkt
        expected_result = "LINESTRING (0 0, 6 0, 10 0)"        
        self.assertEqual(expected_result, result)
        
    def test_linstring_m_wkt(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(1970, 1, 1, 0, 0, 1)},
            {'geometry': Point(6, 0), 't': datetime(1970, 1, 1, 0, 0, 2)},
            {'geometry': Point(10, 0), 't': datetime(1970, 1, 1, 0, 0, 3)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.to_linestringm_wkt()
        expected_result = "LINESTRING M (0.0 0.0 1.0, 6.0 0.0 2.0, 10.0 0.0 3.0)"        
        self.assertEqual(expected_result, result)

    def test_get_position_at_existing_timestamp(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 20, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_position_at(datetime(2018, 1, 1, 12, 10, 0), method='nearest')
        expected_result = Point(6, 0)
        self.assertEqual(expected_result, result)

    def test_get_position_of_nearest_timestamp(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 20, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_position_at(datetime(2018, 1, 1, 12, 14, 0), method='nearest')
        expected_result = Point(6, 0)
        self.assertEqual(expected_result, result)
        result = traj.get_position_at(datetime(2018, 1, 1, 12, 15, 0), method='nearest')
        expected_result = Point(10, 0)
        self.assertEqual(expected_result, result)

    def test_get_position_interpolated_at_timestamp(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 20, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_position_at(datetime(2018, 1, 1, 12, 14, 0), method="interpolated")
        expected_result = Point(6+4/10*4, 0)
        self.assertEqual(expected_result, result)
        result = traj.get_position_at(datetime(2018, 1, 1, 12, 15, 0), method="interpolated")
        expected_result = Point(6+4/10*5, 0)
        self.assertEqual(expected_result, result)

    def test_get_segment_between_existing_timestamps(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 15, 0)},
            {'geometry': Point(10, 10), 't': datetime(2018, 1, 1, 12, 30, 0)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 13, 0, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_segment_between(datetime(2018, 1, 1, 12, 10, 0), datetime(2018, 1, 1, 12, 30, 0)).df
        expected_result = pd.DataFrame([
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 15, 0)},
            {'geometry': Point(10, 10), 't': datetime(2018, 1, 1, 12, 30, 0)}
            ]).set_index('t')
        pd.testing.assert_frame_equal(result, expected_result)
        expected_result = pd.DataFrame([
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 15, 0)},
            {'geometry': Point(10, 10), 't': datetime(2018, 1, 1, 12, 30, 1)}
            ]).set_index('t')
        self.assertNotEqual(expected_result.to_dict(), result.to_dict())

    def test_get_segment_between_new_timestamps(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(20, 0), 't': datetime(2018, 1, 1, 12, 20, 0)},
            {'geometry': Point(30, 0), 't': datetime(2018, 1, 1, 12, 30, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_segment_between(datetime(2018, 1, 1, 12, 5, 0), datetime(2018, 1, 1, 12, 25, 0, 50)).df
        expected_result = pd.DataFrame([
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(20, 0), 't': datetime(2018, 1, 1, 12, 20, 0)}
            ]).set_index('t')
        pd.testing.assert_frame_equal(result, expected_result)
        
    def test_add_heading(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 10, 0)},
            {'geometry': Point(6, -6), 't': datetime(2018, 1, 1, 12, 20, 0)},
            {'geometry': Point(-6, -6), 't': datetime(2018, 1, 1, 12, 30, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        traj.add_direction()
        result = traj.df[DIRECTION_COL_NAME].tolist()
        expected_result = [90.0, 90.0, 180.0, 270]
        self.assertEqual(expected_result, result)
        
    def test_add_heading_latlon(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 10), 't': datetime(2018, 1, 1, 12, 10, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1, geo_df)
        traj.add_direction()
        result = traj.df[DIRECTION_COL_NAME].tolist()
        expected_result = [44.561451413257714, 44.561451413257714]
        self.assertAlmostEqual(expected_result[0], result[0], 5)
        
    def test_add_meters_per_sec(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        traj.add_speed()
        result = traj.df[SPEED_COL_NAME].tolist()
        expected_result = [6.0, 6.0]
        self.assertEqual(expected_result, result)
        
    def test_add_meters_per_sec_latlon(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 1), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1, geo_df)
        traj.add_speed()
        result = traj.df[SPEED_COL_NAME].tolist()[0]/1000
        expected_result = 676.3
        self.assertAlmostEqual(expected_result, result, 1)
        
    def test_get_bbox(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 1), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 5), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1, geo_df)
        result = traj.get_bbox()
        expected_result = (0, 1, 6, 5)  # (minx, miny, maxx, maxy)
        self.assertEqual(expected_result, result)
 
    def test_get_length_spherical(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 1), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1, geo_df)
        result = traj.get_length()/1000
        expected_result = 676.3
        self.assertAlmostEqual(expected_result, result, 1)
        
    def test_get_length_euclidiean(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 2), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_length()
        expected_result = 6.3
        self.assertAlmostEqual(expected_result, result, 1)
        
    def test_get_direction(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(-6, 10), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(6, 6), 't': datetime(2018, 1, 1, 12, 0, 2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        result = traj.get_direction()
        expected_result = 45
        self.assertAlmostEqual(expected_result, result, 1)
        
    def test_split_by_daybreak(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(-6, 10), 't': datetime(2018, 1, 1, 12, 1, 0)},
            {'geometry': Point(6, 6), 't': datetime(2018, 1, 3, 12, 0, 1)},
            {'geometry': Point(6, 16), 't': datetime(2018, 1, 3, 12, 5, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        split = traj.split('daybreak')
        result = len(split)
        expected_result = 2
        self.assertEqual(expected_result, result)

    def test_split_by_daybreak_same_day_of_year(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(-6, 10), 't': datetime(2018, 1, 1, 12, 1, 0)},
            {'geometry': Point(6, 6), 't': datetime(2019, 1, 1, 12, 0, 1)},
            {'geometry': Point(6, 16), 't': datetime(2019, 1, 1, 12, 5, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        split = traj.split('daybreak')
        result = len(split)
        expected_result = 2
        self.assertEqual(expected_result, result)

    def test_offset_seconds(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0), 'value': 1},
            {'geometry': Point(-6, 10), 't': datetime(2018, 1, 1, 12, 1, 0), 'value': 2},
            {'geometry': Point(6, 6), 't': datetime(2018, 1, 1, 12, 2, 0), 'value': 3},
            {'geometry': Point(6, 12), 't': datetime(2018, 1, 1, 12, 3, 0), 'value': 4},
            {'geometry': Point(6, 18), 't': datetime(2018, 1, 1, 12, 4, 0), 'value': 5}
        ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        traj.apply_offset_seconds('value', -120)
        self.assertEqual(5, traj.df.iloc[2].value)
        self.assertEqual(Point(6, 6), traj.df.iloc[2].geometry)

    def test_offset_minutes(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0), 'value': 1},
            {'geometry': Point(-6, 10), 't': datetime(2018, 1, 1, 12, 1, 0), 'value': 2},
            {'geometry': Point(6, 6), 't': datetime(2018, 1, 1, 12, 2, 0), 'value': 3},
            {'geometry': Point(6, 12), 't': datetime(2018, 1, 1, 12, 3, 0), 'value': 4},
            {'geometry': Point(6, 18), 't': datetime(2018, 1, 1, 12, 4, 0), 'value': 5}
        ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        traj.apply_offset_minutes('value', -2)
        self.assertEqual(5, traj.df.iloc[2].value)
        self.assertEqual(Point(6, 6), traj.df.iloc[2].geometry)

    def test_nonchronological_input(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 2, 0, 0, 0)},
            {'geometry': Point(1, 1), 't': datetime(2018, 1, 3, 0, 0, 0)},
            {'geometry': Point(2, 2), 't': datetime(2018, 1, 1, 0, 0, 0)}
        ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        self.assertEqual(datetime(2018, 1, 1), traj.get_start_time())
        self.assertEqual(datetime(2018, 1, 3), traj.get_end_time())
        self.assertEqual(Point(2, 2), traj.get_start_location())


if __name__ == '__main__':
    unittest.main()
