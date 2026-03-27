# -*- coding: utf-8 -*-
#
# Test data and expected values adapted from scikit-mobility
# https://github.com/scikit-mobility/scikit-mobility
# Copyright (c) 2021, scikit-mobility contributors
# BSD 3-Clause License

import pytest
import pandas as pd
from datetime import datetime
from geopandas import GeoDataFrame
from pyproj import CRS
from shapely.geometry import Point

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


class TestMobilityMetricsCalculatorMetricCRS:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [99, Point(0, 0), datetime(2011, 2, 4, 10, 34, 4)],
                [99, Point(0, 20), datetime(2011, 2, 4, 12, 34, 4)],
            ],
            columns=["id", "geometry", "t"],
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        traj = TrajectoryCollection(geo_df, traj_id_col="id").trajectories[0]
        self.calc = MobilityMetricsCalculator(traj)

    def test_radius_of_gyration_metric(self):
        rog = self.calc.radius_of_gyration()
        assert rog == pytest.approx(10, rel=1e-2)
