# -*- coding: utf-8 -*-
#
# Test data and expected values adapted from scikit-mobility
# https://github.com/scikit-mobility/scikit-mobility
# Copyright (c) 2021, scikit-mobility contributors
# BSD 3-Clause License

import pytest
from pyproj import CRS

from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.mobility_metrics import MobilityMetricsCalculator
from .test_trajectory import Node, make_traj

CRS_LATLON = CRS.from_user_input(4326)
CRS_METRIC = CRS.from_user_input(31256)

NODES_U1 = [
    Node(10.5079940, 43.8430139, 2011, 2, 3, 8, 34, 4),
    Node(10.3261500, 43.5442700, 2011, 2, 3, 9, 34, 4),
    Node(10.4036000, 43.7085300, 2011, 2, 3, 10, 34, 4),
    Node(11.2462600, 43.7792500, 2011, 2, 4, 10, 34, 4),
]

NODES_U2 = [
    Node(10.5079940, 43.8430139, 2011, 2, 3, 8, 34, 4),
    Node(10.4036000, 43.7085300, 2011, 2, 3, 9, 34, 4),
    Node(10.5079940, 43.8430139, 2011, 2, 4, 10, 34, 4),
    Node(10.3261500, 43.5442700, 2011, 2, 4, 11, 34, 4),
]

NODES_U3 = [
    Node(10.3261500, 43.5442700, 2011, 2, 3, 8, 34, 4),
    Node(10.4036000, 43.7085300, 2011, 2, 3, 9, 34, 4),
    Node(10.5079940, 43.8430139, 2011, 2, 4, 10, 34, 4),
    Node(11.2462600, 43.7792500, 2011, 2, 4, 11, 34, 4),
]

NODES_U4 = [
    Node(10.4036000, 43.7085300, 2011, 2, 4, 10, 34, 4),
    Node(10.3261500, 43.5442700, 2011, 2, 4, 11, 34, 4),
    Node(11.2462600, 43.7792500, 2011, 2, 4, 12, 34, 4),
]

NODES_U5 = [
    Node(10.4036000, 43.7085300, 2011, 2, 4, 10, 34, 4),
    Node(11.2462600, 43.7792500, 2011, 2, 4, 11, 34, 4),
    Node(10.5079940, 43.8430139, 2011, 2, 5, 12, 34, 4),
]

NODES_U6 = [
    Node(10.5079940, 43.8430139, 2011, 2, 4, 10, 34, 4),
    Node(10.3261500, 43.5442700, 2011, 2, 4, 11, 34, 4),
]

NODES_U99 = [
    Node(0, 0, 2011, 2, 4, 10, 34, 4),
    Node(0, 20, 2011, 2, 4, 12, 34, 4),
]


class TestMobilityMetricsCalculator:
    def setup_method(self):
        self.traj1 = make_traj(NODES_U1, crs=CRS_LATLON, id=1)
        self.traj2 = make_traj(NODES_U2, crs=CRS_LATLON, id=2)
        self.traj3 = make_traj(NODES_U3, crs=CRS_LATLON, id=3)
        self.traj4 = make_traj(NODES_U4, crs=CRS_LATLON, id=4)
        self.traj5 = make_traj(NODES_U5, crs=CRS_LATLON, id=5)
        self.traj6 = make_traj(NODES_U6, crs=CRS_LATLON, id="A")
        self.collection = TrajectoryCollection(
            [
                self.traj1,
                self.traj2,
                self.traj3,
                self.traj4,
                self.traj5,
                self.traj6,
            ]
        )
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
        self.traj = make_traj(NODES_U99, crs=CRS_METRIC, id=99)
        self.calc = MobilityMetricsCalculator(self.traj)

    def test_radius_of_gyration_metric(self):
        rog = self.calc.radius_of_gyration()
        assert rog == pytest.approx(10, rel=1e-2)
