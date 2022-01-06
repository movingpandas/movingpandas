# -*- coding: utf-8 -*-

from movingpandas.trajectory_collection import TrajectoryCollection
from .test_trajectory import make_traj, Node
from movingpandas.trajectory_cleaner import OutlierCleaner
import pandas as pd
from fiona.crs import from_epsg
from shapely.geometry import Point
from datetime import datetime
from geopandas import GeoDataFrame

CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)


class TestTrajectoryCleaner:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 3, 10],
                [1, "A", Point(1, 1), datetime(2018, 1, 1, 12, 1, 0), 1, 14],
                [1, "A", Point(3, 1), datetime(2018, 1, 1, 12, 2, 0), 3, 11],
                [1, "A", Point(6, 0), datetime(2018, 1, 1, 12, 6, 0), -10, 20],
                [1, "A", Point(6, 6), datetime(2018, 1, 1, 14, 10, 0), 20, 200],
                [1, "A", Point(9, 9), datetime(2018, 1, 1, 14, 15, 0), 2, 20],
                [2, "A", Point(10, 10), datetime(2018, 1, 1, 12, 0, 0), 30, 20],
                [2, "A", Point(16, 10), datetime(2018, 1, 1, 12, 6, 0), 30, 30],
                [2, "A", Point(16, 12), datetime(2018, 1, 1, 12, 9, 0), 40, 30],
                [2, "A", Point(20, 20), datetime(2018, 1, 1, 12, 20, 0), 1000, 30],
                [2, "A", Point(16, 16), datetime(2018, 1, 2, 13, 10, 0), 20, -30],
                [2, "A", Point(190, 19), datetime(2018, 1, 2, 13, 15, 0), 20, 50],
            ],
            columns=["id", "obj", "geometry", "t", "val", "val2"],
        ).set_index("t")
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, "id", obj_id_col="obj")

    def test_outlier_cleaner_traj(self):
        traj = make_traj(
            [
                Node(),
                Node(1, 0.1, day=2, value=1),
                Node(2, 0.2, day=3, value=3),
                Node(3, 0, day=4, value=10),
                Node(3, 3, day=5, value=2),
                Node(4, 3, day=6, value=1),
                Node(5, 5, day=7, value=1),
            ]
        )
        result = OutlierCleaner(traj).clean(columns={"value": 3})
        assert result == make_traj(
            [
                Node(),
                Node(1, 0.1, day=2, value=1),
                Node(2, 0.2, day=3, value=3),
                Node(3, 3, day=5, value=2),
                Node(4, 3, day=6, value=1),
                Node(5, 5, day=7, value=1),
            ]
        )

    def test_outlier_cleaner_collection(self):
        collection = OutlierCleaner(self.collection).clean(
            columns={"val": 3, "val2": 3}
        )
        assert len(collection) == 2
        wkt1 = collection.trajectories[0].to_linestring().wkt
        assert wkt1 == "LINESTRING (0 0, 1 1, 3 1, 9 9)"
        wkt2 = collection.trajectories[1].to_linestring().wkt
        assert wkt2 == "LINESTRING (10 10, 16 10, 16 12, 190 19)"
