# -*- coding: utf-8 -*-

"""
ATTENTION!
If you use OSGeo4W, you need to run the following command first:
call C:\OSGeo4W64\bin\py3_env.bat

python3 test_trajectory.py -v

or if you want to run all tests at once:

python3 -m unittest discover . -v

"""

import os
import sys
import unittest
import pandas as pd
from pandas.util.testing import assert_frame_equal
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import datetime, timedelta
from fiona.crs import from_epsg
from movingpandas.trajectory import Trajectory, DIRECTION_COL_NAME, SPEED_COL_NAME


CRS_METRIC = from_epsg(31256)
CRS_LATLON = from_epsg(4326)


class Node:
    def __init__(self, x=0, y=0, year=1970, month=1, day=1, hour=0, minute=0, second=0, millisec=0, value=0):
        self.geometry = Point(x, y)
        self.t = datetime(year, month, day, hour, minute, second, millisec)
        self.value = value

    def to_dict(self):
        return {'geometry': self.geometry, 't': self.t, 'value': self.value}


def make_trajectory(nodes, crs=CRS_METRIC, id=1, parent=None):
    nodes = [node.to_dict() for node in nodes]
    df = pd.DataFrame(nodes).set_index('t')
    geo_df = GeoDataFrame(df, crs=crs)
    return Trajectory(id, geo_df, parent=parent)


