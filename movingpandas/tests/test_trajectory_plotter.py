# -*- coding: utf-8 -*-

from pandas import DataFrame
from geopandas import GeoDataFrame
from shapely.geometry import Point
from pyproj import CRS
from datetime import datetime, timedelta
from movingpandas.trajectory import Trajectory
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_plotter import _TrajectoryPlotter

CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestTrajectoryCollection:
    def setup_method(self):
        df = DataFrame(
            [
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 9, "a"],
                [1, "A", Point(6, 0), datetime(2018, 1, 1, 12, 0, 6), 5, "b"],
                [1, "A", Point(10, 0), datetime(2018, 1, 1, 12, 0, 10), 2, "c"],
                [1, "A", Point(20, 0), datetime(2018, 1, 1, 12, 0, 15), 4, "d"],
                [2, "A", Point(10, 10), datetime(2018, 1, 1, 12, 0, 0), 10, "e"],
                [2, "A", Point(16, 10), datetime(2018, 1, 1, 12, 0, 6), 6, "f"],
                [2, "A", Point(20, 10), datetime(2018, 1, 1, 12, 0, 10), 7, "g"],
                [2, "A", Point(35, 10), datetime(2018, 1, 1, 12, 0, 15), 3, "h"],
            ],
            columns=["id", "obj", "geometry", "t", "val", "val2"],
        ).set_index("t")
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, "id", obj_id_col="obj")

    def test_get_min_max_values(self):
        self.plotter = _TrajectoryPlotter(self.collection, column="val")
        min_value, max_value = self.plotter.get_min_max_values()
        assert min_value == 2
        assert max_value == 10


class TestTrajectoryCollectionNonGeo:
    def setup_method(self):
        n = 3
        start = datetime(2023, 1, 1)
        data = {
            "t": [start + timedelta(seconds=i) for i in range(n)],
            "x": [0, 1, 2],
            "y": [0, 0, 0],
            "val": [2, 5, 10],
        }
        df = DataFrame(data)
        self.traj_nongeo_xyt = Trajectory(
            df, traj_id=1, t="t", x="x", y="y", crs=CRS_METRIC
        )

        data = {
            "a": [start + timedelta(seconds=i) for i in range(n)],
            "b": [0, 1, 2],
            "c": [0, 0, 0],
            "val": [2, 5, 10],
        }
        df = DataFrame(data)
        self.traj_nongeo_abc = Trajectory(
            df, traj_id=1, t="a", x="b", y="c", crs=CRS_METRIC
        )

    def test_get_min_max_values_nongeo(self):
        self.plotter = _TrajectoryPlotter(self.traj_nongeo_xyt, column="val")
        min_value, max_value = self.plotter.get_min_max_values()
        assert min_value == 2
        assert max_value == 10

    def test_get_min_max_values_nongeo_custom_cols(self):
        self.plotter = _TrajectoryPlotter(self.traj_nongeo_abc, column="val")
        min_value, max_value = self.plotter.get_min_max_values()
        assert min_value == 2
        assert max_value == 10
