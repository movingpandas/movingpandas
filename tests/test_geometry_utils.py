# -*- coding: utf-8 -*-

"""
ATTENTION!
If you use OSGeo4W, you need to run the following command first:
call C:\OSGeo4W64\bin\py3_env.bat

python3 test_geometry_utils.py -v

or if you want to run all tests at once:

python3 -m unittest discover . -v

"""

import os 
import sys 
import unittest
from shapely.geometry import Point
from movingpandas.geometry_utils import azimuth, calculate_initial_compass_bearing, angular_difference

 
class TestGeometryUtils(unittest.TestCase):
 
    def test_compass_bearing_east(self):
        result = calculate_initial_compass_bearing(Point(0, 0), Point(10, 0))
        expected_result = 90
        self.assertEqual(expected_result, result)
        
    def test_compass_bearing_west(self):
        result = calculate_initial_compass_bearing(Point(0, 0), Point(-10, 0))
        expected_result = 270
        self.assertEqual(expected_result, result)
        
    def test_compass_bearing_north(self):
        result = calculate_initial_compass_bearing(Point(0, 0), Point(0, 10))
        expected_result = 0
        self.assertEqual(expected_result, result)
        
    def test_compass_bearing_south(self):
        result = calculate_initial_compass_bearing(Point(0, 0), Point(0, -10))
        expected_result = 180
        self.assertEqual(expected_result, result)
 
    def test_azimuth_east(self):
        result = azimuth(Point(0, 0), Point(1, 0))
        expected_result = 90
        self.assertEqual(expected_result, result)
         
        result = azimuth(Point(0, 0), Point(100, 0))
        expected_result = 90
        self.assertEqual(expected_result, result)
        
    def test_azimuth_west(self):
        result = azimuth(Point(0, 0), Point(-10, 0))
        expected_result = 270
        self.assertEqual(expected_result, result)
        
    def test_azimuth_north(self):
        result = azimuth(Point(0, 0), Point(0, 1))
        expected_result = 0
        self.assertEqual(expected_result, result)
            
    def test_azimuth_south(self):
        result = azimuth(Point(0, 0), Point(0, -1))
        expected_result = 180
        self.assertEqual(expected_result, result)
 
    def test_azimuth_northeast(self):
        result = azimuth(Point(0, 0), Point(1, 1))
        expected_result = 45
        self.assertEqual(expected_result, result)
        
    def test_azimuth_southeast(self):
        result = azimuth(Point(0, 0), Point(1, -1))
        expected_result = 135
        self.assertEqual(expected_result, result)
        
    def test_azimuth_southwest(self):
        result = azimuth(Point(0, 0), Point(-1, -1))
        expected_result = 225
        self.assertEqual(expected_result, result)
        
    def test_azimuth_northwest(self):
        result = azimuth(Point(100, 100), Point(99, 101))
        expected_result = 315
        self.assertEqual(expected_result, result)
        
    def test_anglular_difference_tohigher(self):
        result = angular_difference(1, 5)
        expected_result = 4
        self.assertEqual(expected_result, result)
        
    def test_anglular_difference_tolower(self):
        result = angular_difference(355, 5)
        expected_result = 10
        self.assertEqual(expected_result, result)
        
    def test_anglular_difference_halfcicle(self):
        result = angular_difference(180, 0)
        expected_result = 180
        self.assertEqual(expected_result, result)
        
    def test_anglular_difference_same(self):
        result = angular_difference(45, 45)
        expected_result = 0
        self.assertEqual(expected_result, result)
        
    def test_anglular_difference_onenegative(self):
        result = angular_difference(-45, 45)
        expected_result = 90
        self.assertEqual(expected_result, result)
        
    def test_anglular_difference_twonegative(self):
        result = angular_difference(-200, -160)
        expected_result = 40
        self.assertEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
