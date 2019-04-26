# -*- coding: utf-8 -*-

"""
***************************************************************************
    test_trajectory_sampler.py
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

python3 test_trajectory_sampler.py -v

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

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from trajectory import Trajectory
from trajectory_sampler import TrajectorySampler

 
class TestTrajectorySampler(unittest.TestCase):
    
    def test_sample(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 1), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(0, 2), 't': datetime(2018, 1, 1, 12, 0, 2)},
            {'geometry': Point(0, 3), 't': datetime(2018, 1, 1, 12, 0, 3)},
            {'geometry': Point(0, 4), 't': datetime(2018, 1, 1, 12, 0, 4)},
            {'geometry': Point(0, 4), 't': datetime(2018, 1, 1, 12, 0, 5)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        sampler = TrajectorySampler(traj)
        past_timedelta = timedelta(seconds=2)
        future_timedelta = timedelta(seconds=2)
        sample = sampler.get_sample(past_timedelta, future_timedelta)
        result = sample.future_pos.wkt
        expected_result = "POINT (0 4)"
        self.assertEqual(expected_result, result)
        result = sample.past_traj.to_linestring().wkt
        expected_result = "LINESTRING (0 0, 0 1, 0 2)"
        self.assertEqual(expected_result, result)
    
    def test_sample_after_movement_start(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 11, 0, 57)},
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 11, 0, 58)},
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 11, 0, 59)},
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 1, 0)},
            {'geometry': Point(0, 1), 't': datetime(2018, 1, 1, 12, 1, 1)},
            {'geometry': Point(0, 2), 't': datetime(2018, 1, 1, 12, 1, 2)},
            {'geometry': Point(0, 3), 't': datetime(2018, 1, 1, 12, 1, 3)},
            {'geometry': Point(0, 4), 't': datetime(2018, 1, 1, 12, 1, 4)},
            {'geometry': Point(0, 4), 't': datetime(2018, 1, 1, 12, 1, 5)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '31256'})
        traj = Trajectory(1, geo_df)
        sampler = TrajectorySampler(traj)
        past_timedelta = timedelta(seconds=2)
        future_timedelta = timedelta(seconds=2)
        sample = sampler.get_sample(past_timedelta, future_timedelta)
        result = sample.future_pos.wkt
        expected_result = "POINT (0 4)"
        self.assertEqual(expected_result, result)
        result = sample.past_traj.to_linestring().wkt
        expected_result = "LINESTRING (0 0, 0 1, 0 2)"
        self.assertEqual(expected_result, result)
    
    def test_sample_irregular_updates(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(0, 3), 't': datetime(2018, 1, 1, 12, 3, 2)},
            {'geometry': Point(0, 6), 't': datetime(2018, 1, 1, 12, 6, 1)},
            {'geometry': Point(0, 9), 't': datetime(2018, 1, 1, 12, 9, 2)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 10, 2)},
            {'geometry': Point(0, 14), 't': datetime(2018, 1, 1, 12, 14, 3)},
            {'geometry': Point(0, 19), 't': datetime(2018, 1, 1, 12, 19, 5)},
            {'geometry': Point(0, 20), 't': datetime(2018, 1, 1, 12, 20, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1, geo_df)
        sampler = TrajectorySampler(traj, timedelta(seconds=5))
        past_timedelta = timedelta(minutes=5)
        future_timedelta = timedelta(minutes=5)
        sample = sampler.get_sample(past_timedelta, future_timedelta)
        result = sample.future_pos.wkt
        expected_result = "POINT (0 19)"
        self.assertEqual(expected_result, result)
        result = sample.past_traj.to_linestring().wkt
        expected_result = "LINESTRING (0 9, 0 10, 0 14)"
        self.assertEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
    
    
    