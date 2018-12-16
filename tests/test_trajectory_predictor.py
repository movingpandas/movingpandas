# -*- coding: utf-8 -*-

"""
***************************************************************************
    test_trajectory_predictor.py
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

python3 test_trajectory_predictor.py -v

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

from trajectory import Trajectory
from trajectory_predictor import TrajectoryPredictor

 
class TestTrajectoryPredictor(unittest.TestCase):
    
    def test_linear_prediction_east(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,1,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(20,0)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))
    
    def test_linear_prediction_west(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(-10,0), 't':datetime(2018,1,1,12,1,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(-20,0)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))
        
    def test_linear_prediction_north(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(0,10), 't':datetime(2018,1,1,12,1,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(0,20)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))

    def test_linear_prediction_south(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(0,-10), 't':datetime(2018,1,1,12,1,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(0,-20)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))

    def test_kinetic_prediction_east_constant(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,1,0)},
            {'geometry':Point(20,0), 't':datetime(2018,1,1,12,2,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(minutes=1))
        expected_result = Point(30,0)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))
        
    def test_kinetic_prediction_west_constant(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(-10,0), 't':datetime(2018,1,1,12,1,0)},
            {'geometry':Point(-20,0), 't':datetime(2018,1,1,12,2,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(minutes=1))
        expected_result = Point(-30,0)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))
        
    def test_kinetic_prediction_east_3pt_constant_speed(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,1,0)},
            {'geometry':Point(20,0), 't':datetime(2018,1,1,12,2,0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(minutes=1))
        expected_result = Point(30,0)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))
        
    def test_kinetic_prediction_east_3pt_accelerating(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,0,1)},
            {'geometry':Point(30,0), 't':datetime(2018,1,1,12,0,2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(100,0)
        #print("\n")
        #print(predictor.traj.df)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))            
    
    def test_kinetic_prediction_east_3pt_decelerating(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,0,1)},
            {'geometry':Point(18,0), 't':datetime(2018,1,1,12,0,2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(28,0)
        #print("\n")
        #print(predictor.traj.df)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))  
        
    def test_kinetic_prediction_east_3pt_decelerating_tozero(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(10,0), 't':datetime(2018,1,1,12,0,1)},
            {'geometry':Point(16,0), 't':datetime(2018,1,1,12,0,2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(18,0)
        #print("\n")
        #print(predictor.traj.df)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result))
        
    def test_kinetic_prediction_turning_left(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(20,0), 't':datetime(2018,1,1,12,0,1)},
            {'geometry':Point(20,20), 't':datetime(2018,1,1,12,0,2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(-1,-1)
        #print("\n")
        #print(predictor.traj.df)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result,0))
        
    def test_kinetic_prediction_turning_right(self):
        df = pd.DataFrame([
            {'geometry':Point(0,0), 't':datetime(2018,1,1,12,0,0)},
            {'geometry':Point(20,0), 't':datetime(2018,1,1,12,0,1)},
            {'geometry':Point(38,-10), 't':datetime(2018,1,1,12,0,2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs={'init': '4326'})
        traj = Trajectory(1,geo_df)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(50.4,-49.3)
        #print("\n")
        #print(predictor.traj.df)
        #print("Got {}, expected {}".format(result, expected_result))
        self.assertTrue(result.almost_equals(expected_result,0))
        
if __name__ == '__main__':
    unittest.main()