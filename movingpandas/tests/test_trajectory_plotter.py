# -*- coding: utf-8 -*-

import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from fiona.crs import from_epsg
from datetime import datetime
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_plotter import _TrajectoryCollectionPlotter

CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)


class TestTrajectoryCollection:

    def setup_method(self):
        df = pd.DataFrame([
            {'id': 1, 'obj': 'A', 'geometry': Point(0, 0), 't': datetime(2018,1,1,12,0,0), 'val': 9, 'val2': 'a'},
            {'id': 1, 'obj': 'A', 'geometry': Point(6, 0), 't': datetime(2018,1,1,12,0,6), 'val': 5, 'val2': 'b'},
            {'id': 1, 'obj': 'A', 'geometry': Point(10, 0), 't': datetime(2018,1,1,12,0,10), 'val': 2, 'val2': 'c'},
            {'id': 1, 'obj': 'A', 'geometry': Point(20, 0), 't': datetime(2018,1,1,12,0,15), 'val': 4, 'val2': 'd'},
            {'id': 2, 'obj': 'A', 'geometry': Point(10, 10), 't': datetime(2018,1,1,12,0,0), 'val': 10, 'val2': 'e'},
            {'id': 2, 'obj': 'A', 'geometry': Point(16, 10), 't': datetime(2018,1,1,12,0,6), 'val': 6, 'val2': 'f'},
            {'id': 2, 'obj': 'A', 'geometry': Point(20, 10), 't': datetime(2018,1,1,12,0,10), 'val': 7, 'val2': 'g'},
            {'id': 2, 'obj': 'A', 'geometry': Point(35, 10), 't': datetime(2018,1,1,12,0,15), 'val': 3, 'val2': 'h'}
        ]).set_index('t')
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, 'id', obj_id_col='obj')

    def test_get_min_max_values(self):
        self.plotter = _TrajectoryCollectionPlotter(self.collection, column='val')
        min_value, max_value = self.plotter.get_min_max_values()
        assert min_value == 2
        assert max_value == 10

    def test_get_min_max_speed(self):
        self.plotter = _TrajectoryCollectionPlotter(self.collection, column='speed')
        min_value, max_value = self.plotter.get_min_max_values()
        assert min_value == 1
        assert max_value == 3

