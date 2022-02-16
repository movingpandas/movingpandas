# -*- coding: utf-8 -*-

from geopandas import GeoDataFrame
from shapely.geometry import MultiPoint
from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import mrr_diagonal
from .trajectory_utils import convert_time_ranges_to_segments
from .time_range_utils import TemporalRangeWithTrajId


class TrajectoryStopDetector:
    """
    Detects stops in a trajectory.
    A stop is detected if the movement stays within an area of specified size for
    at least the specified duration.
    """

    def __init__(self, traj):
        """
        Create StopDetector

        Parameters
        ----------
        traj : Trajectory or TrajectoryCollection
        """
        self.traj = traj

    def get_stop_time_ranges(self, max_diameter, min_duration):
        """
        Returns detected stop start and end times

        Parameters
        ----------
        max_diameter : float
            Maximum diameter for stop detection
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
            return self._process_traj_collection(max_diameter, min_duration)
        else:
            raise TypeError

    def _process_traj_collection(self, max_diameter, min_duration):
        result = []
        for traj in self.traj:
            for time_range in self._process_traj(traj, max_diameter, min_duration):
                result.append(time_range)
        return result

    def _process_traj(self, traj, max_diameter, min_duration):
        detected_stops = []
        segment_geoms = []
        segment_times = []
        geom = MultiPoint()
        is_stopped = False
        previously_stopped = False

        for index, data in traj.df[traj.get_geom_column_name()].iteritems():
            segment_geoms.append(data)
            geom = geom.union(data)
            segment_times.append(index)

            if not is_stopped:  # remove points to the specified min_duration
                while (
                    len(segment_geoms) > 2
                    and segment_times[-1] - segment_times[0] >= min_duration
                ):
                    segment_geoms.pop(0)
                    segment_times.pop(0)
                # after removing extra points, re-generate geometry
                geom = MultiPoint(segment_geoms)

            if (
                len(segment_geoms) > 1
                and mrr_diagonal(geom, traj.is_latlon) < max_diameter
            ):
                is_stopped = True
            else:
                is_stopped = False

            if len(segment_geoms) > 1:
                segment_end = segment_times[-2]
                segment_begin = segment_times[0]
                if not is_stopped and previously_stopped:
                    if (
                        segment_end - segment_begin >= min_duration
                    ):  # detected end of a stop
                        detected_stops.append(
                            TemporalRangeWithTrajId(segment_begin, segment_end, traj.id)
                        )
                        segment_geoms = []
                        segment_times = []
                        geom = MultiPoint()

            previously_stopped = is_stopped

        if is_stopped and segment_times[-1] - segment_times[0] >= min_duration:
            detected_stops.append(
                TemporalRangeWithTrajId(segment_times[0], segment_times[-1], traj.id)
            )

        return detected_stops

    def get_stop_segments(self, max_diameter, min_duration):
        """
        Returns detected stop trajectory segments

        Parameters
        ----------
        max_diameter : float
            Maximum diameter for stop detection
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
        Returns detected stop location points

        Parameters
        ----------
        max_diameter : float
            Maximum diameter for stop detection
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
            stop_pts.at[stop.id, "geometry"] = stop.get_start_location()
            stop_pts.at[stop.id, "traj_id"] = stop.parent.id

        if len(stops) > 0:
            stop_pts["duration_s"] = (
                stop_pts["end_time"] - stop_pts["start_time"]
            ).dt.total_seconds()
            stop_pts["traj_id"] = stop_pts["traj_id"].astype(type(stop.parent.id))

        return stop_pts
