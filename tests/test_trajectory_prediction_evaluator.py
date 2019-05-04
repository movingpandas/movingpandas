# -*- coding: utf-8 -*-

"""
***************************************************************************
    test_trajectory_prediction_evaluator.py
    ---------------------
    Date                 : May 2019
    Copyright            : (C) 2019 by Anita Graser
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

python3 test_trajectory_prediction_evaluator.py -v

or if you want to run all tests at once:

python3 -m unittest discover . -v

"""

import os 
import sys 
import unittest
import pandas as pd
from math import sqrt
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from geometry_utils import measure_distance_spherical
from trajectory import Trajectory
from trajectory_sampler import TrajectorySample
from trajectory_prediction_evaluator import TrajectoryPredictionEvaluator

 
class TestTrajectoryPredictionEvaluator(unittest.TestCase):
    
    def test_errors_prediction_on_true_trajectory(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': 'epsg:25832'})
        true_traj = Trajectory(1,geo_df)
        true_pos = Point(0, 10)
        predicted_pos = Point(0, 9)
        dummy_td = timedelta(seconds=1)
        sample = TrajectorySample(0, dummy_td, dummy_td, dummy_td, None, true_pos, true_traj)
        evaluator = TrajectoryPredictionEvaluator(sample, predicted_pos, 'epsg:25832', 'epsg:25832')
        result = evaluator.get_distance_error()
        expected_result = 1
        self.assertAlmostEqual(result, expected_result, 3)
        result = evaluator.get_cross_track_error()
        expected_result = 0
        self.assertAlmostEqual(result, expected_result, 3)
        result = evaluator.get_along_track_error()
        expected_result = 1
        self.assertAlmostEqual(result, expected_result, 3)

    def test_errors_non_straight(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 8), 't': datetime(2018, 1, 1, 12, 0, 10)},
            {'geometry': Point(1, 9), 't': datetime(2018, 1, 1, 12, 0, 30)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 1, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': 'epsg:25832'})
        true_traj = Trajectory(1,geo_df)
        true_pos = Point(0, 10)
        predicted_pos = Point(0, 8)
        dummy_td = timedelta(minutes=1)
        sample = TrajectorySample(0, dummy_td, dummy_td, dummy_td, None, true_pos, true_traj)
        evaluator = TrajectoryPredictionEvaluator(sample, predicted_pos, 'epsg:25832', 'epsg:25832')
        result = evaluator.get_distance_error()
        expected_result = 2
        self.assertAlmostEqual(result, expected_result, 3)
        result = evaluator.get_cross_track_error()
        expected_result = 0
        self.assertAlmostEqual(result, expected_result, 3)
        result = evaluator.get_along_track_error()
        expected_result = 2*sqrt(2)
        self.assertAlmostEqual(result, expected_result, 3)

    def test_dist_error_latlon(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': 'epsg:4326'})
        true_traj = Trajectory(1,geo_df)
        true_pos = Point(0, 10)
        predicted_pos = Point(0, 9)
        dummy_td = timedelta(seconds=1)
        sample = TrajectorySample(0, dummy_td, dummy_td, dummy_td, None, true_pos, true_traj)
        evaluator = TrajectoryPredictionEvaluator(sample, predicted_pos, 'epsg:25832', 'epsg:4326')
        result = evaluator.get_distance_error()
        expected_result = measure_distance_spherical(true_pos, predicted_pos)
        self.assertAlmostEqual(result, expected_result, 3)

if __name__ == '__main__':
    unittest.main()
