# -*- coding: utf-8 -*-

import pytest
from datetime import datetime, timedelta
from pytz import timezone

from pyproj import CRS
from numpy import issubdtype

from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_splitter import StopSplitter
from movingpandas.trajectory_stop_detector import TrajectoryStopDetector
from .test_trajectory import Node, make_traj

CRS_METRIC = CRS.from_user_input(31256)
CRS_LATLON = CRS.from_user_input(4326)


class TestTrajectoryStopDetector:
    def setup_method(self):
        self.traj = make_traj(
            [
                Node(0, 0),
                Node(0, 10, second=1),
                Node(0, 20, second=2),
                Node(0, 21, second=4),
                Node(0, 22, second=6),
                Node(0, 30, second=8),
                Node(0, 40, second=10),
                Node(1, 50, second=15),
            ]
        )
        self.detector = TrajectoryStopDetector(self.traj)

    def test_stop_segments_middle_stop(self):
        stop_segments = self.detector.get_stop_segments(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_segments) == 1
        assert (
            stop_segments.trajectories[0].to_linestringm_wkt()
            == "LINESTRING M (0.0 20.0 2.0, 0.0 21.0 4.0, 0.0 22.0 6.0)"
        )
        assert stop_segments.get_crs() == CRS_METRIC

    def test_stop_times_middle_stop(self):
        stop_times = self.detector.get_stop_time_ranges(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_times) == 1
        assert stop_times[0].t_0 == datetime(1970, 1, 1, 0, 0, 2)
        assert stop_times[0].t_n == datetime(1970, 1, 1, 0, 0, 6)

    def test_stop_points_middle_stop(self):
        self.traj.id = "a"
        stop_points = self.detector.get_stop_points(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_points) == 1
        assert stop_points.iloc[0].geometry.x == 0
        assert stop_points.iloc[0].geometry.y == 21
        assert stop_points.iloc[0].start_time == datetime(1970, 1, 1, 0, 0, 2)
        assert stop_points.iloc[0].end_time == datetime(1970, 1, 1, 0, 0, 6)
        assert stop_points.iloc[0].duration_s == 4
        assert stop_points.iloc[0].traj_id == "a"

    def test_stop_point_parent_traj_id(self):
        stop_points = self.detector.get_stop_points(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert stop_points.iloc[0].traj_id == 1
        assert issubdtype(stop_points.iloc[0].traj_id, type(self.traj.id))
        self.traj.id = "a"
        stop_points = self.detector.get_stop_points(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert stop_points.iloc[0].traj_id == "a"
        assert isinstance(stop_points.iloc[0].traj_id, type(self.traj.id))
        self.traj.id = 5.5
        stop_points = self.detector.get_stop_points(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert stop_points.iloc[0].traj_id == 5.5
        assert issubdtype(stop_points.iloc[0].traj_id, type(self.traj.id))

    def test_stop_detector_start_stop(self):
        traj = make_traj(
            [
                Node(0, 0),
                Node(0, 1, second=1),
                Node(0, 2, second=2),
                Node(0, 1, second=3),
                Node(0, 22, second=4),
                Node(0, 30, second=8),
                Node(0, 40, second=10),
                Node(1, 50, second=15),
            ]
        )
        detector = TrajectoryStopDetector(traj)
        stop_times = detector.get_stop_time_ranges(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_times) == 1
        assert stop_times[0].t_0 == datetime(1970, 1, 1, 0, 0, 0)
        assert stop_times[0].t_n == datetime(1970, 1, 1, 0, 0, 3)

    def test_stop_detector_end_stop(self):
        traj = make_traj(
            [
                Node(0, -100),
                Node(0, -10, second=1),
                Node(0, 2, second=2),
                Node(0, 1, second=3),
                Node(0, 22, second=4),
                Node(0, 30, second=8),
                Node(0, 31, second=10),
                Node(1, 32, second=15),
            ]
        )
        detector = TrajectoryStopDetector(traj)
        stop_times = detector.get_stop_time_ranges(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_times) == 1
        assert stop_times[0].t_0 == datetime(1970, 1, 1, 0, 0, 8)
        assert stop_times[0].t_n == datetime(1970, 1, 1, 0, 0, 15)

    def test_stop_detector_multiple_stops(self):
        traj = make_traj(
            [
                Node(0, 0),
                Node(0, 1, second=1),
                Node(0, 2, second=2),
                Node(0, 1, second=3),
                Node(0, 22, second=4),
                Node(0, 30, second=8),
                Node(0, 31, second=10),
                Node(1, 32, second=15),
            ]
        )
        detector = TrajectoryStopDetector(traj)
        stop_times = detector.get_stop_time_ranges(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_times) == 2
        assert stop_times[0].t_0 == datetime(1970, 1, 1, 0, 0, 0)
        assert stop_times[0].t_n == datetime(1970, 1, 1, 0, 0, 3)
        assert stop_times[1].t_0 == datetime(1970, 1, 1, 0, 0, 8)
        assert stop_times[1].t_n == datetime(1970, 1, 1, 0, 0, 15)

    def test_stop_detector_multiple_stops_without_gap(self):
        traj = make_traj(
            [
                Node(0, 0),
                Node(0, 1, second=1),
                Node(0, 2, second=2),
                Node(0, 1, second=3),
                Node(0, 30, second=8),
                Node(0, 31, second=10),
                Node(1, 32, second=15),
            ]
        )
        detector = TrajectoryStopDetector(traj)
        stop_times = detector.get_stop_time_ranges(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_times) == 2
        assert stop_times[0].t_0 == datetime(1970, 1, 1, 0, 0, 0)
        assert stop_times[0].t_n == datetime(1970, 1, 1, 0, 0, 3)
        assert stop_times[1].t_0 == datetime(1970, 1, 1, 0, 0, 8)
        assert stop_times[1].t_n == datetime(1970, 1, 1, 0, 0, 15)

    def test_stop_detector_no_stops(self):
        traj = make_traj(
            [
                Node(0, 0),
                Node(0, 1, second=1),
                Node(0, 2, second=2),
                Node(0, 1, second=3),
                Node(0, 22, second=4),
                Node(0, 30, second=8),
                Node(0, 31, second=10),
                Node(1, 32, second=15),
            ]
        )
        detector = TrajectoryStopDetector(traj)
        stop_times = detector.get_stop_time_ranges(
            max_diameter=1, min_duration=timedelta(seconds=1)
        )
        stop_segments = detector.get_stop_segments(
            max_diameter=1, min_duration=timedelta(seconds=1)
        )
        stop_points = detector.get_stop_points(
            max_diameter=1, min_duration=timedelta(seconds=1)
        )
        assert len(stop_times) == 0
        assert len(stop_segments) == 0
        assert len(stop_points) == 0

    def test_stop_detector_tzaware_data(self):
        nodes = [
            Node(0, 0),
            Node(0, 1, second=1),
            Node(0, 2, second=2),
            Node(0, 1, second=3),
            Node(0, 22, second=4),
            Node(0, 30, second=8),
            Node(0, 31, second=10),
            Node(1, 32, second=15),
        ]

        for node in nodes:
            node.t = timezone("Europe/Vienna").localize(node.t)

        with pytest.warns():
            traj = make_traj(nodes)
        detector = TrajectoryStopDetector(traj)
        stop_times = detector.get_stop_time_ranges(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_times) == 2
        assert stop_times[0].t_0 == datetime(1970, 1, 1, 0, 0, 0)
        assert stop_times[0].t_n == datetime(1970, 1, 1, 0, 0, 3)
        assert stop_times[1].t_0 == datetime(1970, 1, 1, 0, 0, 8)
        assert stop_times[1].t_n == datetime(1970, 1, 1, 0, 0, 15)
        assert traj.df.index.tzinfo is None

    def test_stop_detector_collection(self):
        traj1 = make_traj(
            [
                Node(0, 0),
                Node(0, 1, second=1),
                Node(0, 2, second=2),
                Node(0, 1, second=3),
                Node(0, 22, second=4),
                Node(0, 30, second=8),
                Node(0, 40, second=10),
                Node(1, 50, second=15),
            ],
            id=1,
        )
        traj2 = make_traj(
            [
                Node(0, -100),
                Node(0, -10, second=1),
                Node(0, 2, second=2),
                Node(0, 1, second=3),
                Node(0, 22, second=4),
                Node(0, 30, second=8),
                Node(0, 31, second=10),
                Node(1, 32, second=15),
            ],
            id=2,
        )
        collection = TrajectoryCollection([traj1, traj2])
        detector = TrajectoryStopDetector(collection)
        stop_times = detector.get_stop_time_ranges(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        stop_segments = detector.get_stop_segments(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        stop_points = detector.get_stop_points(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert len(stop_times) == 2
        assert len(stop_segments) == 2
        assert len(stop_points) == 2

    def test_stop_splitter_no_stops(self):
        traj1 = make_traj(
            [
                Node(0, 0),
                Node(0, 10, second=10),
                Node(0, 20, second=20),
                Node(0, 30, second=30),
                Node(0, 40, second=40),
                Node(0, 50, second=50),
            ],
            id=1,
        )
        collection = TrajectoryCollection([traj1])
        detector = StopSplitter(collection)
        stops = detector.split(max_diameter=1, min_duration=timedelta(seconds=1))
        assert len(stops) == 1


class TestTrajectoryStopDetectorWithDeprecations:
    """Test whether deprecations are working as expected."""

    def setup_method(self):
        self.traj = make_traj(
            [
                Node(0, 0),
                Node(0, 10, second=1),
            ]
        )

    def test_deprecation_warning_when_using_n_threads(self):
        """Test to ensure a DeprecationWarning is raised when using `n_threads`."""
        with pytest.deprecated_call():
            TrajectoryStopDetector(traj=self.traj, n_threads=2)

    def test_using_n_threads_and_n_processes_together_gives_error(self):
        """Test whether using both mutually-exclusive arguments raises `ValueError`."""
        with pytest.raises(ValueError):
            TrajectoryStopDetector(traj=self.traj, n_threads=2, n_processes=2)
