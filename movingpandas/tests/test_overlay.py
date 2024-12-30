# -*- coding: utf-8 -*-

from pytest import approx
from pandas.testing import assert_frame_equal
from shapely.geometry import Polygon
from datetime import datetime, timedelta
from movingpandas.tests.test_trajectory import Node, make_traj, CRS_METRIC, CRS_LATLON
from movingpandas.overlay import _get_potentially_intersecting_lines


class TestOverlay:
    def setup_method(self):
        self.nodes = [
            Node(0, 0, 1970, 1, 1, 0, 0, 0),
            Node(6, 0, 1970, 1, 1, 0, 0, 6),
            Node(10, 0, 1970, 1, 1, 0, 0, 10),
            Node(10, 10, 1970, 1, 1, 0, 0, 20),
            Node(0, 10, 1970, 1, 1, 0, 0, 30),
        ]
        self.default_traj_metric = make_traj(self.nodes[:3], CRS_METRIC)
        self.default_traj_latlon = make_traj(self.nodes[:3], CRS_LATLON)
        self.default_traj_metric_5 = make_traj(self.nodes, CRS_METRIC)

    def test_clip_one_intersections(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 8), (5, 8), (5, -5)])
        traj = self.default_traj_metric_5
        intersections = traj.clip(polygon)
        assert len(intersections) == 1
        assert intersections.get_trajectory("1_0") == make_traj(
            [Node(5, 0, second=5), Node(6, 0, second=6), Node(7, 0, second=7)],
            id="1_0",
            parent=traj,
        )
        # make sure traj ids are clean and not timestamped:
        assert intersections.get_trajectory("1_0").df.traj_id.unique() == ["1_0"]

    def test_clip_no_node_in_poly(self):
        polygon = Polygon([(1, -5), (2, -5), (2, 8), (1, 8), (1, -5)])
        traj = self.default_traj_metric_5
        intersections = traj.clip(polygon)
        assert len(intersections) == 1
        assert intersections.get_trajectory("1_0") == make_traj(
            [Node(1, 0, second=1), Node(2, 0, second=2)], id="1_0", parent=traj
        )

    def test_get_potentially_intersecting_lines(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 8), (5, 8), (5, -5)])
        traj = self.default_traj_metric_5
        result = _get_potentially_intersecting_lines(traj, polygon)
        assert result.shape[0] == 2
        expected = make_traj(self.nodes[:3])._to_line_df()
        assert_frame_equal(expected, result)

    def test_clip_two_intersections_with_same_polygon(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 12), (5, 12), (5, -5)])
        traj = self.default_traj_metric_5
        intersections = traj.clip(polygon)
        assert len(intersections) == 2
        assert intersections.get_trajectory("1_0") == make_traj(
            [Node(5, 0, second=5), Node(6, 0, second=6), Node(7, 0, second=7)],
            id="1_0",
            parent=traj,
        )
        assert intersections.get_trajectory("1_1") == make_traj(
            [Node(7, 10, second=23), Node(5, 10, second=25)], id="1_1", parent=traj
        )

    def test_clip_with_duplicate_traj_points_does_not_drop_any_points(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 5), (5, 5), (5, -5)])
        traj = make_traj(
            [
                Node(),
                Node(6, 0, second=6),
                Node(6, 0, second=7),
                Node(10, 0, second=11),
                Node(10, 10, second=20),
                Node(0, 10, second=30),
            ]
        )
        intersections = traj.clip(polygon)
        assert len(intersections) == 1
        assert intersections.get_trajectory("1_0") == make_traj(
            [
                Node(5, 0, second=5),
                Node(6, 0, second=6),
                Node(6, 0, second=7),
                Node(7, 0, second=8),
            ],
            id="1_0",
            parent=traj,
        )

    def test_clip_pointbased(self):
        polygon = Polygon([(5.1, -5), (7.5, -5), (7.5, 12), (5.1, 12), (5.1, -5)])
        traj = make_traj(
            [
                Node(),
                Node(6, 0, minute=6),
                Node(6.5, 0, minute=6, second=30),
                Node(7, 0, minute=7),
                Node(10, 0, minute=10),
            ]
        )
        intersections = traj.clip(polygon, point_based=True)
        assert len(intersections) == 1
        assert intersections.get_trajectory("1_0") == make_traj(
            [
                Node(6, 0, minute=6),
                Node(6.5, 0, minute=6, second=30),
                Node(7, 0, minute=7),
            ],
            id="1_0",
            parent=traj,
        )

    def test_clip_pointbased_singlepoint_returns_empty(self):
        polygon = Polygon([(5.1, -5), (6.4, -5), (6.4, 12), (5.1, 12), (5.1, -5)])
        traj = make_traj(
            [
                Node(),
                Node(6, 0, minute=6),
                Node(6.5, 0, minute=6, second=30),
                Node(7, 0, minute=7),
                Node(10, 0, minute=10),
            ]
        )
        intersections = traj.clip(polygon, point_based=True)
        assert len(intersections) == 0

    def test_clip_interpolated_singlepoint(self):
        polygon = Polygon([(5.1, -5), (6.4, -5), (6.4, 12), (5.1, 12), (5.1, -5)])
        traj = make_traj(
            [
                Node(0, 0, minute=5),
                Node(6, 0, minute=6),
                Node(6.5, 0, minute=6, second=30),
            ]
        )
        intersections = traj.clip(polygon, point_based=False)
        assert len(intersections) == 1
        assert intersections.get_trajectory("1_0") == make_traj(
            [
                Node(5.1, 0, minute=5, second=51),
                Node(6, 0, minute=6),
                Node(6.4, 0, minute=6, second=24),
            ],
            id="1_0",
            parent=traj,
        )

    def test_clip_does_not_alter_df(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 12), (5, 12), (5, -5)])
        traj = self.default_traj_metric_5.copy()
        traj.clip(polygon)
        assert_frame_equal(self.default_traj_metric_5.df, traj.df)

    def test_clip_with_one_intersection_reversed(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 5), (5, 5), (5, -5)])
        traj = make_traj([Node(10, 0), Node(6, 0, minute=10), Node(0, 0, minute=20)])
        intersections = traj.clip(polygon)
        assert len(intersections) == 1
        assert intersections.get_trajectory("1_0") == make_traj(
            [
                Node(7, 0, minute=7, second=30),
                Node(6, 0, minute=10),
                Node(5, 0, minute=11, second=40),
            ],
            id="1_0",
            parent=traj,
        )

    def test_clip_with_milliseconds(self):
        polygon = Polygon([(5, -5), (7, -5), (8, 5), (5, 5), (5, -5)])
        traj = make_traj(
            [
                Node(0, 10, hour=12),
                Node(10, 10, hour=12, minute=10),
                Node(10, 0, hour=12, minute=15),
                Node(6, 0, hour=12, minute=30),
                Node(0, 0, hour=13),
            ]
        )
        intersection = traj.clip(polygon).get_trajectory("1_0")
        assert intersection.to_linestring().wkt == "LINESTRING (7.5 0, 6 0, 5 0)"
        assert intersection.get_start_time() - datetime(
            1970, 1, 1, 12, 24, 22, 500000
        ) < timedelta(milliseconds=1)
        assert intersection.get_end_time() == datetime(1970, 1, 1, 12, 35, 0)

    def test_clip_with_numerical_time_issues(self):
        xmin, xmax, ymin, ymax = (
            116.36850352835575,
            116.37029459899574,
            39.904675309969896,
            39.90772814977718,
        )
        polygon = Polygon(
            [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]
        )
        traj = make_traj(
            [
                Node(116.36855, 39.904926, 2009, 3, 10, 11, 3, 35),
                Node(116.368612, 39.904877, 2009, 3, 10, 11, 3, 37),
                Node(116.368644, 39.90484, 2009, 3, 10, 11, 3, 39),
            ]
        )
        result = traj.clip(polygon).get_trajectory("1_0").to_linestring().wkt
        assert (
            result == "LINESTRING (116.36855 39.904926, "
            "116.368612 39.904877, "
            "116.368644 39.90484)"
        )

    def test_clip_with_no_intersection(self):
        polygon = Polygon([(105, -5), (107, -5), (107, 12), (105, 12), (105, -5)])
        intersections = self.default_traj_metric.clip(polygon)
        assert len(intersections) == 0

    def test_intersection_with_feature(self):
        feature = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(5, -5), (7, -5), (8, 5), (5, 5), (5, -5)]],
            },
            "properties": {"id": 1, "name": "foo"},
        }
        intersection = self.default_traj_metric_5.intersection(feature).get_trajectory(
            "1_0"
        )
        assert len(intersection.df.columns) == len(
            ["geometry", "value", "traj_id", "intersecting_id", "intersecting_name"]
        )
        assert intersection.df.iloc[0]["intersecting_id"] == 1
        assert intersection.df.iloc[0]["intersecting_name"] == "foo"

    def test_clip_with_empty_spatial_intersection_linestrings(self):
        polygon = Polygon(
            [
                (-92.98830, 35.38896),
                (-92.35109, 33.96139),
                (-93.27393, 33.61437),
                (-93.99904, 34.88572),
                (-92.98830, 35.38896),
            ]
        )
        traj = make_traj(
            [
                Node(-92.00000, 35.35000, 2020, 8, 5, 21, 33),
                Node(-92.10000, 35.30000, 2020, 8, 5, 21, 34),
                Node(-92.48333, 35.05000, 2020, 8, 5, 21, 38),
                Node(-92.68333, 34.95000, 2020, 8, 5, 21, 40),
                Node(-92.80000, 34.86667, 2020, 8, 5, 21, 41),
                Node(-93.15000, 34.66667, 2020, 8, 5, 21, 44),
                Node(-93.31667, 34.55000, 2020, 8, 5, 21, 45),
                Node(-93.66667, 34.35000, 2020, 8, 5, 21, 48),
                Node(-93.88333, 34.20000, 2020, 8, 5, 21, 50),
                Node(-94.00000, 34.16904, 2020, 8, 5, 21, 51),
            ]
        )
        result = traj.clip(polygon)
        assert len(result) == 1
        coords = result.get_trajectory("1_0").to_linestring().coords
        expected = [
            [-92.76600766934008, 34.89094857130274],
            [-92.8, 34.86667],
            [-93.15000000000001, 34.66667],
            [-93.31667, 34.55],
            [-93.66667, 34.35],
            [-93.68590048921358, 34.33668617473444],
        ]
        assert len(coords) == len(expected)
        for o, e in zip(coords, expected):
            assert o == approx(e, 0.1)
