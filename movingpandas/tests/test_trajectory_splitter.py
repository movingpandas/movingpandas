# -*- coding: utf-8 -*-

import pandas as pd
from pandas.util.testing import assert_frame_equal
from fiona.crs import from_epsg
from datetime import timedelta, datetime
from geopandas import GeoDataFrame
from shapely.geometry import Point
from .test_trajectory import make_traj, Node
from movingpandas.trajectory_collection import TrajectoryCollection
from movingpandas.trajectory_splitter import (
    TemporalSplitter,
    ObservationGapSplitter,
    SpeedSplitter,
    StopSplitter,
)


CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)


class TestTrajectorySplitter:
    def setup_method(self):
        df = pd.DataFrame(
            [
                [1, "A", Point(0, 0), datetime(2018, 1, 1, 12, 0, 0), 9, "a"],
                [1, "A", Point(6, 0), datetime(2018, 1, 1, 12, 6, 0), 5, "b"],
                [1, "A", Point(6, 6), datetime(2018, 1, 1, 14, 10, 0), 2, "c"],
                [1, "A", Point(9, 9), datetime(2018, 1, 1, 14, 15, 0), 4, "d"],
                [2, "A", Point(10, 10), datetime(2018, 1, 1, 12, 0, 0), 10, "e"],
                [2, "A", Point(16, 10), datetime(2018, 1, 1, 12, 6, 0), 6, "f"],
                [2, "A", Point(16, 16), datetime(2018, 1, 2, 13, 10, 0), 7, "g"],
                [2, "A", Point(190, 19), datetime(2018, 1, 2, 13, 15, 0), 3, "h"],
            ],
            columns=["id", "obj", "geometry", "t", "val", "val2"],
        ).set_index("t")
        self.geo_df = GeoDataFrame(df, crs=CRS_METRIC)
        self.collection = TrajectoryCollection(self.geo_df, "id", obj_id_col="obj")

    def test_split_by_daybreak(self):
        traj = make_traj([Node(), Node(second=1), Node(day=2), Node(day=2, second=1)])
        split = TemporalSplitter(traj).split()
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert split.trajectories[0] == make_traj(
            [Node(), Node(second=1)], id="1_1970-01-01 00:00:00"
        )
        assert split.trajectories[1] == make_traj(
            [Node(day=2), Node(day=2, second=1)], id="1_1970-01-02 00:00:00"
        )

    def test_split_by_date_ignores_single_node_sgements(self):
        traj = make_traj([Node(), Node(second=1), Node(day=2)])
        split = TemporalSplitter(traj).split()
        assert type(split) == TrajectoryCollection
        assert len(split) == 1
        assert split.trajectories[0] == make_traj(
            [Node(), Node(second=1)], id="1_1970-01-01 00:00:00"
        )

    def test_split_by_daybreak_same_day_of_year(self):
        traj = make_traj(
            [Node(), Node(second=1), Node(year=2000), Node(year=2000, second=1)]
        )
        split = TemporalSplitter(traj).split()
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert split.trajectories[0] == make_traj(
            [Node(), Node(second=1)], id="1_1970-01-01 00:00:00"
        )
        assert split.trajectories[1] == make_traj(
            [Node(year=2000), Node(year=2000, second=1)], id="1_2000-01-01 00:00:00"
        )

    def test_split_by_hour(self):
        traj = make_traj([Node(), Node(second=1), Node(hour=1), Node(hour=1, second=1)])
        split = TemporalSplitter(traj).split(mode="hour")
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert split.trajectories[0] == make_traj(
            [Node(), Node(second=1)], id="1_1970-01-01 00:00:00"
        )
        assert split.trajectories[1] == make_traj(
            [Node(hour=1), Node(hour=1, second=1)], id="1_1970-01-01 01:00:00"
        )

    def test_split_by_2H(self):
        traj = make_traj([Node(), Node(second=1), Node(hour=2), Node(hour=2, second=1)])
        split = TemporalSplitter(traj).split(mode="2H")
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert split.trajectories[0] == make_traj(
            [Node(), Node(second=1)], id="1_1970-01-01 00:00:00"
        )
        assert split.trajectories[1] == make_traj(
            [Node(hour=2), Node(hour=2, second=1)], id="1_1970-01-01 02:00:00"
        )

    def test_split_by_month(self):
        traj = make_traj(
            [
                Node(),
                Node(second=1),
                Node(day=2),
                Node(day=2, second=1),
                Node(month=2),
                Node(month=2, second=1),
            ]
        )
        split = TemporalSplitter(traj).split(mode="month")
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert split.trajectories[0] == make_traj(
            [Node(), Node(second=1), Node(day=2), Node(day=2, second=1)],
            id="1_1970-01-31 00:00:00",
        )
        assert split.trajectories[1] == make_traj(
            [Node(month=2), Node(month=2, second=1)], id="1_1970-02-28 00:00:00"
        )

    def test_split_by_year(self):
        traj = make_traj(
            [
                Node(),
                Node(second=1),
                Node(day=2),
                Node(day=2, second=1),
                Node(year=2000),
                Node(year=2000, second=1),
            ]
        )
        split = TemporalSplitter(traj).split(mode="year")
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert split.trajectories[0] == make_traj(
            [Node(), Node(second=1), Node(day=2), Node(day=2, second=1)],
            id="1_1970-12-31 00:00:00",
        )
        assert split.trajectories[1] == make_traj(
            [Node(year=2000), Node(year=2000, second=1)], id="1_2000-12-31 00:00:00"
        )

    def test_split_by_observation_gap(self):
        traj = make_traj([Node(), Node(minute=1), Node(minute=5), Node(minute=6)])
        split = ObservationGapSplitter(traj).split(gap=timedelta(seconds=120))
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert split.trajectories[0] == make_traj([Node(), Node(minute=1)], id="1_0")
        assert split.trajectories[1] == make_traj(
            [Node(minute=5), Node(minute=6)], id="1_1"
        )

    def test_split_by_observation_gap_skip_single_points(self):
        traj = make_traj([Node(), Node(minute=1), Node(minute=5), Node(minute=7)])
        split = ObservationGapSplitter(traj).split(gap=timedelta(seconds=61))
        assert type(split) == TrajectoryCollection
        assert len(split) == 1
        assert split.trajectories[0] == make_traj([Node(), Node(minute=1)], id="1_0")

    def test_splitbyobservationgap_does_not_alter_df(self):
        traj = make_traj([Node(), Node(minute=1), Node(minute=5), Node(minute=7)])
        traj_copy = traj.copy()
        ObservationGapSplitter(traj).split(gap=timedelta(minutes=5))  # noqa: F841
        assert_frame_equal(traj.df, traj_copy.df)

    def test_speed_splitter(self):
        traj = make_traj(
            [
                Node(0, 0),
                Node(0, 10, second=1),
                Node(0, 20, second=2),
                Node(0, 21, second=3),
                Node(0, 22, second=4),
                Node(0, 30, second=5),
                Node(0, 40, second=6),
            ]
        )
        traj_copy = traj.copy()
        split = SpeedSplitter(traj).split(speed=5, duration=timedelta(seconds=2))
        assert_frame_equal(traj.df, traj_copy.df)
        assert type(split) == TrajectoryCollection
        assert len(split) == 2

    def test_speed_splitter_max_speed(self):
        traj = make_traj(
            [
                Node(0, 0),
                Node(0, 2, second=1),
                Node(0, 12, second=2),
                Node(0, 22, second=3),
                Node(0, 24, second=4),
                Node(0, 26, second=5),
                Node(0, 27, second=6),
                Node(0, 28, second=7),
                Node(0, 30, second=8),
                Node(0, 32, second=9),
            ]
        )
        traj_copy = traj.copy()
        split = SpeedSplitter(traj).split(
            speed=2, duration=timedelta(seconds=2), max_speed=8
        )
        assert_frame_equal(traj.df, traj_copy.df)
        assert type(split) == TrajectoryCollection
        assert len(split) == 3

    def test_stop_splitter(self):
        traj = make_traj(
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
        traj_copy = traj.copy()
        split = StopSplitter(traj).split(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert_frame_equal(traj.df, traj_copy.df)
        assert type(split) == TrajectoryCollection
        assert len(split) == 2
        assert (
            split.trajectories[0].to_linestring().wkt == "LINESTRING (0 0, 0 10, 0 20)"
        )
        assert (
            split.trajectories[1].to_linestring().wkt
            == "LINESTRING (0 22, 0 30, 0 40, 1 50)"
        )

    def test_stop_splitter_min_length(self):
        traj = make_traj(
            [
                Node(0, 0),
                Node(0, 10, second=1),
                Node(0, 20, second=2),
                Node(0, 21, second=4),
                Node(0, 22, second=6),
                Node(0, 30, second=8),
                Node(0, 40, second=10),
                Node(1, 100, second=15),
            ]
        )
        traj_copy = traj.copy()
        split = StopSplitter(traj).split(
            max_diameter=3, min_duration=timedelta(seconds=2), min_length=25
        )
        assert_frame_equal(traj.df, traj_copy.df)
        assert type(split) == TrajectoryCollection
        assert len(split) == 1
        assert (
            split.trajectories[0].to_linestring().wkt
            == "LINESTRING (0 22, 0 30, 0 40, 1 100)"
        )

    def test_collection_split_by_date(self):
        split = TemporalSplitter(self.collection).split(mode="day")
        assert type(split) == TrajectoryCollection
        assert len(split) == 3

    def test_collection_split_by_observation_gap(self):
        split = ObservationGapSplitter(self.collection).split(gap=timedelta(hours=1))
        assert type(split) == TrajectoryCollection
        assert len(split) == 4

    def test_stop_splitter_stop_at_start(self):
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
        traj_copy = traj.copy()
        split = StopSplitter(traj).split(
            max_diameter=3, min_duration=timedelta(seconds=2)
        )
        assert_frame_equal(traj.df, traj_copy.df)
        assert type(split) == TrajectoryCollection
        assert len(split) == 1
        assert (
            split.trajectories[0].to_linestring().wkt
            == "LINESTRING (0 1, 0 22, 0 30, 0 40, 1 50)"
        )
