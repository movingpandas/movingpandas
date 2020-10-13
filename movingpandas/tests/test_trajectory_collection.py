# -*- coding: utf-8 -*-

import pandas as pd
import pytest
from geopandas import GeoDataFrame
from shapely.geometry import Point, Polygon
from fiona.crs import from_epsg
from datetime import datetime, timedelta
from copy import copy
from movingpandas.trajectory_collection import TrajectoryCollection

from .markers import importthenskip


CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)


class TestTrajectoryCollection:

    def setup_method(self):
        df = pd.DataFrame([
            {'id': 1, 'obj': 'A', 'geometry': Point(0, 0), 't': datetime(2018,1,1,12,0,0), 'val': 9, 'val2': 'a'},
            {'id': 1, 'obj': 'A', 'geometry': Point(6, 0), 't': datetime(2018,1,1,12,6,0), 'val': 5, 'val2': 'b'},
            {'id': 1, 'obj': 'A', 'geometry': Point(6, 6), 't': datetime(2018,1,1,14,10,0), 'val': 2, 'val2': 'c'},
            {'id': 1, 'obj': 'A', 'geometry': Point(9, 9), 't': datetime(2018,1,1,14,15,0), 'val': 4, 'val2': 'd'},
            {'id': 2, 'obj': 'A', 'geometry': Point(10, 10), 't': datetime(2018,1,1,12,0,0), 'val': 10, 'val2': 'e'},
            {'id': 2, 'obj': 'A', 'geometry': Point(16, 10), 't': datetime(2018,1,1,12,6,0), 'val': 6, 'val2': 'f'},
            {'id': 2, 'obj': 'A', 'geometry': Point(16, 16), 't': datetime(2018,1,2,13,10,0), 'val': 7, 'val2': 'g'},
            {'id': 2, 'obj': 'A', 'geometry': Point(190, 19), 't': datetime(2018,1,2,13,15,0), 'val': 3, 'val2': 'h'}
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

    def test_get_trajectory(self):
        assert self.collection.get_trajectory(1).id == 1
        assert self.collection.get_trajectory(1).obj_id == 'A'
        assert self.collection.get_trajectory(2).id == 2
        assert self.collection.get_trajectory(3) is None

    def test_get_locations_at(self):
        locs = self.collection.get_locations_at(datetime(2018,1,1,12,6,0))
        assert len(locs) == 2
        assert locs.iloc[0].geometry in [Point(6, 0), Point(16, 10)]
        assert locs.iloc[0].val in [5, 6]
        assert locs.iloc[1].geometry in [Point(6, 0), Point(16, 10)]
        assert locs.iloc[0].geometry != locs.iloc[1].geometry

    def test_get_locations_at_needing_interpolation(self):
        locs = self.collection.get_locations_at(datetime(2018,1,1,12,6,1))
        assert len(locs) == 2
        assert locs.iloc[0].val in [5, 6]

    def test_get_locations_at_out_of_time_range(self):
        locs = self.collection.get_locations_at(datetime(2017,1,1,12,6,1))
        assert len(locs) == 0

    def test_get_start_locations(self):
        locs = self.collection.get_start_locations()
        assert len(locs) == 2
        assert locs.iloc[0].geometry in [Point(0, 0), Point(10, 10)]
        assert locs.iloc[0].id in [1, 2]
        assert locs.iloc[0].obj == 'A'
        assert locs.iloc[0].val in [9, 10]
        assert locs.iloc[0].val2 in ['a', 'e']
        assert locs.iloc[1].geometry in [Point(0, 0), Point(10, 10)]
        assert locs.iloc[0].geometry != locs.iloc[1].geometry

    def test_get_end_locations(self):
        locs = self.collection.get_end_locations()
        assert len(locs) == 2
        assert locs.iloc[0].geometry in [Point(9, 9), Point(190, 19)]
        assert locs.iloc[0].id in [1, 2]
        assert locs.iloc[0].obj == 'A'
        assert locs.iloc[0].val in [4, 3]
        assert locs.iloc[0].val2 in ['d', 'h']
        assert locs.iloc[1].geometry in [Point(9, 9), Point(190, 19)]
        assert locs.iloc[0].geometry != locs.iloc[1].geometry

    def test_get_intersecting(self):
        polygon = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)])
        collection = self.collection.get_intersecting(polygon)
        assert len(collection) == 1
        assert collection.trajectories[0] == self.collection.trajectories[0]

    def test_clip(self):
        polygon = Polygon([(-1, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)])
        collection = self.collection.clip(polygon)
        assert len(collection) == 1
        assert collection.trajectories[0].to_linestring().wkt == 'LINESTRING (0 0, 1 0)'

    def test_filter(self):
        assert len(self.collection.filter('obj', 'A')) == 2
        assert len(self.collection.filter('obj', 'B')) == 0

    def test_get_min_and_max(self):
        assert self.collection.get_min('val') == 2
        assert self.collection.get_max('val') == 10

    def test_plot_exists(self):
        from matplotlib.axes import Axes
        result = self.collection.plot()
        assert isinstance(result, Axes)

    def test_hvplot_exists(self):
        holoviews = pytest.importorskip("holoviews")
        result = self.collection_latlon.hvplot()
        assert isinstance(result, holoviews.core.overlay.Overlay)

    def test_hvplot_fails_without_holoviews(self):
        importthenskip('holoviews', minversion='1')
        with pytest.raises(ImportError):
            self.collection_latlon.hvplot()

    def test_plot_exist_column(self):
        from matplotlib.axes import Axes
        result = self.collection.plot(column='val')
        assert isinstance(result, Axes)

    def test_iteration(self):
        assert sum([1 for _ in self.collection]) == len(self.collection)

    def test_iteration_error(self):
        def filter_trajectory(trajectory):
            trajectory.df = trajectory.df[trajectory.df['val'] >= 7]
            return trajectory

        trajs = [filter_trajectory(traj) for traj in self.collection]

        lengths = (1, 2)
        for i, traj in enumerate(trajs):
            assert len(traj.df) == lengths[i]

        collection = copy(self.collection)
        collection.trajectories = trajs
        with pytest.raises(ValueError):
            for _ in collection:
                pass
