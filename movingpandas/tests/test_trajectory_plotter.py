# -*- coding: utf-8 -*-

import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from pyproj import CRS
from datetime import datetime
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_plotter import _TrajectoryPlotter

CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestTrajectoryCollection:
    def setup_method(self):
        df = pd.DataFrame(
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
