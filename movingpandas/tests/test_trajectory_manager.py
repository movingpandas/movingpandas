# -*- coding: utf-8 -*-

import pytest
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import datetime
from movingpandas.trajectory_manager import TrajectoryManager


class TestTrajectoryManager:

    def setup_method(self):
        df = pd.DataFrame([
            {'id': 1, 'geometry': Point(0, 0), 't': datetime(2018,1,1,12,0,0)},
            {'id': 1, 'geometry': Point(6, 0), 't': datetime(2018,1,1,12,6,0)},
            {'id': 1, 'geometry': Point(6, 6), 't': datetime(2018,1,1,12,10,0)},
            {'id': 1, 'geometry': Point(9, 9), 't': datetime(2018,1,1,12,15,0)},
            {'id': 2, 'geometry': Point(10, 10), 't': datetime(2018,1,1,12,0,0)},
            {'id': 2, 'geometry': Point(16, 10), 't': datetime(2018,1,1,12,6,0)},
            {'id': 2, 'geometry': Point(16, 16), 't': datetime(2018,1,2,12,10,0)},
            {'id': 2, 'geometry': Point(190, 19), 't': datetime(2018,1,2,12,15,0)}
        ]).set_index('t')
        self.geo_df = GeoDataFrame(df, crs={'init': '31256'})

    def test_number_of_trajectories(self):
        tm = TrajectoryManager(self.geo_df, 'id')
        assert len(tm) == 2

    def test_number_of_trajectories_min_length(self):
        tm = TrajectoryManager(self.geo_df, 'id', min_length=100)
        assert len(tm) == 1

    def test_number_of_trajectories_min_length_never_reached(self):
        tm = TrajectoryManager(self.geo_df, 'id', min_length=1000)
        assert len(tm) == 0

    def test_split_by_date(self):
        tm = TrajectoryManager(self.geo_df, 'id')
        tm = tm.split_by_date(mode='day')
        assert len(tm) == 3
