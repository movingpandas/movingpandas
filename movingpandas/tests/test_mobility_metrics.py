# -*- coding: utf-8 -*-
#
# Test data and expected values adapted from scikit-mobility
# https://github.com/scikit-mobility/scikit-mobility
# Copyright (c) 2021, scikit-mobility contributors
# BSD 3-Clause License

import math
import pytest
import pandas as pd
from datetime import datetime, time
from geopandas import GeoDataFrame
from pyproj import CRS
from shapely.geometry import Point

from movingpandas.trajectory import Trajectory
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.mobility_metrics import MobilityMetricsCalculator

CRS_LATLON = CRS.from_user_input(4326)
CRS_METRIC = CRS.from_user_input(31256)


class TestMobilityMetricsCalculator:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [1, Point(10.507994, 43.843014), datetime(2011, 2, 3, 8, 34, 4)],
                [1, Point(10.326150, 43.544270), datetime(2011, 2, 3, 9, 34, 4)],
                [1, Point(10.403600, 43.708530), datetime(2011, 2, 3, 10, 34, 4)],
                [1, Point(11.246260, 43.779250), datetime(2011, 2, 4, 10, 34, 4)],
                [2, Point(10.507994, 43.843014), datetime(2011, 2, 3, 8, 34, 4)],
                [2, Point(10.403600, 43.708530), datetime(2011, 2, 3, 9, 34, 4)],
                [2, Point(10.507994, 43.843014), datetime(2011, 2, 4, 10, 34, 4)],
                [2, Point(10.326150, 43.544270), datetime(2011, 2, 4, 11, 34, 4)],
                [3, Point(10.326150, 43.544270), datetime(2011, 2, 3, 8, 34, 4)],
                [3, Point(10.403600, 43.708530), datetime(2011, 2, 3, 9, 34, 4)],
                [3, Point(10.507994, 43.843014), datetime(2011, 2, 4, 10, 34, 4)],
                [3, Point(11.246260, 43.779250), datetime(2011, 2, 4, 11, 34, 4)],
                [4, Point(10.403600, 43.708530), datetime(2011, 2, 4, 10, 34, 4)],
                [4, Point(10.326150, 43.544270), datetime(2011, 2, 4, 11, 34, 4)],
                [4, Point(11.246260, 43.779250), datetime(2011, 2, 4, 12, 34, 4)],
                [5, Point(10.403600, 43.708530), datetime(2011, 2, 4, 10, 34, 4)],
                [5, Point(11.246260, 43.779250), datetime(2011, 2, 4, 11, 34, 4)],
                [5, Point(10.507994, 43.843014), datetime(2011, 2, 5, 12, 34, 4)],
                ["A", Point(10.507994, 43.843014), datetime(2011, 2, 4, 10, 34, 4)],
                ["A", Point(10.326150, 43.544270), datetime(2011, 2, 4, 11, 34, 4)],
            ],
            columns=["id", "geometry", "t"],
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        self.collection = TrajectoryCollection(geo_df, traj_id_col="id")
        self.calc = MobilityMetricsCalculator(self.collection)

    def test_random_entropy(self):
        re = self.calc.random_entropy()
        assert len(re) == 6
        assert re.loc[1] == pytest.approx(math.log2(4), rel=1e-2)  # 2.0
        assert re.loc[2] == pytest.approx(math.log2(3), rel=1e-2)  # 1.585
        assert re.loc[3] == pytest.approx(math.log2(4), rel=1e-2)  # 2.0
        assert re.loc[4] == pytest.approx(math.log2(3), rel=1e-2)  # 1.585
        assert re.loc[5] == pytest.approx(math.log2(3), rel=1e-2)  # 1.585
        assert re.loc["A"] == pytest.approx(math.log2(2), rel=1e-2)  # 1.0

    def test_radius_of_gyration(self):
        rog = self.calc.radius_of_gyration()
        assert len(rog) == 6
        # original values in km in comments, differences due to more precise
        # distance calculations (using GeoPy) compared to scikit-mobility,
        # which uses a simplified Haversine formula
        assert rog.loc[1] == pytest.approx(32035.10, rel=1e-2)  # 31.964885737
        assert rog.loc[2] == pytest.approx(14985.89, rel=1e-2)  # 14.988909726
        assert rog.loc[3] == pytest.approx(32035.10, rel=1e-2)  # 31.964885737
        assert rog.loc[4] == pytest.approx(35325.09, rel=1e-2)  # 35.241089869
        assert rog.loc[5] == pytest.approx(30806.80, rel=1e-2)  # 30.727237693
        assert rog.loc["A"] == pytest.approx(18142.77, rel=1e-2)  # 18.146860183

    def test_distance_straight_line(self):
        dsl = self.calc.distance_straight_line()
        assert len(dsl) == 6
        # original values in km in comments, differences due to more precise
        # distance calculations compared to scikit-mobility's Haversine formula
        assert dsl.loc[1] == pytest.approx(123906.01, rel=1e-2)  # 123.74008488
        assert dsl.loc[2] == pytest.approx(70572.91, rel=1e-2)  # 70.57908362
        assert dsl.loc[3] == pytest.approx(96256.40, rel=1e-2)  # 96.10397212
        assert dsl.loc[4] == pytest.approx(97964.95, rel=1e-2)  # 97.79046189
        assert dsl.loc[5] == pytest.approx(128151.39, rel=1e-2)  # 127.8088686
        assert dsl.loc["A"] == pytest.approx(36285.54, rel=1e-2)  # 36.29370121

    def test_home_location_fallback(self):
        # All timestamps are daytime, so nighttime window returns nothing and
        # home falls back to the most visited location overall.
        # Ties are broken by sorting locations by (lat, lon) ascending, matching
        # scikit-mobility's groupby sort order.
        hl = self.calc.home_location()
        assert len(hl) == 6
        assert hl.loc[1] == Point(
            10.326150, 43.544270
        )  # 4 unique locs, tie → lowest lat
        assert hl.loc[2] == Point(10.507994, 43.843014)  # visited twice → clear winner
        assert hl.loc[3] == Point(
            10.326150, 43.544270
        )  # 4 unique locs, tie → lowest lat
        assert hl.loc[4] == Point(
            10.326150, 43.544270
        )  # 3 unique locs, tie → lowest lat
        assert hl.loc[5] == Point(
            10.403600, 43.708530
        )  # 3 unique locs, tie → lowest lat
        assert hl.loc["A"] == Point(
            10.326150, 43.544270
        )  # 2 unique locs, tie → lowest lat


