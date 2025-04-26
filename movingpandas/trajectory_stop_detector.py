# -*- coding: utf-8 -*-
import warnings

from geopy import distance
from math import hypot
from multiprocessing import Pool
from itertools import repeat
from geopandas import GeoDataFrame
from shapely.geometry import MultiPoint, Point
from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import mrr_diagonal
from .trajectory_utils import convert_time_ranges_to_segments
from .spatiotemporal_utils import TRangeWithTrajId


class TrajectoryStopDetector:
    """
    Detects stops in a trajectory.
    A stop is detected if the movement stays within an area of specified size for
    at least the specified duration.
    """

    def __init__(self, traj, n_processes=1, **kwargs):
        """
        Create a StopDetector.

        Parameters
        ----------
        traj : Trajectory or TrajectoryCollection
            The trajectory or collection of trajectories to analyze.

        n_processes : int or None, optional
            Number of processes to use for computation (default: 1). If set to `None`,
            the number of processes will be set to `os.cpu_count()`
            (or `os.process_cpu_count()` in Python 3.13+), enabling full CPU
            utilization via multiprocessing.

        n_threads : int, optional
            DEPRECATED. Use `n_processes` instead. This parameter will be
            removed in a future version.

        Raises
        ------
        ValueError
            If both `n_processes` and the deprecated `n_threads` are provided.
        """
        n_threads = kwargs.pop("n_threads", None)

        if n_threads is not None and n_processes != 1:
            raise ValueError(
                "You cannot pass both `n_threads` (deprecated) and `n_processes`. "
                "Please use only `n_processes`."
            )

        if n_threads is not None:
            warnings.warn(
                "`n_threads` is deprecated and will be removed in a future version. "
                "Please use `n_processes` instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            n_processes = n_threads

        self.traj = traj
        self.n_processes = n_processes

    def get_stop_time_ranges(self, max_diameter, min_duration):
        """
        Returns detected stop start and end times.

        Parameters
        ----------
        max_diameter : float
            Maximum diameter for stop detection. (Distances will be calculated
            in meters using geodesic distance calculations for geographic projections
            (e.g. EPSG:4326 WGS84) and in CRS units for all other projections)
        min_duration : datetime.timedelta
            Minimum stop duration

        Returns
        -------
        list
            TemporalRanges of detected stops
        """
        if isinstance(self.traj, Trajectory):
            return self._process_traj(self.traj, max_diameter, min_duration)
        elif isinstance(self.traj, TrajectoryCollection):
            trajs = self.traj.trajectories
            if self.n_processes > 1 or self.n_processes is None:
                return self._process_traj_collection_multiprocessing(
                    trajs, max_diameter, min_duration
                )
            else:
                return self._process_traj_collection(trajs, max_diameter, min_duration)
        else:
            raise TypeError

    def _process_traj_collection(self, trajs, max_diameter, min_duration):
        results = []
        for traj in trajs:
            for time_range in self._process_traj(traj, max_diameter, min_duration):
                results.append(time_range)
        return results

    def _process_traj_collection_multiprocessing(
        self, trajs, max_diameter, min_duration
    ):
        from movingpandas.tools._multi_threading import split_list

        p = Pool(self.n_processes)
        data = split_list(trajs, self.n_processes)

        results = []
        for stops in p.starmap(
            self._process_traj_collection,
            zip(data, repeat(max_diameter), repeat(min_duration)),
        ):
            results.extend(stops)
        return results

    def _process_traj(self, traj, max_diameter, min_duration):
        detected_stops = []
        pts, xs, ys, ts = [], [], [], []
        minx, miny = float("inf"), float("inf")
        maxx, maxy = float("-inf"), float("-inf")
        geom = MultiPoint()
        is_stopped = False
        previously_stopped = False

        for t, pt in traj.df[traj.get_geom_col()].items():
            pts.append(pt)
            xs.append(pt.x)
            ys.append(pt.y)
            ts.append(t)
            first_to_keep = 0

            if not is_stopped:  # remove points to the specified min_duration
                while (
                    len(pts[first_to_keep:]) > 2
                    and ts[-1] - ts[first_to_keep] >= min_duration
                ):
                    first_to_keep += 1
                pts = pts[first_to_keep:]
                xs = xs[first_to_keep:]
                ys = ys[first_to_keep:]
                ts = ts[first_to_keep:]

            minx = min(xs)
            miny = min(ys)
            maxx = max(xs)
            maxy = max(ys)

            is_stopped = False
            if len(pts) > 1:
                if traj.is_latlon:
                    d = distance.distance((miny, minx), (maxy, maxx)).meters
                else:
                    d = hypot(maxx - minx, maxy - miny)
                if d < max_diameter * 1.5:
                    geom = MultiPoint(pts)
                    if mrr_diagonal(geom, traj.is_latlon) < max_diameter:
                        is_stopped = True

            if not is_stopped and previously_stopped and len(pts) > 1:
                segment_end = ts[-2]
                segment_begin = ts[0]
                if (
                    segment_end - segment_begin >= min_duration
                ):  # detected end of a stop
                    detected_stops.append(
                        TRangeWithTrajId(segment_begin, segment_end, traj.id)
                    )
                    pts = [pts[-1]]
                    xs = [xs[-1]]
                    ys = [ys[-1]]
                    ts = [ts[-1]]

            previously_stopped = is_stopped

        if is_stopped and ts[-1] - ts[0] >= min_duration:
            detected_stops.append(TRangeWithTrajId(ts[0], ts[-1], traj.id))

        return detected_stops

    def get_stop_segments(self, max_diameter, min_duration):
        """
        Returns detected stop trajectory segments.

        Parameters
        ----------
        max_diameter : float
            Maximum diameter for stop detection. (Distances will be calculated
            in meters using geodesic distance calculations for geographic projections
            (e.g. EPSG:4326 WGS84) and in CRS units for all other projections)
        min_duration : datetime.timedelta
            Minimum stop duration

        Returns
        -------
        TrajectoryCollection
            Trajectory segments

        Examples
        --------

        >>> detector = mpd.TrajectoryStopDetector(traj)
        >>> stops = detector.get_stop_segments(min_duration=timedelta(seconds=60),
                                               max_diameter=100)
        """
        stop_time_ranges = self.get_stop_time_ranges(max_diameter, min_duration)
        return TrajectoryCollection(
            convert_time_ranges_to_segments(self.traj, stop_time_ranges)
        )

    def get_stop_points(self, max_diameter, min_duration):
        """
        Returns detected stop location points.

        Parameters
        ----------
        max_diameter : float
            Maximum diameter for stop detection. (Distances will be calculated
            in meters using geodesic distance calculations for geographic projections
            (e.g. EPSG:4326 WGS84) and in CRS units for all other projections)
        min_duration : datetime.timedelta
            Minimum stop duration

        Returns
        -------
        geopandas.GeoDataFrame
            Stop locations as points with start and end time and stop duration
            in seconds

        Examples
        --------

        >>> detector = mpd.TrajectoryStopDetector(traj)
        >>> stops = detector.get_stop_points(min_duration=timedelta(seconds=60),
                                             max_diameter=100)
        """
        stop_time_ranges = self.get_stop_time_ranges(max_diameter, min_duration)
        stops = TrajectoryCollection(
            convert_time_ranges_to_segments(self.traj, stop_time_ranges)
        )

        stop_pts = GeoDataFrame(columns=["geometry"]).set_geometry("geometry")
        stop_pts["stop_id"] = [track.id for track in stops.trajectories]
        stop_pts = stop_pts.set_index("stop_id")

        for stop in stops:
            stop_pts.at[stop.id, "start_time"] = stop.get_start_time()
            stop_pts.at[stop.id, "end_time"] = stop.get_end_time()
            pt = Point(stop.df.geometry.x.median(), stop.df.geometry.y.median())
            stop_pts.at[stop.id, "geometry"] = pt
            stop_pts.at[stop.id, "traj_id"] = stop.parent.id

        if stops:
            stop_pts["duration_s"] = (
                stop_pts["end_time"] - stop_pts["start_time"]
            ).dt.total_seconds()
            stop_pts["traj_id"] = stop_pts["traj_id"].astype(type(stop.parent.id))

        return stop_pts
