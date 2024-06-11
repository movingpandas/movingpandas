# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from datetime import datetime
from pyproj import CRS
from geopandas import GeoDataFrame
from shapely.geometry import Point
from shapely.wkt import loads

from movingpandas.trajectory_collection import TrajectoryCollection

from .test_trajectory import make_traj, Node
from . import requires_stonesoup

CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestTrajectorySmoother:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0)],
                [1, "A", Point(6, 0), datetime(2018, 1, 1, 12, 6, 0)],
                [1, "A", Point(6, 6), datetime(2018, 1, 1, 14, 10, 0)],
                [1, "A", Point(9, 9), datetime(2018, 1, 1, 14, 15, 0)],
                [2, "A", Point(10, 10), datetime(2018, 1, 1, 12, 0, 0)],
                [2, "A", Point(16, 10), datetime(2018, 1, 1, 12, 6, 0)],
                [2, "A", Point(16, 16), datetime(2018, 1, 2, 13, 10, 0)],
                [2, "A", Point(190, 19), datetime(2018, 1, 2, 13, 15, 0)],
            ],
            columns=["id", "obj", "geometry", "t"],
        ).set_index("t")
        self.df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.df, "id", obj_id_col="obj")

    @requires_stonesoup
    def test_kalman_smoother_cv_single(self):
        from movingpandas.trajectory_smoother import KalmanSmootherCV

        traj = make_traj(
            [
                Node(),
                Node(1, 0.1, second=1),
                Node(2, 0.2, second=2),
                Node(3, 0, second=3),
                Node(3, 3, second=4),
            ]
        )
        result = KalmanSmootherCV(traj).smooth(
            process_noise_std=0.1, measurement_noise_std=10
        )
        truth = loads(
            "LINESTRING ("
            "1.7982884510469304 0.6585353696461531, "
            "1.7986579478436395 0.6588189259897214, "
            "1.7996332413712328 0.6596163790136829, "
            "1.8009712874015955 0.6608076466642573, "
            "1.8024490723366013 0.6622216786861853)"
        )
        assert np.allclose(result.to_linestring().xy, truth.xy)

    @requires_stonesoup
    def test_kalman_smoother_cv_single_tuple(self):
        from movingpandas.trajectory_smoother import KalmanSmootherCV

        traj = make_traj(
            [
                Node(),
                Node(1, 0.1, second=1),
                Node(2, 0.2, second=2),
                Node(3, 0, second=3),
                Node(3, 3, second=4),
            ]
        )
        result = KalmanSmootherCV(traj).smooth(
            process_noise_std=(0.1, 0.1), measurement_noise_std=(10, 10)
        )
        truth = loads(
            "LINESTRING ("
            "1.7982884510469304 0.6585353696461531, "
            "1.7986579478436395 0.6588189259897214, "
            "1.7996332413712328 0.6596163790136829, "
            "1.8009712874015955 0.6608076466642573, "
            "1.8024490723366013 0.6622216786861853)"
        )
        assert np.allclose(result.to_linestring().xy, truth.xy)

    @requires_stonesoup
    def test_kalman_smoother_cv_single_geo(self):
        from movingpandas.trajectory_smoother import KalmanSmootherCV

        traj = make_traj(
            [
                Node(),
                Node(1, 0.1, second=1),
                Node(2, 0.2, second=2),
                Node(3, 0, second=3),
                Node(3, 3, second=4),
            ],
            crs=CRS_LATLON,
        )
        result = KalmanSmootherCV(traj).smooth(
            process_noise_std=0.1, measurement_noise_std=10
        )
        truth = loads(
            "LINESTRING ("
            "1.7982884510469301 0.6587980686797733, "
            "1.7986579478436397 0.6590817401695466, "
            "1.7996332413712322 0.6598795189933684, "
            "1.8009712874015955 0.6610712754609851, "
            "1.8024490723366011 0.6624858873670953)"
        )
        assert np.allclose(result.to_linestring().xy, truth.xy)

    @requires_stonesoup
    def test_kalman_smoother_sv_collection(self):
        from movingpandas.trajectory_smoother import KalmanSmootherCV

        collection = KalmanSmootherCV(self.collection).smooth(
            process_noise_std=0.1, measurement_noise_std=10
        )
        truth_1 = loads(
            "LINESTRING ("
            "0.0044805333934456 0.0000761144223231, "
            "5.9954842501546315 -0.0000845436868686, "
            "6.00040594977978 6.000156500844182, "
            "8.999629266671697 8.999851928420188)"
        )
        truth_2 = loads(
            "LINESTRING ("
            "10.004429320057262 10.000008962523324, "
            "15.995566251010434 9.999990965241574, "
            "16.000875056273347 16.000014621277007, "
            "189.9991293726476 18.99998545095791)"
        )
        assert len(collection) == 2
        assert np.allclose(collection.trajectories[0].to_linestring().xy, truth_1.xy)
        assert np.allclose(collection.trajectories[1].to_linestring().xy, truth_2.xy)
