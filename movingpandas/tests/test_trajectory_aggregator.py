# -*- coding: utf-8 -*-

from pandas import DataFrame
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from pyproj import CRS
from datetime import datetime, timedelta
from movingpandas.trajectory import Trajectory
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_aggregator import (
    TrajectoryCollectionAggregator,
    _PtsExtractor,
)

CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestPtsExtractor:
    def test_sparse_trajectory(self):
        df = DataFrame(
            [
                {"id": 1, "geometry": Point(0, 0), "t": datetime(2018, 1, 1, 12, 0, 0)},
                {"id": 1, "geometry": Point(6, 0), "t": datetime(2018, 1, 1, 12, 6, 0)},
                {"id": 1, "geometry": Point(6, 6), "t": datetime(2018, 1, 1, 14, 9, 0)},
            ]
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        traj = Trajectory(geo_df, "id")
        extractor = _PtsExtractor(traj, 5, 0, min_stop_duration=timedelta(hours=12))
        actual = extractor.find_significant_points()
        expected = [Point(0, 0), Point(6, 0), Point(6, 6)]
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual

    def test_dense_trajectory(self):
        df = DataFrame(
            [
                {"id": 1, "geometry": Point(0, 0), "t": datetime(2018, 1, 1, 12, 0, 0)},
                {"id": 1, "geometry": Point(1, 0), "t": datetime(2018, 1, 1, 12, 1, 0)},
                {"id": 1, "geometry": Point(2, 0), "t": datetime(2018, 1, 1, 12, 2, 0)},
                {"id": 1, "geometry": Point(3, 0), "t": datetime(2018, 1, 1, 12, 3, 0)},
                {"id": 1, "geometry": Point(4, 0), "t": datetime(2018, 1, 1, 12, 4, 0)},
                {"id": 1, "geometry": Point(5, 0), "t": datetime(2018, 1, 1, 12, 5, 0)},
                {"id": 1, "geometry": Point(6, 0), "t": datetime(2018, 1, 1, 12, 6, 0)},
                {"id": 1, "geometry": Point(6, 6), "t": datetime(2018, 1, 1, 14, 9, 0)},
            ]
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        traj = Trajectory(geo_df, "id")
        extractor = _PtsExtractor(traj, 4, 0, min_stop_duration=timedelta(hours=12))
        actual = extractor.find_significant_points()
        expected = [Point(0, 0), Point(4, 0), Point(6, 0), Point(6, 6)]
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual

    def test_no_stops_found(self):
        df = DataFrame(
            [
                {"id": 1, "geometry": Point(0, 0), "t": datetime(2018, 1, 1, 10, 0, 0)},
                {"id": 1, "geometry": Point(1, 0), "t": datetime(2018, 1, 1, 10, 1, 0)},
                {"id": 1, "geometry": Point(2, 0), "t": datetime(2018, 1, 1, 10, 2, 0)},
                {"id": 1, "geometry": Point(3, 0), "t": datetime(2018, 1, 1, 12, 3, 0)},
                {"id": 1, "geometry": Point(4, 0), "t": datetime(2018, 1, 1, 12, 4, 0)},
                {"id": 1, "geometry": Point(5, 0), "t": datetime(2018, 1, 1, 12, 5, 0)},
                {"id": 1, "geometry": Point(6, 0), "t": datetime(2018, 1, 1, 14, 6, 0)},
                {"id": 1, "geometry": Point(7, 0), "t": datetime(2018, 1, 1, 14, 7, 0)},
            ]
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        traj = Trajectory(geo_df, "id")
        extractor = _PtsExtractor(traj, 10, 2, min_stop_duration=timedelta(hours=10))
        actual = extractor.find_significant_points()
        for pt in actual:
            print(pt)
        expected = [Point(0, 0), Point(7, 0)]
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual

    def test_stops_found(self):
        df = DataFrame(
            [
                {"id": 1, "geometry": Point(0, 0), "t": datetime(2018, 1, 1, 10, 0, 0)},
                {"id": 1, "geometry": Point(1, 0), "t": datetime(2018, 1, 1, 10, 1, 0)},
                {"id": 1, "geometry": Point(2, 0), "t": datetime(2018, 1, 1, 10, 2, 0)},
                {"id": 1, "geometry": Point(3, 0), "t": datetime(2018, 1, 1, 12, 3, 0)},
                {"id": 1, "geometry": Point(4, 0), "t": datetime(2018, 1, 1, 12, 4, 0)},
                {"id": 1, "geometry": Point(5, 0), "t": datetime(2018, 1, 1, 12, 5, 0)},
                {"id": 1, "geometry": Point(6, 0), "t": datetime(2018, 1, 1, 14, 6, 0)},
                {"id": 1, "geometry": Point(7, 0), "t": datetime(2018, 1, 1, 14, 7, 0)},
            ]
        ).set_index("t")
        geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        traj = Trajectory(geo_df, "id")
        extractor = _PtsExtractor(traj, 10, 2, min_stop_duration=timedelta(hours=1))
        actual = extractor.find_significant_points()
        for pt in actual:
            print(pt)
        expected = [Point(0, 0), Point(2, 0), Point(5, 0), Point(7, 0)]
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual


class TestTrajectoryCollectionAggregator:
    def setup_method(self):
        pt_coords = [(0, 0), (6, 0), (6, 6), (0.2, 0.2), (6.2, 0.2), (6.2, 6.2)]
        self.pts = [Point(x, y) for (x, y) in pt_coords]
        lst = [
            [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0)],
            [1, "A", Point(6, 0), datetime(2018, 1, 1, 12, 6, 0)],
            [1, "A", Point(6, 6), datetime(2018, 1, 1, 14, 10, 0)],
            [2, "A", Point(0.2, 0.2), datetime(2019, 1, 1, 12, 0, 0)],
            [2, "A", Point(6.2, 0.2), datetime(2019, 1, 1, 12, 6, 0)],
            [2, "A", Point(6.2, 6.2), datetime(2019, 1, 1, 14, 10, 0)],
        ]
        df = DataFrame(lst, columns=["id", "obj", "geometry", "t"]).set_index("t")
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, "id", obj_id_col="obj")
        self.trajectory_aggregator = TrajectoryCollectionAggregator(
            self.collection, 5, 0, min_stop_duration=timedelta(hours=12)
        )
        self.expected_clusters = GeoDataFrame(
            DataFrame(
                [[Point(0.1, 0.1), 2], [Point(6.1, 0.1), 2], [Point(6.1, 6.1), 2]],
                columns=["geometry", "n"],
            )
        )
        self.expected_flows = GeoDataFrame(
            DataFrame(
                [
                    [LineString([Point(0.1, 0.1), Point(6.1, 0.1)]), 2],
                    [LineString([Point(6.1, 0.1), Point(6.1, 6.1)]), 2],
                ],
                columns=["geometry", "weight"],
            )
        )
        self.geo_df_latlon = GeoDataFrame(df, crs=CRS_LATLON)
        self.geo_df_latlon.crs = CRS_LATLON  # try to fix
        # https://travis-ci.com/github/anitagraser/movingpandas/builds/177149345
        self.collection_latlon = TrajectoryCollection(
            self.geo_df_latlon, "id", obj_id_col="obj"
        )
        self.trajectory_aggregator_latlon = TrajectoryCollectionAggregator(
            self.collection_latlon, 100, 0, min_stop_duration=timedelta(hours=12)
        )

    def test_get_significant_points_gdf_crs_metric(self):
        sig_points = self.trajectory_aggregator.get_significant_points_gdf()
        assert sig_points.crs == CRS_METRIC
        actual = sig_points.geometry.tolist()
        expected = self.pts
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual

    def test_get_significant_points_gdf_crs_latlon(self):
        crs = self.trajectory_aggregator_latlon.get_significant_points_gdf().crs
        assert crs == CRS_LATLON

    def test_get_flows_gdf_crs_metric(self):
        flows = self.trajectory_aggregator.get_flows_gdf()
        assert flows.crs == CRS_METRIC
        actual = [(f.geometry, f.weight) for key, f in flows.iterrows()]
        expected = [(f.geometry, f.weight) for key, f in self.expected_flows.iterrows()]
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual

    def test_get_flows_gdf_crs_latlon(self):
        assert self.trajectory_aggregator_latlon.get_flows_gdf().crs == CRS_LATLON

    def test_get_clusters_gdf_crs_metric(self):
        clusters = self.trajectory_aggregator.get_clusters_gdf()
        assert clusters.crs == CRS_METRIC
        print(clusters)
        actual = [(c.geometry, c.n) for key, c in clusters.iterrows()]
        expected = [(c.geometry, c.n) for key, c in self.expected_clusters.iterrows()]
        for pt in expected:
            assert pt in actual

    def test_get_clusters_gdf_crs_latlon(self):
        assert self.trajectory_aggregator_latlon.get_clusters_gdf().crs == CRS_LATLON
