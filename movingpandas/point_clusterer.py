import math
import statistics

from geopandas import GeoDataFrame
from pandas import DataFrame
from shapely.geometry import Point

from movingpandas.geometry_utils import C_EARTH, measure_distance_euclidean


class PointClusterer:
    """
    Clusters points using a grid-based approach. Cluster seeds are a regular
    point grid.

    References
    ----------
    * Andrienko, N., & Andrienko, G. (2011). Spatial generalization and
      aggregation of massive movement data. IEEE Transactions on
      visualization and computer graphics, 17(2), 205-219.
    """

    def __init__(self, points, max_distance, is_latlon):
        df = DataFrame(points, columns=["geometry"])
        bbox = GeoDataFrame(df).total_bounds
        cell_size = max_distance
        if is_latlon:
            cell_size = cell_size / C_EARTH * 360
        self.grid = _Grid(bbox, cell_size)
        self.grid.insert_points(points)
        self.grid.redistribute_points(points)

    def get_clusters(self):
        return self.grid.resulting_clusters


class _PointCluster:
    def __init__(self, pt):
        self.points = [pt]
        self.centroid = pt

    def add_point(self, pt):
        self.points.append(pt)

    def delete_points(self):
        self.points = []

    def recompute_centroid(self):
        x = statistics.fmean(pt.x for pt in self.points)
        y = statistics.fmean(pt.y for pt in self.points)
        self.centroid = Point(x, y)


class _Grid:
    def __init__(self, bbox, cell_size):
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        self.x_min = bbox[0]
        self.y_min = bbox[1]
        self.cell_size = cell_size
        self.cells = []
        # in the rare case that the points are horizontal or vertical,
        # fallback to a 1x1 cell matrix
        self.n_rows = max(1, math.ceil(h / self.cell_size))
        self.n_cols = max(1, math.ceil(w / self.cell_size))
        self.cells = [[None] * self.n_rows for _ in range(self.n_cols)]
        self.resulting_clusters = []

    def insert_points(self, points):
        for pt in points:
            c = self.get_closest_centroid(pt, self.cell_size)
            if not c:
                g = _PointCluster(pt)
                self.resulting_clusters.append(g)
                (i, j) = self.get_grid_position(g.centroid)
                self.cells[i][j] = g
            else:
                (i, j) = c
                g = self.cells[i][j]
                if g:
                    g.add_point(pt)
                    g.recompute_centroid()
                else:
                    print(f"Error: no group in cell {i}, {j}")
                    print(pt)

    def get_group(self, centroid):
        """returns the group with the provided centroid"""
        for g in self.resulting_clusters:
            if g.centroid.compare(centroid):
                return g

    def get_closest_centroid(self, pt, max_dist=100000000):
        (i, j) = self.get_grid_position(pt)
        shortest_dist = self.cell_size * 100
        nearest_centroid = None
        for k in range(max(i - 1, 0), min(i + 2, self.n_cols)):
            for m in range(max(j - 1, 0), min(j + 2, self.n_rows)):
                if not self.cells[k][m]:  # no centroid in this cell yet
                    continue
                dist = measure_distance_euclidean(pt, self.cells[k][m].centroid)
                if dist <= max_dist and dist < shortest_dist:
                    nearest_centroid = (k, m)
                    shortest_dist = dist
        return nearest_centroid

    def get_grid_position(self, pt):
        i = math.floor((pt.x - self.x_min) / self.cell_size)
        j = math.floor((pt.y - self.y_min) / self.cell_size)
        return i, j

    def redistribute_points(self, points):
        for g in self.resulting_clusters:
            g.delete_points()
        for pt in points:
            (i, j) = self.get_closest_centroid(pt, self.cell_size * 20)
            if i is not None and j is not None:
                g = self.cells[i][j]
                g.add_point(pt)
            else:
                print(f"Discarding {pt}")
