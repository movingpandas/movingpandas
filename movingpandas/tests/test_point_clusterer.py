import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point

from movingpandas import PointClusterer


class TestClustering:

    def test_cluster_points(self):
        pts = [Point(0, 0), Point(10, 10), Point(10.2, 10.2)]
        expected = GeoDataFrame(pd.DataFrame([
            {'geometry': Point(0, 0), 'n': 1},
            {'geometry': Point(10.1, 10.1), 'n': 2}]
        ))
        actual = PointClusterer(pts, max_distance=3, is_latlon=False).get_clusters()
        actual = [(c.centroid, len(c.points)) for c in actual]
        expected = [(c.geometry, c.n) for key, c in expected.iterrows()]
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual

    def test_cluster_points2(self):
        pts = [Point(0, 0), Point(6, 0), Point(6, 6), Point(0.2, 0.2), Point(6.2, 0.2), Point(6.2, 6.2)]
        expected = GeoDataFrame(pd.DataFrame([
            {'geometry': Point(0.1, 0.1), 'n': 2},
            {'geometry': Point(6.1, 0.1), 'n': 2},
            {'geometry': Point(6.1, 6.1), 'n': 2}]
        ))
        actual = PointClusterer(pts, max_distance=5, is_latlon=False).get_clusters()
        actual = [(c.centroid, len(c.points)) for c in actual]
        expected = [(c.geometry, c.n) for key, c in expected.iterrows()]
        assert len(actual) == len(expected)
        for pt in expected:
            assert pt in actual