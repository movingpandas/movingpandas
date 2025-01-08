# -*- coding: utf-8 -*-

from collections import Counter

from pandas import DataFrame
from geopandas import GeoDataFrame
from shapely.geometry import LineString
from shapely.ops import nearest_points

from movingpandas.point_clusterer import PointClusterer
from .geometry_utils import (
    azimuth,
    angular_difference,
    measure_distance,
)


class TrajectoryCollectionAggregator:
    def __init__(
        self,
        traj_collection,
        max_distance,
        min_distance,
        min_stop_duration,
        min_angle=45,
    ):
        """
        Aggregates trajectories by extracting significant points,
        clustering those points, and extracting flows between clusters.

        Parameters
        ----------
        traj_collection : TrajectoryCollection
            TrajectoryCollection to be aggregated
        max_distance : float
            Maximum distance between significant points (distance is
            calculated in CRS units, except if the CRS is geographic, e.g.
            EPSG:4326 WGS84, then distance is calculated in meters)
        min_distance : float
            Minimum distance between significant points
        min_stop_duration : datetime.timedelta
            Minimum duration required for stop detection
        min_angle : float
            Minimum angle for significant point extraction

        References
        ----------
        * Andrienko, N., & Andrienko, G. (2011). Spatial generalization and
          aggregation of massive movement data. IEEE Transactions on
          visualization and computer graphics, 17(2), 205-219.
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
        # print('Extracting significant points ...')
        self.significant_points = self._extract_significant_points()
        # print('Clustering significant points ...')
        self.clusters = PointClusterer(
            self.significant_points, self.max_distance, self.is_latlon
        ).get_clusters()
        # print('  No. clusters: {}'.format(len(self.clusters)))
        # print('Computing flows ...')
        self.flows = self._compute_flows_between_clusters()
        # print('Flows ready!')

    def get_significant_points_gdf(self):
        """
        Return the extracted significant points

        Returns
        -------
        GeoDataFrame
            Significant points
        """
        if not self.significant_points:
            self.significant_points = self._extract_significant_points()
        df = DataFrame(self.significant_points, columns=["geometry"])
        return GeoDataFrame(df, crs=self._crs)

    def get_clusters_gdf(self):
        """
        Return the extracted cluster centroids

        Returns
        -------
        GeoDataFrame
            Cluster centroids, incl. the number of clustered significant
            points (n).
        """
        if not self.clusters:
            self.clusters = PointClusterer(
                self.significant_points, self.max_distance, self.is_latlon
            ).get_clusters()
        df = DataFrame(
            [cluster.centroid for cluster in self.clusters],
            columns=["geometry"],
        )
        df["n"] = [len(cluster.points) for cluster in self.clusters]
        return GeoDataFrame(df, crs=self._crs)

    def get_flows_gdf(self):
        """
        Return the extracted flows

        Returns
        -------
        GeoDataFrame
            Flow lines, incl. the number of trajectories summarized in the
            flow (weight) and the number of unique trajectory objects summarized
            in the flow (obj_weight).
        """
        if not self.flows:
            self.flows = self._compute_flows_between_clusters()
        return GeoDataFrame(self.flows, crs=self._crs)

    def _extract_significant_points(self):
        sig_points = []
        for traj in self.traj_collection:
            a = PtsExtractor(
                traj,
                self.max_distance,
                self.min_distance,
                self.min_stop_duration,
                self.min_angle,
            )
            sig_points = sig_points + a.find_significant_points()
        return sig_points

    def _compute_flows_between_clusters(self):
        sg = _SequenceGenerator(self.get_clusters_gdf(), self.traj_collection)
        return sg.create_flow_lines()


class PtsExtractor:
    def __init__(
        self, traj, max_distance, min_distance, min_stop_duration, min_angle=45
    ):
        self.traj = traj
        self.traj_geom = traj.df[traj.get_geom_col()]
        self.n = self.traj.df.geometry.count()
        self.max_distance = max_distance
        self.min_distance = min_distance
        self.min_stop_duration = min_stop_duration
        self.min_angle = min_angle
        self.significant_points = [
            self.traj.get_start_location(),
            self.traj.get_end_location(),
        ]

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
                # print(f"has points (i={i} | j={j} | k={k})")
                if k > j + 1:
                    if self.is_significant_stop(j, k):
                        self.add_point(j)
                        i = j
                        j = k
                        continue
                    # compute the average spatial position to represent
                    # the similar points
                    else:
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
        angle = self.compute_angle_between_vectors(i, j, k)
        return angle >= self.min_angle and angle <= (360 - self.min_angle)

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
        d = measure_distance(pt1, pt2, self.traj.is_latlon)
        return d >= dist

    def get_pt(self, the_loc):
        return self.traj_geom.iloc[the_loc]

    def is_significant_distance(self, i, j):
        if self.distance_greater_than(i, j, self.max_distance):
            self.append_point(self.get_pt(i))
            return True
        return False


class _SequenceGenerator:
    def __init__(self, cells, traj_collection):
        self.cells = cells
        try:
            self.cells_union = cells.geometry.union_all()
        except AttributeError:
            self.cells_union = cells.geometry.unary_union

        self.id_to_centroid = {i: [f, [0, 0, 0, 0, 0]] for i, f in cells.iterrows()}
        self.sequences = Counter()
        self.sequences_obj_log = {}
        for traj in traj_collection:
            self.evaluate_trajectory(traj)

    def evaluate_trajectory(self, trajectory):
        this_sequence = []
        prev_cell_id = None
        geom_name = trajectory.get_geom_col()
        for t, geom in trajectory.df[geom_name].items():
            nearest_id = self.get_nearest(geom)
            nearest_cell = self.id_to_centroid[nearest_id][0]
            nearest_cell_id = nearest_cell.name
            if this_sequence:
                prev_cell_id = this_sequence[-1]
                if nearest_cell_id != prev_cell_id:
                    self.sequences[(prev_cell_id, nearest_cell_id)] += 1
                    if (prev_cell_id, nearest_cell_id) in self.sequences_obj_log.keys():
                        self.sequences_obj_log[(prev_cell_id, nearest_cell_id)].update(
                            [trajectory.obj_id]
                        )
                    else:
                        self.sequences_obj_log[(prev_cell_id, nearest_cell_id)] = set(
                            [trajectory.obj_id]
                        )
            if nearest_cell_id != prev_cell_id:
                # we have changed to a new cell --> up the counter
                h = t.hour
                self.id_to_centroid[nearest_id][1][0] += 1
                self.id_to_centroid[nearest_id][1][h // 6 + 1] += 1
                this_sequence.append(nearest_cell_id)

    def create_flow_lines(self):
        lines = []
        for key, value in self.sequences.items():
            p1 = self.id_to_centroid[key[0]][0].geometry
            p2 = self.id_to_centroid[key[1]][0].geometry
            obj_value = len(self.sequences_obj_log[key])
            lines.append(
                {
                    "geometry": LineString([p1, p2]),
                    "weight": value,
                    "obj_weight": obj_value,
                }
            )
        return lines

    def get_nearest(self, pt):
        nearest = self.cells.geometry.geom_equals(
            nearest_points(pt, self.cells_union)[1]
        )
        return self.cells[nearest].iloc[0].name
