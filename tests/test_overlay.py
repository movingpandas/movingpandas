# -*- coding: utf-8 -*-

import pytest
from pandas.util.testing import assert_frame_equal
from shapely.geometry import Point, LineString, Polygon
from datetime import datetime, timedelta
from tests.test_trajectory import Node, make_traj, CRS_METRIC, CRS_LATLON

 
class TestOverlay:

    def setup_method(self):
        nodes = [
            Node( 0,  0, 1970, 1, 1, 0, 0,  0),
            Node( 6,  0, 1970, 1, 1, 0, 0,  6),
            Node(10,  0, 1970, 1, 1, 0, 0, 10),
            Node(10, 10, 1970, 1, 1, 0, 0, 20),
            Node( 0, 10, 1970, 1, 1, 0, 0, 30)
        ]
        self.default_traj_metric = make_traj(nodes[:3], CRS_METRIC)
        self.default_traj_latlon = make_traj(nodes[:3], CRS_LATLON)
        self.default_traj_metric_5 = make_traj(nodes, CRS_METRIC)
         
    def test_clip_two_intersections_with_same_polygon(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 12), (5, 12), (5, -5)])
        traj = self.default_traj_metric_5
        intersections = traj.clip(polygon)
        assert len(intersections) == 2
        assert intersections[0] == \
               make_traj([Node(5, 0, second=5), Node(6, 0, second=6), Node(7, 0, second=7)], id='1_0', parent=traj)
        assert intersections[1] == \
               make_traj([Node(7, 10, second=23), Node(5, 10, second=25)], id='1_1', parent=traj)
                
    def test_clip_with_duplicate_traj_points_does_not_drop_any_points(self):
        polygon = Polygon([(5, -5), (7, -5), (7, 5), (5, 5), (5, -5)])
        traj = make_traj([Node(), Node(6, 0, second=6), Node(6, 0, second=7), Node(10, 0, second=11),
                          Node(10, 10, second=20), Node(0, 10, second=30)])
        intersections = traj.clip(polygon)
        assert len(intersections) == 1
        assert intersections[0] == \
               make_traj([Node(5, 0, second=5), Node(6, 0, second=6), Node(6, 0, second=7), Node(7, 0, second=8)], id='1_0', parent=traj)

    def test_clip_pointbased(self):
        polygon = Polygon([(5.1, -5), (7.5, -5), (7.5, 12), (5.1, 12), (5.1, -5)])
        traj = make_traj([Node(), Node(6, 0, minute=6), Node(6.5, 0, minute=6, second=30), Node(7, 0, minute=7),
                          Node(10, 0, minute=10)])
        intersections = traj.clip(polygon, pointbased=True)
        assert len(intersections) == 1
        assert intersections[0] == \
               make_traj([Node(6, 0, minute=6), Node(6.5, 0, minute=6, second=30), Node(7, 0, minute=7)], id='1_0', parent=traj)

    def test_clip_pointbased_singlepoint_returns_empty(self):
        polygon = Polygon([(5.1, -5), (6.4, -5), (6.4, 12), (5.1, 12), (5.1, -5)])
        traj = make_traj([Node(), Node(6, 0, minute=6), Node(6.5, 0, minute=6, second=30), Node(7, 0, minute=7),
                          Node(10, 0, minute=10)])
        assert traj.clip(polygon, pointbased=True) == []

    def test_clip_interpolated_singlepoint(self):
        polygon = Polygon([(5.1, -5), (6.4, -5), (6.4, 12), (5.1, 12), (5.1, -5)])
        traj = make_traj([Node(0, 0, minute=5), Node(6, 0, minute=6), Node(6.5, 0, minute=6, second=30)])
        intersections = traj.clip(polygon, pointbased=False)
        assert len(intersections) == 1
        assert intersections[0] == \
               make_traj([Node(5.1, 0, minute=5, second=51), Node(6, 0, minute=6), Node(6.4, 0, minute=6, second=24)], id='1_0', parent=traj)

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
        assert intersections[0] == \
               make_traj([Node(7, 0, minute=7, second=30), Node(6, 0, minute=10), Node(5, 0, minute=11, second=40)], id='1_0', parent=traj)
         
    def test_clip_with_milliseconds(self):
        polygon = Polygon([(5, -5), (7, -5), (8, 5), (5, 5), (5, -5)])
        traj = make_traj([Node(0, 10, hour=12), Node(10, 10, hour=12, minute=10), Node(10, 0, hour=12, minute=15),
                          Node(6, 0, hour=12, minute=30), Node(0, 0, hour=13)])
        intersection = traj.clip(polygon)[0]
        assert intersection.to_linestring().wkt == "LINESTRING (7.5 0, 6 0, 5 0)"
        assert intersection.get_start_time() - datetime(1970, 1, 1, 12, 24, 22, 500000) < timedelta(milliseconds=1)
        assert intersection.get_end_time() == datetime(1970, 1, 1, 12, 35, 0)
         
    def test_clip_with_numerical_time_issues(self):     
        xmin, xmax, ymin, ymax = 116.36850352835575, 116.37029459899574, 39.904675309969896, 39.90772814977718
        polygon = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)])
        traj = make_traj([Node(116.36855, 39.904926, 2009, 3, 10, 11, 3, 35),
                          Node(116.368612, 39.904877, 2009, 3, 10, 11, 3, 37),
                          Node(116.368644, 39.90484, 2009, 3, 10, 11, 3, 39)])
        result = traj.clip(polygon)[0].to_linestring().wkt
        assert result == "LINESTRING (116.36855 39.904926, 116.368612 39.904877, 116.368644 39.90484)"
         
    def test_clip_with_no_intersection(self):
        polygon = Polygon([(105, -5), (107, -5), (107, 12), (105, 12), (105, -5)])
        assert self.default_traj_metric.clip(polygon) == []
        
    def test_intersection_with_one_intersection(self):
        feature = {
            'geometry': {'type': 'Polygon', 'coordinates': [[(5, -5), (7, -5), (8, 5), (5, 5), (5, -5)]]},
            'properties': {'id': 1, 'name': 'foo'}}
        intersections = self.default_traj_metric_5.intersection(feature)
        assert len(intersections[0].df.columns) == len(['geometry', 'value', 'intersecting_id', 'intersecting_name'])
        assert intersections[0].df.iloc[0]['intersecting_id'] == 1
        assert intersections[0].df.iloc[0]['intersecting_name'] == 'foo'
