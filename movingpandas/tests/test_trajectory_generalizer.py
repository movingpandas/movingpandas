# -*- coding: utf-8 -*-

import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from pyproj import CRS
from datetime import datetime, timedelta
from .test_trajectory import make_traj, Node
from movingpandas.trajectory import Trajectory
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_generalizer import (
    MaxDistanceGeneralizer,
    MinDistanceGeneralizer,
    MinTimeDeltaGeneralizer,
    DouglasPeuckerGeneralizer,
    TopDownTimeRatioGeneralizer,
)


CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestTrajectoryGeneralizer:
    def setup_method(self):
        self.nodes = [
            Node(0, 0, day=1),
            Node(1, 0.1, day=2),
            Node(2, 0.2, day=3),
            Node(3, 0, day=4),
            Node(3, 3, day=5),
        ]
        self.traj = make_traj(self.nodes)
        df = pd.DataFrame(
            [{"xxx": n.geometry, "t": n.t} for n in self.nodes]
        ).set_index("t")
        geo_df = GeoDataFrame(df, geometry="xxx", crs=CRS_METRIC)
        self.traj_other_geometry_column_names = Trajectory(geo_df, 1)
        df = pd.DataFrame(
            [
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 9, "a"],
                [1, "A", Point(6, 0), datetime(2018, 1, 1, 12, 6, 0), 5, "b"],
                [1, "A", Point(6, 6), datetime(2018, 1, 1, 14, 10, 0), 2, "c"],
                [1, "A", Point(9, 9), datetime(2018, 1, 1, 14, 15, 0), 4, "d"],
                [2, "A", Point(10, 10), datetime(2018, 1, 1, 12, 0, 0), 10, "e"],
                [2, "A", Point(16, 10), datetime(2018, 1, 1, 12, 6, 0), 6, "f"],
                [2, "A", Point(16, 16), datetime(2018, 1, 2, 13, 10, 0), 7, "g"],
                [2, "A", Point(190, 19), datetime(2018, 1, 2, 13, 15, 0), 3, "h"],
            ],
            columns=["id", "obj", "geometry", "t", "val", "val2"],
        ).set_index("t")
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, "id", obj_id_col="obj")

    def test_douglas_peucker(self):
        result = DouglasPeuckerGeneralizer(self.traj).generalize(tolerance=1)
        assert result == make_traj([self.nodes[0], self.nodes[3], self.nodes[4]])

    def test_douglas_peucker_for_other_geometry_column_names(self):
        result = DouglasPeuckerGeneralizer(
            self.traj_other_geometry_column_names
        ).generalize(tolerance=1)
        assert result == make_traj([self.nodes[0], self.nodes[3], self.nodes[4]])

    def test_tdtr(self):
        result = TopDownTimeRatioGeneralizer(self.traj).generalize(tolerance=1)
        assert result == make_traj([self.nodes[0], self.nodes[3], self.nodes[4]])

    def test_tdtr_different_than_dp(self):
        nodes = [
            Node(),
            Node(1, 0.1, hour=1),
            Node(1, 2, hour=7),
            Node(2, 2, hour=15),
            Node(3, 0, hour=16),
            Node(3, 3, hour=17),
        ]
        traj = make_traj(nodes)
        result = TopDownTimeRatioGeneralizer(traj).generalize(tolerance=1)
        assert result == make_traj([nodes[0], nodes[2], nodes[3], nodes[4], nodes[5]])

    def test_tdtr_for_other_geometry_column_names(self):
        result = TopDownTimeRatioGeneralizer(
            self.traj_other_geometry_column_names
        ).generalize(tolerance=1)
        assert result == make_traj([self.nodes[0], self.nodes[3], self.nodes[4]])

    def test_max_distance(self):
        result = MaxDistanceGeneralizer(self.traj).generalize(tolerance=1)
        assert result == make_traj([self.nodes[0], self.nodes[3], self.nodes[4]])

    def test_max_distance_for_other_geometry_column_names(self):
        result = MaxDistanceGeneralizer(
            self.traj_other_geometry_column_names
        ).generalize(tolerance=1)
        assert result == make_traj([self.nodes[0], self.nodes[3], self.nodes[4]])

    def test_min_time_delta(self):
        nodes = [
            Node(),
            Node(1, 0.1, minute=6),
            Node(2, 0.2, minute=10),
            Node(3, 0, minute=30),
            Node(3, 3, minute=59),
        ]
        traj = make_traj(nodes)
        result = MinTimeDeltaGeneralizer(traj).generalize(timedelta(minutes=10))
        assert result == make_traj([nodes[0], nodes[2], nodes[3], nodes[4]])

    def test_min_distance(self):
        nodes = [
            Node(),
            Node(0, 0.1, day=2),
            Node(0, 0.2, day=3),
            Node(0, 1, day=4),
            Node(0, 3, day=5),
        ]
        traj = make_traj(nodes, CRS_METRIC)
        result = MinDistanceGeneralizer(traj).generalize(tolerance=1)
        assert result == make_traj([nodes[0], nodes[3], nodes[4]], CRS_METRIC)

    def test_collection(self):
        collection = MinTimeDeltaGeneralizer(self.collection).generalize(
            tolerance=timedelta(minutes=10)
        )
        assert len(collection) == 2
        wkt1 = collection.trajectories[0].to_linestring().wkt
        assert wkt1 == "LINESTRING (0 0, 6 6, 9 9)"
        wkt2 = collection.trajectories[1].to_linestring().wkt
        assert wkt2 == "LINESTRING (10 10, 16 16, 190 19)"
