# -*- coding: utf-8 -*-

import math
from pandas import DataFrame
from geopandas import GeoDataFrame
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

from .geometry_utils import azimuth, angular_difference, measure_distance_spherical, measure_distance_euclidean, R_EARTH


class TrajectoryCollectionAggregator:
    def __init__(self, traj_collection, max_distance, min_distance, min_stop_duration, min_angle=45):
        """
        Create TrajectoryCollectionAggregator

        Parameters
        ----------
        traj_collection : TrajectoryCollection
            TrajectoryCollection to be aggregated
        max_distance : float
            Maximum distance between significant points
        min_distance : float
            Minimum distance between significant points
        min_stop_duration : integer
            Minimum duration required for stop detection (in seconds)
        min_angle : float
            Minimum angle for significant point extraction
        """
        self.traj_collection = traj_collection
        if self.traj_collection.trajectories:
            self._crs = traj_collection.trajectories[0].crs
        else:
            self._crs = None
        self.max_distance = max_distance
        self.min_distance = min_distance
        self.min_stop_duration = min_stop_duration
        self.min_angle = min_angle
        self.is_latlon = self.traj_collection.trajectories[0].is_latlon
        #print('Extracting significant points ...')
        self.significant_points = self._extract_significant_points()
        #print('  No. significant points: {}'.format(len(self.significant_points)))
        #print('Clustering significant points ...')
        self.clusters = _cluster_significant_points(self.significant_points, self.max_distance, self.is_latlon)
        #print('  No. clusters: {}'.format(len(self.clusters)))
        #print('Computing flows ...')
        self.flows = self._compute_flows_between_clusters()
        #print('Flows ready!')

    def get_significant_points_gdf(self):
        """
        Return the extracted significant points

        Returns
        -------
        GeoDataFrame
            Significant points
        """
        if not self.significant_points:
            self._extract_significant_points()
        df = DataFrame(self.significant_points, columns=['geometry'])
        return GeoDataFrame(df, crs=self._crs)

    def get_clusters_gdf(self):
        """
        Return the extracted cluster centroids

        Returns
        -------
        GeoDataFrame
            Cluster centroids, incl. the number of clustered significant points (n)
        """
        if not self.clusters:
            self._cluster_significant_points()
        df = DataFrame([cluster.centroid for cluster in self.clusters], columns=['geometry'])
        df['n'] = [len(cluster.points) for cluster in self.clusters]
        return GeoDataFrame(df, crs=self._crs)

    def get_flows_gdf(self):
        """
        Return the extracted flows

        Returns
        -------
        GeoDataFrame
            Flow lines, incl. the number of trajectories summarized in the flow (weight)
        """
        if not self.flows:
            self._compute_flows_between_clusters()
        return GeoDataFrame(self.flows, crs=self._crs)

    def _extract_significant_points(self):
        significant_points = []
        for traj in self.traj_collection:
            a = _PtsExtractor(traj, self.max_distance, self.min_distance, self.min_stop_duration, self.min_angle)
            significant_points = significant_points + a.find_significant_points()
        return significant_points

    def _compute_flows_between_clusters(self):
        sg = _SequenceGenerator(self.get_clusters_gdf(), self.traj_collection)
        return sg.create_flow_lines()


def _cluster_significant_points(points, max_distance, is_latlon):
    df = DataFrame(points, columns=['geometry'])
    bbox = GeoDataFrame(df).total_bounds
    cell_size = max_distance / 10
    if is_latlon:
        cell_size = cell_size / R_EARTH * 360
    grid = _Grid(bbox, cell_size)
    grid.insert_points(points)
    grid.redistribute_points(points)
    return grid.resulting_clusters


