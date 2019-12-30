# -*- coding: utf-8 -*-

import pytest
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from fiona.crs import from_epsg
from datetime import datetime
from movingpandas.trajectory_collection import TrajectoryCollection


CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)


class TestTrajectoryCollection:

    def setup_method(self):
        df = pd.DataFrame([
            {'id': 1, 'obj': 'A', 'geometry': Point(0, 0), 't': datetime(2018,1,1,12,0,0), 'val': 9},
            {'id': 1, 'obj': 'A', 'geometry': Point(6, 0), 't': datetime(2018,1,1,12,6,0), 'val': 5},
            {'id': 1, 'obj': 'A', 'geometry': Point(6, 6), 't': datetime(2018,1,1,12,10,0), 'val': 2},
            {'id': 1, 'obj': 'A', 'geometry': Point(9, 9), 't': datetime(2018,1,1,12,15,0), 'val': 4},
            {'id': 2, 'obj': 'A', 'geometry': Point(10, 10), 't': datetime(2018,1,1,12,0,0), 'val': 10},
            {'id': 2, 'obj': 'A', 'geometry': Point(16, 10), 't': datetime(2018,1,1,12,6,0), 'val': 6},
            {'id': 2, 'obj': 'A', 'geometry': Point(16, 16), 't': datetime(2018,1,2,12,10,0), 'val': 7},
            {'id': 2, 'obj': 'A', 'geometry': Point(190, 19), 't': datetime(2018,1,2,12,15,0), 'val': 3}
        ]).set_index('t')
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, 'id', obj_id_col='obj')
        self.geo_df_latlon = GeoDataFrame(df, crs=CRS_LATLON)
        self.collection_latlon = TrajectoryCollection(self.geo_df_latlon, 'id', obj_id_col='obj')

    def test_number_of_trajectories(self):
        assert len(self.collection) == 2

    def test_number_of_trajectories_min_length(self):
        collection = TrajectoryCollection(self.geo_df, 'id', obj_id_col='obj', min_length=100)
        assert len(collection) == 1

    def test_number_of_trajectories_min_length_never_reached(self):
        collection = TrajectoryCollection(self.geo_df, 'id', obj_id_col='obj', min_length=1000)
        assert len(collection) == 0

    def test_split_by_date(self):
        collection = self.collection.split_by_date(mode='day')
        assert len(collection) == 3

    def test_get_trajectory(self):
        assert self.collection.get_trajectory(1).id == 1
        assert self.collection.get_trajectory(1).obj_id == 'A'
        assert self.collection.get_trajectory(2).id == 2
        assert self.collection.get_trajectory(3) is None

    def test_filter(self):
        assert len(self.collection.filter('obj', 'A')) == 2
        assert len(self.collection.filter('obj', 'B')) == 0

    def test_get_min_and_max(self):
        assert self.collection.get_min('val') == 2
        assert self.collection.get_max('val') == 10

    def test_get_start_locations(self):
        locs = self.collection.get_start_locations(columns=['val'])
        assert len(locs) == 2
        assert locs.iloc[0].geometry in [Point(0, 0), Point(10, 10)]
        assert locs.iloc[0].traj_id in [1, 2]
        assert locs.iloc[0].obj_id == 'A'
        assert locs.iloc[0].val in [9, 10]
        assert locs.iloc[1].geometry in [Point(0, 0), Point(10, 10)]

    def test_plot_exists(self):
        from matplotlib.axes import Axes
        result = self.collection.plot()
        assert isinstance(result, Axes)

    def test_hvplot_exists(self):
        import holoviews
        result = self.collection_latlon.hvplot()
        assert isinstance(result, holoviews.core.overlay.Overlay)
