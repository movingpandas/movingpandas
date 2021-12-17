# -*- coding: utf-8 -*-

import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from fiona.crs import from_epsg
from geopandas import GeoDataFrame
from shapely.geometry import Point
from shapely.wkt import loads

from movingpandas.trajectory_collection import TrajectoryCollection

from .test_trajectory import make_traj, Node
from . import requires_stonesoup

CRS_METRIC = from_epsg(31256)


class TestTrajectorySmoother:

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

    @requires_stonesoup
    def test_kalman_smoother_cv_single(self):
        from movingpandas.trajectory_smoother import KalmanSmootherCV
        traj = make_traj([Node(), Node(1, 0.1, second=1), Node(2, 0.2, second=2), Node(3, 0, second=3), Node(3, 3, second=4)])
        result = KalmanSmootherCV(traj).smooth(process_noise_std=0.1, measurement_noise_std=10)
        truth = loads('LINESTRING (1.798868492442355 0.6586892921477556, 1.799237989172711 0.6589728491380811, 1.800213282871148 0.6597703006118536, 1.801551328884808 0.6609615702182055, 1.803029113866919 0.6623756028711796)')
        assert np.allclose(result.to_linestring().xy, truth.xy)

    @requires_stonesoup
    def test_kalman_smoother_sv_collection(self):
        from movingpandas.trajectory_smoother import KalmanSmootherCV
        collection = KalmanSmootherCV(self.collection).smooth(process_noise_std=0.1, measurement_noise_std=10)
        truth_1 = loads('LINESTRING (0.005060459517095535 0.0002300338819622993, 5.996064188703684 6.937421858310699e-05, 6.000985887760065 6.000310433097184, 9.000209211771365 9.000005868263543)')
        truth_2 = loads('LINESTRING (10.00500926703283 10.00016289390624, 15.99614620902795 10.00014491192997, 16.00145501559013 16.00016856286675, 189.9997096982685 19.00013939198107)')
        assert len(collection) == 2
        assert np.allclose(collection.trajectories[0].to_linestring().xy, truth_1.xy)
        assert np.allclose(collection.trajectories[1].to_linestring().xy, truth_2.xy)