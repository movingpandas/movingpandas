# -*- coding: utf-8 -*-

import pytest
import pandas as pd
from math import sqrt
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import datetime, timedelta
from fiona.crs import from_epsg


from movingpandas.geometry_utils import measure_distance_spherical
from movingpandas.trajectory import Trajectory
from movingpandas.trajectory_sampler import TrajectorySample
from movingpandas.trajectory_prediction_evaluator import TrajectoryPredictionEvaluator


CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)

 
class TestTrajectoryPredictionEvaluator:
    
    def test_errors_prediction_on_true_trajectory(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        true_traj = Trajectory(geo_df, 1)
        true_pos = Point(0, 10)
        predicted_pos = Point(0, 9)
        dummy_td = timedelta(seconds=1)
        sample = TrajectorySample(0, dummy_td, dummy_td, dummy_td, None, true_pos, true_traj)
        evaluator = TrajectoryPredictionEvaluator(sample, predicted_pos, CRS_METRIC, CRS_METRIC)
        result = evaluator.get_distance_error()
        expected_result = 1
        assert result == pytest.approx(expected_result, 0.001)
        result = evaluator.get_cross_track_error()
        expected_result = 0
        assert result == pytest.approx(expected_result, 0.001)
        result = evaluator.get_along_track_error()
        expected_result = 1
        assert result == pytest.approx(expected_result, 0.001)

    def test_errors_non_straight(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 8), 't': datetime(2018, 1, 1, 12, 0, 10)},
            {'geometry': Point(1, 9), 't': datetime(2018, 1, 1, 12, 0, 30)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 1, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        true_traj = Trajectory(geo_df, 1)
        true_pos = Point(0, 10)
        predicted_pos = Point(0, 8)
        dummy_td = timedelta(minutes=1)
        sample = TrajectorySample(0, dummy_td, dummy_td, dummy_td, None, true_pos, true_traj)
        evaluator = TrajectoryPredictionEvaluator(sample, predicted_pos, CRS_METRIC, CRS_METRIC)
        result = evaluator.get_distance_error()
        expected_result = 2
        assert result == pytest.approx(expected_result, 0.001)
        result = evaluator.get_cross_track_error()
        expected_result = 0
        assert result == pytest.approx(expected_result, 0.001)
        result = evaluator.get_along_track_error()
        expected_result = 2*sqrt(2)
        assert result == pytest.approx(expected_result, 0.001)

    def test_dist_error_latlon(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(0, 10), 't': datetime(2018, 1, 1, 12, 0, 1)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        true_traj = Trajectory(geo_df, 1)
        true_pos = Point(0, 10)
        predicted_pos = Point(0, 9)
        dummy_td = timedelta(seconds=1)
        sample = TrajectorySample(0, dummy_td, dummy_td, dummy_td, None, true_pos, true_traj)
        evaluator = TrajectoryPredictionEvaluator(sample, predicted_pos, CRS_METRIC, CRS_LATLON)
        result = evaluator.get_distance_error()
        expected_result = measure_distance_spherical(true_pos, predicted_pos)
        assert result == pytest.approx(expected_result, 0.001)
