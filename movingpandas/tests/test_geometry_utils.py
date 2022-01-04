# -*- coding: utf-8 -*-

from math import sqrt
from shapely.geometry import Point
from movingpandas.geometry_utils import (
    azimuth,
    calculate_initial_compass_bearing,
    angular_difference,
    mrr_diagonal,
    measure_distance_geodesic,
)


class TestGeometryUtils:
    def test_compass_bearing_east(self):
        assert calculate_initial_compass_bearing(Point(0, 0), Point(10, 0)) == 90

    def test_compass_bearing_west(self):
        assert calculate_initial_compass_bearing(Point(0, 0), Point(-10, 0)) == 270

    def test_compass_bearing_north(self):
        assert calculate_initial_compass_bearing(Point(0, 0), Point(0, 10)) == 0

    def test_compass_bearing_south(self):
        assert calculate_initial_compass_bearing(Point(0, 0), Point(0, -10)) == 180

    def test_azimuth_east(self):
        assert azimuth(Point(0, 0), Point(1, 0)) == 90
        assert azimuth(Point(0, 0), Point(100, 0)) == 90

    def test_azimuth_west(self):
        assert azimuth(Point(0, 0), Point(-10, 0)) == 270

    def test_azimuth_north(self):
        assert azimuth(Point(0, 0), Point(0, 1)) == 0

    def test_azimuth_south(self):
        assert azimuth(Point(0, 0), Point(0, -1)) == 180

    def test_azimuth_northeast(self):
        assert azimuth(Point(0, 0), Point(1, 1)) == 45

    def test_azimuth_southeast(self):
        assert azimuth(Point(0, 0), Point(1, -1)) == 135

    def test_azimuth_southwest(self):
        assert azimuth(Point(0, 0), Point(-1, -1)) == 225

    def test_azimuth_northwest(self):
        assert azimuth(Point(100, 100), Point(99, 101)) == 315

    def test_anglular_difference_tohigher(self):
        assert angular_difference(1, 5) == 4

    def test_anglular_difference_tolower(self):
        assert angular_difference(355, 5) == 10

    def test_anglular_difference_halfcicle(self):
        assert angular_difference(180, 0) == 180

    def test_anglular_difference_same(self):
        assert angular_difference(45, 45) == 0

    def test_anglular_difference_onenegative(self):
        assert angular_difference(-45, 45) == 90

    def test_anglular_difference_twonegative(self):
        assert angular_difference(-200, -160) == 40

    def test_mrr_diagonal(self):
        assert mrr_diagonal(
            [Point(0, 0), Point(0, 2), Point(2, 0), Point(2, 2)]
        ) == sqrt(8)

    def test_geodesic_distance(self):
        # Distance between NYC, NY USA and Los Angeles, CA USA is
        # 3944411.0951634306 meters
        assert (
            measure_distance_geodesic(
                Point(-74.00597, 40.71427), Point(-118.24368, 34.05223)
            )
            == 3944411.0951634306
        )