class TestMobilityMetricsCalculatorMetricCRS:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [99, Point(0, 0), datetime(2011, 2, 4, 10, 34, 4)],
                [99, Point(0, 20), datetime(2011, 2, 4, 23, 34, 4)],
            ],
            columns=["id", "geometry", "t"],
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        traj = Trajectory(geo_df, traj_id=99)
        self.calc = MobilityMetricsCalculator(traj)

    def test_radius_of_gyration_metric(self):
        rog = self.calc.radius_of_gyration()
        assert rog == pytest.approx(10, rel=1e-2)

    def test_random_entropy_metric(self):
        assert self.calc.random_entropy() == pytest.approx(math.log2(2), rel=1e-2)

    def test_distance_straight_line_metric(self):
        assert self.calc.distance_straight_line() == pytest.approx(20, rel=1e-2)

    def test_home_location_single_traj(self):
        # Single trajectory → returns a Point, not a Series
        assert self.calc.home_location() == Point(0, 20)


class TestMobilityMetricsCalculatorNoCRS:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [99, Point(0, 0), datetime(2011, 2, 4, 10, 34, 4)],
                [99, Point(0, 20), datetime(2011, 2, 4, 12, 34, 4)],
            ],
            columns=["id", "geometry", "t"],
        ).set_index("t")
        geo_df = GeoDataFrame(df)
        traj = Trajectory(geo_df, traj_id=99, crs=None)
        self.calc = MobilityMetricsCalculator(traj)

    def test_radius_of_gyration_no_crs(self):
        rog = self.calc.radius_of_gyration()
        assert rog == pytest.approx(10, rel=1e-2)

    def test_random_entropy_no_crs(self):
        assert self.calc.random_entropy() == pytest.approx(math.log2(2), rel=1e-2)

    def test_distance_straight_line_no_crs(self):
        assert self.calc.distance_straight_line() == pytest.approx(20, rel=1e-2)


class TestMobilityMetricsCalculatorHomeLocationNighttime:
    def setup_method(self):
        # Explicit nighttime timestamps to test the primary nighttime logic.
        # User 1: visits A twice at 23:00, B once at 23:00, C once at 10:00 (daytime)
        #   → nighttime: A=2, B=1 → home = A = Point(10.507994, 43.843014)
        # User 2: visits B three times at 23:00, A once at 10:00 (daytime)
        #   → nighttime: B=3 → home = B = Point(10.326150, 43.544270)
        df = pd.DataFrame(
            [
                [1, Point(10.507994, 43.843014), datetime(2011, 2, 3, 23, 0, 0)],
                [1, Point(10.507994, 43.843014), datetime(2011, 2, 4, 23, 0, 0)],
                [1, Point(10.326150, 43.544270), datetime(2011, 2, 5, 23, 0, 0)],
                [1, Point(11.246260, 43.779250), datetime(2011, 2, 6, 10, 0, 0)],
                [2, Point(10.326150, 43.544270), datetime(2011, 2, 3, 23, 0, 0)],
                [2, Point(10.326150, 43.544270), datetime(2011, 2, 4, 23, 0, 0)],
                [2, Point(10.326150, 43.544270), datetime(2011, 2, 5, 23, 0, 0)],
                [2, Point(10.507994, 43.843014), datetime(2011, 2, 6, 10, 0, 0)],
            ],
            columns=["id", "geometry", "t"],
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_LATLON)
        self.collection = TrajectoryCollection(geo_df, traj_id_col="id")
        self.calc = MobilityMetricsCalculator(self.collection)

    def test_home_location_nighttime_collection(self):
        hl = self.calc.home_location()
        assert len(hl) == 2
        assert hl.loc[1] == Point(10.507994, 43.843014)
        assert hl.loc[2] == Point(10.326150, 43.544270)

    def test_home_location_nighttime_single(self):
        traj1 = self.collection.get_trajectory(1)
        assert MobilityMetricsCalculator(traj1).home_location() == Point(
            10.507994, 43.843014
        )

    def test_home_location_time_objects(self):
        hl = self.calc.home_location(start_night=time(22, 0), end_night=time(7, 0))
        assert hl.loc[1] == Point(10.507994, 43.843014)
        assert hl.loc[2] == Point(10.326150, 43.544270)