class _PtsExtractor:
    def __init__(self, traj, max_distance, min_distance, min_stop_duration, min_angle=45):
        self.traj = traj
        self.n = self.traj.df.geometry.count()
        self.max_distance = max_distance
        self.min_distance = min_distance
        self.min_stop_duration = min_stop_duration
        self.min_angle = min_angle
        self.significant_points = [self.traj.get_start_location(), self.traj.get_end_location()]

    def find_significant_points(self):
        i = 0
        j = 1
        while j < self.n - 1:
            if self.is_significant_distance(i, j):
                self.add_point(j)
                i = j
                j = i + 1
                continue
            k, has_points = self.locate_points_beyond_min_distance(j)
            if has_points:
                #print(f"has points (i={i} | j={j} | k={k})")
                if k > j + 1:
                    if self.is_significant_stop(j, k):
                        self.add_point(j)
                        i = j
                        j = k
                        continue
                    else:  # compute the average spatial position to represent the similar points
                        m = j + (k - 1 - j) / 2
                        j = int(m)
                if self.is_significant_turn(i, j, k):
                    self.add_point(j)
                    i = j
                    j = k
                else:
                    j += 1
            else:
                return self.significant_points
        return self.significant_points

    def is_significant_turn(self, i, j, k):
        turn_angle = self.compute_angle_between_vectors(i, j, k)
        return turn_angle >= self.min_angle and turn_angle <= (360 - self.min_angle)

    def is_significant_stop(self, j, k):
        delta_t = self.traj.df.iloc[k - 1].name - self.traj.df.iloc[j].name
        return delta_t >= self.min_stop_duration

    def add_point(self, j):
        pt = self.get_pt(j)
        self.append_point(pt)

    def append_point(self, pt):
        if pt != self.traj.get_start_location():
            self.significant_points.append(pt)

    def compute_angle_between_vectors(self, i, j, k):
        p_i = self.get_pt(i)
        p_j = self.get_pt(j)
        p_k = self.get_pt(k)
        azimuth_ij = azimuth(p_i, p_j)
        azimuth_jk = azimuth(p_j, p_k)
        return angular_difference(azimuth_ij, azimuth_jk)

    def locate_points_beyond_min_distance(self, j):
        for k in range(j + 1, self.n):
            if self.distance_greater_than(j, k, self.min_distance):
                return k, True
        return k, False

    def distance_greater_than(self, loc1, loc2, dist):
        pt1 = self.get_pt(loc1)
        pt2 = self.get_pt(loc2)
        if self.traj.is_latlon:
            d = measure_distance_spherical(pt1, pt2)
        else:
            d = measure_distance_euclidean(pt1, pt2)
        return d >= dist

    def get_pt(self, the_loc):
        return self.traj.df.iloc[the_loc][self.traj.get_geom_column_name()]

    def is_significant_distance(self, i, j):
        if self.distance_greater_than(i, j, self.max_distance):
            self.append_point(self.get_pt(i))
            return True
        return False


class _PointCluster:
    def __init__(self, pt):
        self.points = [pt]
        self.centroid = pt

    def add_point(self, pt):
        self.points.append(pt)

    def delete_points(self):
        self.points = []

    def recompute_centroid(self):
        x = [pt.x for pt in self.points]
        y = [pt.y for pt in self.points]
        self.centroid = Point(sum(x) / len(x), sum(y) / len(y))


class _Grid:
    def __init__(self, bbox, cell_size):
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        self.x_min = bbox[0]
        self.y_min = bbox[1]
        self.cell_size = cell_size
        self.cells = []
        self.n_rows = int(math.ceil(h / self.cell_size))
        self.n_cols = int(math.ceil(w / self.cell_size))
        for i in range(0, self.n_cols):
            self.cells.append([])
            for j in range(0, self.n_rows):
                self.cells[i].append(None)
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
                    print("Error: no group in cell {0},{1}".format(i, j))
                    print(pt)

    def get_group(self, centroid):
        """ returns the group with the provided centroid """
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
        i = int(math.floor((pt.x - self.x_min) / self.cell_size))
        j = int(math.floor((pt.y - self.y_min) / self.cell_size))
        return i, j

    def redistribute_points(self, points):
        for g in self.resulting_clusters:
            g.delete_points()
        for pt in points:
            (i, j) = self.get_closest_centroid(pt, self.cell_size * 20)
            if i != None and j != None:
                g = self.cells[i][j]
                g.add_point(pt)
            else:
                print("Discarding {}".format(pt))


class _SequenceGenerator:
    def __init__(self, cells, traj_collection):
        self.cells = cells
        self.id_to_centroid = {i: [f, [0, 0, 0, 0, 0]] for i, f in cells.iterrows()}
        self.sequences = {}
        for traj in traj_collection:
            self.evaluate_trajectory(traj)

    def evaluate_trajectory(self, trajectory):
        this_sequence = []
        prev_cell_id = None
        for t, row in trajectory.df.iterrows():
            nearest_id = self.get_nearest(row[trajectory.get_geom_column_name()])
            nearest_cell = self.id_to_centroid[nearest_id][0]
            nearest_cell_id = nearest_cell.name
            if len(this_sequence) >= 1:
                prev_cell_id = this_sequence[-1]
                if nearest_cell_id != prev_cell_id:
                    if (prev_cell_id, nearest_cell_id) in self.sequences:
                        self.sequences[(prev_cell_id, nearest_cell_id)] += 1
                    else:
                        self.sequences[(prev_cell_id, nearest_cell_id)] = 1
            if nearest_cell_id != prev_cell_id:
                # we have changed to a new cell --> up the counter
                h = t.hour
                self.id_to_centroid[nearest_id][1][0] += 1
                self.id_to_centroid[nearest_id][1][int(h / 6 + 1)] += 1
                this_sequence.append(nearest_cell_id)

    def create_flow_lines(self):
        lines = []
        for key, value in self.sequences.items():
            p1 = self.id_to_centroid[key[0]][0].geometry
            p2 = self.id_to_centroid[key[1]][0].geometry
            lines.append({'geometry': LineString([p1, p2]), 'weight': value})
        return lines


    def get_nearest(self, pt):
        pts = self.cells.geometry.unary_union
        nearest = self.cells.geometry.geom_equals(nearest_points(pt, pts)[1])
        return self.cells[nearest].iloc[0].name

