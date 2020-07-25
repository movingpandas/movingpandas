# -*- coding: utf-8 -*-

import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from pyproj import CRS
from datetime import datetime, timedelta
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_aggregator import TrajectoryCollectionAggregator


CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestTrajectoryCollectionAggregator:

    def setup_method(self):
        df = pd.DataFrame([
            {'id': 1, 'obj': 'A', 'geometry': Point(0, 0), 't': datetime(2018,1,1,12,0,0), 'val': 9, 'val2': 'a'},
            {'id': 1, 'obj': 'A', 'geometry': Point(6, 0), 't': datetime(2018,1,1,12,6,0), 'val': 5, 'val2': 'b'},
            {'id': 1, 'obj': 'A', 'geometry': Point(6, 6), 't': datetime(2018,1,1,14,10,0), 'val': 2, 'val2': 'c'}
        ]).set_index('t')
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, 'id', obj_id_col='obj')
        self.trajectory_aggregator = TrajectoryCollectionAggregator(self.collection, 100, 0, min_stop_duration=timedelta(hours=12).seconds)
        self.geo_df_latlon = GeoDataFrame(df, crs=CRS_LATLON)
        self.geo_df_latlon.crs = CRS_LATLON  # try to fix https://travis-ci.com/github/anitagraser/movingpandas/builds/177149345
        self.collection_latlon = TrajectoryCollection(self.geo_df_latlon, 'id', obj_id_col='obj')
        self.trajectory_aggregator_latlon = TrajectoryCollectionAggregator(self.collection_latlon, 100, 0, min_stop_duration=timedelta(hours=12).seconds)

    def test_get_significant_points_gdf_crs_metric(self):
        crs = self.trajectory_aggregator.get_significant_points_gdf().crs
        print("Expected {} and got {}.".format(CRS_METRIC.name, crs.name))
        assert crs == CRS_METRIC

    def test_get_significant_points_gdf_crs_latlon(self):
        print("Raw GDF crs: {}".format(self.geo_df_latlon.crs.name))
        crs = self.trajectory_aggregator_latlon.get_significant_points_gdf().crs
        print("Expected {} and got {}.".format(CRS_LATLON.name, crs.name))
        assert crs == CRS_LATLON

    def test_get_flows_gdf_crs_metric(self):
        assert self.trajectory_aggregator.get_flows_gdf().crs == CRS_METRIC

    def test_get_flows_gdf_crs_latlon(self):
        assert self.trajectory_aggregator_latlon.get_flows_gdf().crs == CRS_LATLON

    def test_get_clusters_gdf_crs_metric(self):
        assert self.trajectory_aggregator.get_clusters_gdf().crs == CRS_METRIC

    def test_get_clusters_gdf_crs_latlon(self):
        assert self.trajectory_aggregator_latlon.get_clusters_gdf().crs == CRS_LATLON
