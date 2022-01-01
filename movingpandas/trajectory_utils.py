# -*- coding: utf-8 -*-

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection


def convert_time_ranges_to_segments(traj, time_ranges):
    """
    Extracts trajectory segments for the specified time ranges.

    Parameters
    ----------
    traj : Trajectory/TrajectoryCollection
        Trajectory or TrajectoryCollection from which to extract the time_ranges
    time_ranges : list
        List of TimeRangeWithTrajId objects

    Returns
    -------
    list
        Extracted trajectory segements
    """
    if isinstance(traj, Trajectory):
        handle_collection = False
    elif isinstance(traj, TrajectoryCollection):
        handle_collection = True
    else:
        raise TypeError

    segments = []
    for time_range in time_ranges:
        try:
            if handle_collection:
                segments.append(
                    traj.get_trajectory(time_range.traj_id).get_segment_between(
                        time_range.t_0, time_range.t_n
                    )
                )
            else:
                segments.append(
                    traj.get_segment_between(time_range.t_0, time_range.t_n)
                )
        except ValueError:
            pass
    return segments