class TestTrajectory(unittest.TestCase):
    def setUp(self):
        nodes = [
            Node( 0,  0, 1970, 1, 1, 0, 0,  0, 0, 1),
            Node( 6,  0, 1970, 1, 1, 0, 0, 10, 0, 2),
            Node(10,  0, 1970, 1, 1, 0, 0, 20, 0, 3),
            Node(10, 10, 1970, 1, 1, 0, 0, 30, 0, 4),
            Node( 0, 10, 1970, 1, 1, 0, 0, 40, 0, 5)
        ]
        self.default_traj_metric = make_trajectory(nodes[:3], CRS_METRIC)
        self.default_traj_latlon = make_trajectory(nodes[:3], CRS_LATLON)
        self.default_traj_metric_5 = make_trajectory(nodes, CRS_METRIC)

    def test_endlocation(self):
        result = self.default_traj_metric.get_end_location()
        expected = Point(10, 0)
        self.assertEqual(expected, result)

    def test_write_linestring_wkt(self):
        result = self.default_traj_metric.to_linestring().wkt
        expected = "LINESTRING (0 0, 6 0, 10 0)"
        self.assertEqual(expected, result)

    def test_write_linstring_m_wkt_with_unix_time(self):
        result = self.default_traj_metric.to_linestringm_wkt()
        expected = "LINESTRING M (0.0 0.0 0.0, 6.0 0.0 10.0, 10.0 0.0 20.0)"
        self.assertEqual(expected, result)

    def test_get_position_at_existing_timestamp(self):
        result = self.default_traj_metric.get_position_at(datetime(1970, 1, 1, 0, 0, 10), method='nearest')
        expected = Point(6, 0)
        self.assertEqual(expected, result)

    def test_get_position_with_invalid_method(self):
        with self.assertRaises(ValueError):
            self.default_traj_metric.get_position_at(datetime(1970, 1, 1, 0, 0, 10), method='xxx')

    def test_get_interpolated_position_at_existing_timestamp(self):
        result = self.default_traj_metric.get_position_at(datetime(1970, 1, 1, 0, 0, 10), method='interpolated')
        expected = Point(6, 0)
        self.assertEqual(expected, result)

    # TODO: If possible use parameterized tests here ...
    def test_get_position_of_nearest_timestamp_1(self):
        result = self.default_traj_metric.get_position_at(datetime(1970, 1, 1, 0, 0, 9), method='nearest')
        expected = Point(6, 0)
        self.assertEqual(expected, result)

    def test_get_position_of_nearest_timestamp_2(self):
        result = self.default_traj_metric.get_position_at(datetime(1970, 1, 1, 0, 0, 15), method='nearest')
        expected = Point(10, 0)
        self.assertEqual(expected, result)

    def test_get_position_interpolated_at_timestamp_1(self):
        result = self.default_traj_metric.get_position_at(datetime(1970, 1, 1, 0, 0, 14), method="interpolated")
        expected = Point(6 + 4 / 10 * 4, 0)
        self.assertEqual(expected, result)

    def test_get_position_interpolated_at_timestamp_2(self):
        result = self.default_traj_metric.get_position_at(datetime(1970, 1, 1, 0, 0, 15), method="interpolated")
        expected = Point(6 + 4 / 10 * 5, 0)
        self.assertEqual(expected, result)

    def test_get_segment_between_existing_timestamps(self):
        result = self.default_traj_metric_5\
            .get_segment_between(datetime(1970, 1, 1, 0, 0, 10), datetime(1970, 1, 1, 0, 0, 30))
        expected = make_trajectory([Node(6, 0, second=10), Node(10, 0, second=20),  Node(10, 10, second=30)], parent=self.default_traj_metric_5)
        self.assertEqual(expected, result)
        expected = make_trajectory([Node(6, 0, second=10), Node(10, 0, second=20), Node(10, 10, second=40)], parent=self.default_traj_metric_5)
        self.assertNotEqual(expected, result)

    def test_get_segment_between_new_timestamps(self):
        result = self.default_traj_metric_5\
            .get_segment_between(datetime(1970, 1, 1, 0, 0, 5), datetime(1970, 1, 1, 0, 0, 25))
        expected = make_trajectory([Node(6, 0, second=10), Node(10, 0, second=20)], parent=self.default_traj_metric_5)
        self.assertEqual(expected, result)

    def test_get_linestring_between_interpolate(self):
        result = self.default_traj_metric_5\
            .get_linestring_between(datetime(1970, 1, 1, 0, 0, 5), datetime(1970, 1, 1, 0, 0, 25), method='interpolated').wkt
        expected = "LINESTRING (3 0, 6 0, 10 0, 10 5)"
        self.assertEqual(expected, result)

    def test_get_linestring_between_within(self):
        result = self.default_traj_metric_5\
            .get_linestring_between(datetime(1970, 1, 1, 0, 0, 5), datetime(1970, 1, 1, 0, 0, 25), method='within').wkt
        expected = "LINESTRING (6 0, 10 0)"
        self.assertEqual(expected, result)

    def test_add_direction(self):
        traj = make_trajectory([Node(0, 0), Node(6, 0, day=2), Node(6, -6, day=3), Node(-6, -6, day=4)])
        traj.add_direction()
        result = traj.df[DIRECTION_COL_NAME].tolist()
        expected = [90.0, 90.0, 180.0, 270]
        self.assertEqual(expected, result)

    def test_add_direction_latlon(self):
        traj = make_trajectory([Node(0, 0), Node(10, 10, day=2)], CRS_LATLON)
        traj.add_direction()
        result = traj.df[DIRECTION_COL_NAME].tolist()
        expected = [44.561451413257714, 44.561451413257714]
        self.assertAlmostEqual(expected[0], result[0], 5)

    def test_add_speed(self):
        traj = make_trajectory([Node(0, 0), Node(6, 0, second=1)])
        traj.add_speed()
        result = traj.df[SPEED_COL_NAME].tolist()
        expected = [6.0, 6.0]
        self.assertEqual(expected, result)

    def test_add_speed_latlon(self):
        traj = make_trajectory([Node(0, 1), Node(6, 0, second=1)], CRS_LATLON)
        traj.add_speed()
        result = traj.df[SPEED_COL_NAME].tolist()[0] / 1000
        expected = 676.3
        self.assertAlmostEqual(expected, result, 1)

    def test_get_bbox(self):
        result = make_trajectory([Node(0, 1), Node(6, 5, day=2)], CRS_LATLON).get_bbox()
        expected = (0, 1, 6, 5)  # (minx, miny, maxx, maxy)
        self.assertEqual(expected, result)

    def test_get_length_spherical(self):
        result = make_trajectory([Node(0, 1), Node(6, 0, day=2)], CRS_LATLON).get_length() / 1000
        expected = 676.3
        self.assertAlmostEqual(expected, result, 1)

    def test_get_length_euclidiean(self):
        result = make_trajectory([Node(0, 2), Node(6, 0, day=2)]).get_length()
        expected = 6.3
        self.assertAlmostEqual(expected, result, 1)

    def test_get_direction(self):
        result = make_trajectory([Node(0, 0), Node(-6, 10, day=1), Node(6, 6, day=2)]).get_direction()
        expected = 45
        self.assertAlmostEqual(expected, result, 1)

    def test_split_by_daybreak(self):
        split = make_trajectory([Node(), Node(second=1), Node(day=2), Node(day=2, second=1)]).split_by_date()
        self.assertEqual(2, len(split))
        self.assertEqual(make_trajectory([Node(), Node(second=1)], id='1_0'), split[0])
        self.assertEqual(make_trajectory([Node(day=2), Node(day=2, second=1)], id='1_1'), split[1])

    def test_split_by_daybreak_same_day_of_year(self):
        split = make_trajectory([Node(), Node(second=1), Node(year=2000), Node(year=2000, second=1)]).split_by_date()
        self.assertEqual(2, len(split))
        self.assertEqual(make_trajectory([Node(), Node(second=1)], id='1_0'), split[0])
        self.assertEqual(make_trajectory([Node(year=2000), Node(year=2000, second=1)], id='1_1'), split[1])

    def test_split_by_observation_gap(self):
        split = make_trajectory([Node(), Node(minute=1), Node(minute=5), Node(minute=6)])\
            .split_by_observation_gap(timedelta(seconds=120))
        self.assertEqual(2, len(split))
        self.assertEqual(make_trajectory([Node(), Node(minute=1)], id='1_0'), split[0])
        self.assertEqual(make_trajectory([Node(minute=5), Node(minute=6)], id='1_1'), split[1])

    def test_split_by_observation_gap_skip_single_points(self):
        split = make_trajectory([Node(), Node(minute=1), Node(minute=5), Node(minute=7)])\
            .split_by_observation_gap(timedelta(seconds=61))
        self.assertEqual(1, len(split))
        self.assertEqual(make_trajectory([Node(), Node(minute=1)], id='1_0'), split[0])

    def test_offset_seconds(self):
        traj = self.default_traj_metric_5
        traj.apply_offset_seconds('value', -20)
        self.assertEqual(5, traj.df.iloc[2].value)
        self.assertEqual(Point(10, 0), traj.df.iloc[2].geometry)

    def test_offset_minutes(self):
        traj = make_trajectory([Node(), Node(6, 0, minute=1, value=1), Node(10, 0, minute=2, value=2)])
        traj.apply_offset_minutes('value', -2)
        self.assertEqual(2, traj.df.iloc[0].value)
        self.assertEqual(Point(0, 0), traj.df.iloc[0].geometry)

    def test_nonchronological_input(self):
        traj = make_trajectory([Node(0, 0, day=3), Node(1, 1, day=2), Node(2, 2, day=1)])
        self.assertEqual(datetime(1970, 1, 1), traj.get_start_time())
        self.assertEqual(datetime(1970, 1, 3), traj.get_end_time())
        self.assertEqual(Point(2, 2), traj.get_start_location())

    def test_douglas_peucker(self):
        traj = make_trajectory([Node(), Node(1, 0.1, day=1), Node(2, 0.2, day=2), Node(3, 0, day=3), Node(3, 3, day=4)])
        result = traj.generalize(mode='douglas-peucker', tolerance=1)
        expected = make_trajectory([Node(), Node(3, 0, day=3), Node(3, 3, day=4)])
        self.assertEqual(expected, result)

    def test_generalize_min_time_delta(self):
        traj = make_trajectory([Node(), Node(1, 0.1, minute=6), Node(2, 0.2, minute=10), Node(3, 0, minute=30), Node(3, 3, minute=59)])
        result = traj.generalize(mode='min-time-delta', tolerance=timedelta(minutes=10))
        expected = make_trajectory([Node(), Node(2, 0.2, minute=10), Node(3, 0, minute=30), Node(3, 3, minute=59)])
        self.assertEqual(expected, result)

    def test_plot_exists(self):
        from matplotlib.axes import Axes
        result = self.default_traj_metric.plot()
        self.assertIsInstance(result, Axes)

    def test_tolinestring_does_not_alter_df(self):
        traj = self.default_traj_metric
        expected = traj.df.copy()
        traj.to_linestring()
        assert_frame_equal(expected, traj.df)

    def test_getlength_does_not_alter_df(self):
        traj = self.default_traj_metric
        expected = traj.df.copy()
        traj.get_length()
        assert_frame_equal(expected, traj.df)

    def test_str_does_not_alter_df(self):
        traj = self.default_traj_metric
        expected = traj.df.copy()
        str(traj)
        assert_frame_equal(expected, traj.df)

    def test_plot_does_not_alter_df(self):
        traj = self.default_traj_metric
        expected = traj.df.copy()
        traj.plot(column='speed')
        assert_frame_equal(expected, traj.df)

    def test_splitbyobservationgap_does_not_alter_df(self):
        traj = self.default_traj_metric
        expected = traj.df.copy()
        traj.split_by_observation_gap(timedelta(minutes=5))
        assert_frame_equal(expected, traj.df)

    def test_linestringbetween_does_not_alter_df(self):
        traj = self.default_traj_metric
        expected = traj.df.copy()
        traj.get_linestring_between(datetime(1970, 1, 1, 0, 0, 1), datetime(1970, 1, 1, 0, 0, 3))
        assert_frame_equal(expected, traj.df)

    def test_getpositionat_does_not_alter_df(self):
        traj = self.default_traj_metric
        expected = traj.df.copy()
        traj.get_position_at(datetime(1970, 1, 1, 0, 0, 2), method="nearest")
        assert_frame_equal(expected, traj.df)

    """ 
    This test should work but fails in my PyCharm probably due to https://github.com/pyproj4/pyproj/issues/134
    def test_crs(self):
        df = pd.DataFrame([
            {'geometry': Point(0, 0), 't': datetime(2018, 1, 1, 12, 0, 0)},
            {'geometry': Point(6, 0), 't': datetime(2018, 1, 1, 12, 6, 0)},
            {'geometry': Point(10, 0), 't': datetime(2018, 1, 1, 12, 10, 0)}
            ]).set_index('t')
        geo_df = GeoDataFrame(df, crs=from_epsg(4326))
        traj = Trajectory(1, geo_df)
        new_df = traj.df.to_crs(epsg=3857)
        self.assertEqual(new_df.crs, from_epsg(3857))
    """


if __name__ == '__main__':
    unittest.main()
