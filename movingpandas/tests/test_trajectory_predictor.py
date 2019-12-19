# -*- coding: utf-8 -*-

import pytest
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import datetime, timedelta
from fiona.crs import from_epsg
from movingpandas.trajectory import Trajectory
from movingpandas.trajectory_predictor import TrajectoryPredictor


CRS_LATLON = from_epsg(4326)
 
 
class TestTrajectoryPredictor:
    
    def test_linear_prediction_east(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 1, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(20, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
    
    def test_linear_prediction_west(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(-10, 0), 't': datetime(2018, 1, 1, 12, 1, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(-20, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
        
    def test_linear_prediction_north(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 1, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(0, 20)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)

    def test_linear_prediction_south(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, -10), 't': datetime(2018, 1, 1, 12, 1, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_linearly(timedelta(minutes=1))
        expected_result = Point(0, -20)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)

    def test_kinetic_prediction_east_constant(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 1, 0)},
            {'geometry': Point(20, 0), 't': datetime(2018, 1, 1, 12, 2, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(minutes=1))
        expected_result = Point(30, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
        
    def test_kinetic_prediction_west_constant(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(-10, 0), 't': datetime(2018, 1, 1, 12, 1, 0)},
            {'geometry': Point(-20, 0), 't': datetime(2018, 1, 1, 12, 2, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(minutes=1))
        expected_result = Point(-30, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
        
    def test_kinetic_prediction_east_3pt_constant_speed(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 1, 0)},
            {'geometry': Point(20, 0), 't': datetime(2018, 1, 1, 12, 2, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(minutes=1))
        expected_result = Point(30, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
        
    def test_kinetic_prediction_east_3pt_accelerating(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(30, 0), 't': datetime(2018, 1, 1, 12, 0, 2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(80, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
    
    def test_kinetic_prediction_east_3pt_decelerating(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(18, 0), 't': datetime(2018, 1, 1, 12, 0, 2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(32, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
        
    def test_kinetic_prediction_east_3pt_decelerating_tozero(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(16, 0), 't': datetime(2018, 1, 1, 12, 0, 2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(24, 0)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
        
    def test_kinetic_prediction_turning_left(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(20, 0), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(20, 20), 't': datetime(2018, 1, 1, 12, 0, 2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(-1.172832, 38.747237)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x)
        assert result.y == pytest.approx(expected_result.y)
        
    def test_kinetic_prediction_turning_right(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(20, 0), 't': datetime(2018, 1, 1, 12, 0, 1)},
            {'geometry': Point(38, -10), 't': datetime(2018, 1, 1, 12, 0, 2)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        traj = Trajectory(geo_df, 1)
        predictor = TrajectoryPredictor(traj)
        result = predictor.predict_kinetically(timedelta(seconds=2))
        expected_result = Point(68.7, -37.3)
        # print("Got {}, expected {}".format(result, expected_result))
        assert result.x == pytest.approx(expected_result.x, 0.1)
        assert result.y == pytest.approx(expected_result.y, 0.1)

