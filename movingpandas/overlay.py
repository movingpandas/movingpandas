# -*- coding: utf-8 -*-

import itertools as it
import pandas as pd
from shapely.geometry import Point, LineString, shape
from shapely.affinity import translate
from datetime import datetime, timedelta

from .spatiotemporal_utils import TRange, STRange


def _get_spatiotemporal_ref(row):
    """
    Returns the SpatioTemporalRange for the input row's spatial_intersection
    LineString by interpolating timestamps.
    """
    if row["spatial_intersection"].is_empty:
        return None
    if type(row["spatial_intersection"]) == LineString:
        pt0 = Point(row["spatial_intersection"].coords[0])
        ptn = Point(row["spatial_intersection"].coords[-1])
        t = row["prev_t"]
        t_delta = row["t"] - t
        length = row["line"].length
        t0 = t + (t_delta * row["line"].project(pt0) / length)
        tn = t + (t_delta * row["line"].project(ptn) / length)
        # to avoid numerical issues with microseconds beyond six digits,
        # we reconstruct the timestamps
        t0 = datetime(
            t0.year, t0.month, t0.day, t0.hour, t0.minute, t0.second, t0.microsecond
        )
        tn = datetime(
            tn.year, tn.month, tn.day, tn.hour, tn.minute, tn.second, tn.microsecond
        )
        # to avoid intersection issues with zero length lines
        if ptn == translate(pt0, 0.00000001, 0.00000001):
            t0 = row["prev_t"]
            tn = row["t"]
        # to avoid numerical issues with timestamps
        if is_equal(tn, row["t"]):
            tn = row["t"]
        if is_equal(t0, row["prev_t"]):
            t0 = row["prev_t"]
        return STRange(pt0, ptn, t0, tn)
    else:
        return None


def _dissolve_ranges(ranges):
    """
    SpatioTemporalRanges that touch (i.e. the end of one equals the start of
    another) are dissolved (aka. merged).
    """
    if len(ranges) == 0:
        raise ValueError("Nothing to dissolve (received empty ranges)!")
    dissolved_ranges = []
    new_range = None
    for r in ranges:
        if r is None:
            continue  # raise ValueError('Received range that is None!')
        if new_range is None:
            new_range = STRange(r.pt_0, r.pt_n, r.t_0, r.t_n)
        elif new_range.t_n == r.t_0 or (
            r.t_0 > new_range.t_n and is_equal(r.t_0, new_range.t_n)
        ):
            new_range.t_n = r.t_n
            new_range.pt_n = r.pt_n
        else:
            dissolved_ranges.append(new_range)
            new_range = STRange(r.pt_0, r.pt_n, r.t_0, r.t_n)
    dissolved_ranges.append(new_range)
    return dissolved_ranges


def is_equal(t1, t2):
    """
    Similar timestamps are considered equal to avoid numerical issues.
    """
    if type(t2) == pd.Timestamp:
        td = abs(t1 - t2.tz_localize(t1.tzinfo).to_pydatetime())
    else:
        td = abs(t1 - t2)
    return td < timedelta(milliseconds=10)


def intersects(traj, polygon):
    try:
        line = traj.to_linestring()
    except:  # noqa: E722
        return False
    return line.intersects(polygon)


def create_entry_and_exit_points(traj, range):
    """
    Returns a dataframe with inserted entry and exit points according to the
    provided SpatioTemporalRange.
    """
    if type(range) != STRange:
        raise TypeError("Input range has to be a SpatioTemporalRange!")

    crs = traj.df.crs
    temp_df = traj.df.copy()

    index = traj.df.index
    # Create row at entry point with attributes from previous row = pad
    row0 = traj.df.iloc[index.get_indexer([range.t_0], method="pad")[0]].copy()
    row0["geometry"] = range.pt_0
    # Create row at exit point
    rown = traj.df.iloc[index.get_indexer([range.t_n], method="pad")[0]].copy()
    rown["geometry"] = range.pt_n
    # Insert rows
    try:
        temp_df.loc[range.t_0] = row0
    except ValueError as err:
        if str(err) == "cannot set a single element with an array":
            # fix for https://github.com/anitagraser/movingpandas/issues/118
            # (not sure what causes this problem)
            pass
        else:
            raise err
    try:
        temp_df.loc[range.t_n] = rown
    except ValueError as err:
        if str(err) == "cannot set a single element with an array":
            pass
        else:
            raise err

    # ensure CRS is set, fix for https://github.com/anitagraser/movingpandas/issues/291
    temp_df = temp_df.set_crs(crs, allow_override=True)

    return temp_df.sort_index()


def _get_segments_for_ranges(traj, ranges):
    counter = it.count()
    segments = []  # list of trajectories
    for the_range in ranges:
        temp_traj = traj.copy()
        if type(the_range) == STRange:
            temp_traj.df = create_entry_and_exit_points(traj, the_range)
        try:
            segment = temp_traj.get_segment_between(the_range.t_0, the_range.t_n)
        except ValueError:
            continue
        segment.id = f"{traj.id}_{next(counter)}"
        segment.parent = traj
        # remove timestamps from trajectory IDs
        segment.df[segment.get_traj_id_col()] = segment.id
        segments.append(segment)
    return segments


def _determine_time_ranges_pointbased(traj, polygon):
    df = traj.df
    df["t"] = df.index
    df["intersects"] = df.intersects(polygon)
    df["segment"] = (df["intersects"].shift(1) != df["intersects"]).astype(int).cumsum()
    df = df.groupby("segment", as_index=False).agg(
        {"t": ["min", "max"], "intersects": ["min"]}
    )
    df.columns = df.columns.map("_".join)

    ranges = []
    for _, row in df[df["intersects_min"]].iterrows():
        ranges.append(TRange(row["t_min"], row["t_max"]))
    return ranges


def _get_potentially_intersecting_lines(traj, polygon):
    """
    Uses a spatial index to determine which parts of the trajectory may be
    intersecting with the polygon

    Returns
    -------
    possible_matches : GeoDataFrame
        GeoDataFrame of potentially intersecting lines
    """
    line_df = traj._to_line_df()
    spatial_index = line_df.sindex
    if spatial_index:
        possible_matches_index = list(spatial_index.intersection(polygon.bounds))
        possible_matches = line_df.iloc[possible_matches_index].sort_index()
    else:
        possible_matches = line_df
    return possible_matches


def _determine_time_ranges_linebased(traj, polygon):
    """
    Returns list of SpatioTemporalRanges that describe trajectory intersections
    with the provided polygon.
    """
    # Note: If the trajectory contains consecutive rows without location change
    #       these will result in zero length lines that return an empty
    #       intersection.
    possible_matches = _get_potentially_intersecting_lines(traj, polygon)
    possible_matches["spatial_intersection"] = possible_matches.intersection(polygon)

    # Intersecting trajectories with complex geometries (e.g. multipolygons with holes)
    # often ends up as MultiLineStrings, which we can't handle downstream.
    # Ensure we break MultiLineStrings into simple LineStrings
    if "MultiLineString" in possible_matches["spatial_intersection"].geom_type.unique():
        spatial_intersection_exp = possible_matches["spatial_intersection"].explode(
            index_parts=False
        )
        possible_matches = possible_matches.reindex(spatial_intersection_exp.index)
        possible_matches["spatial_intersection"] = spatial_intersection_exp

    possible_matches["spatiotemporal_intersection"] = possible_matches.apply(
        _get_spatiotemporal_ref, axis=1
    )
    ranges = possible_matches["spatiotemporal_intersection"]
    return _dissolve_ranges(ranges)


def clip(traj, polygon, pointbased=False):
    """
    Returns a list of trajectory segments clipped by the given feature.
    """
    if not intersects(traj, polygon):
        return []
    if pointbased:
        ranges = _determine_time_ranges_pointbased(traj, polygon)
    else:
        ranges = _determine_time_ranges_linebased(traj, polygon)
    return _get_segments_for_ranges(traj, ranges)


def _get_geometry_and_properties_from_feature(feature):
    """
    Provides convenience access to geometry and properties of a Shapely feature.
    """
    if type(feature) != dict:
        raise TypeError("Trajectories can only be intersected with a Shapely feature!")
    try:
        geometry = shape(feature["geometry"])
        properties = feature["properties"]
    except:  # noqa: E722
        raise TypeError("Trajectories can only be intersected with a Shapely feature!")
    return geometry, properties


def intersection(traj, feature, pointbased=False):
    """
    Returns a list of trajectory segments that intersect the given feature.
    Resulting trajectories include the intersecting feature's attributes.
    """
    geometry, properties = _get_geometry_and_properties_from_feature(feature)
    clipped = clip(traj, geometry, pointbased)
    segments = []
    for clipping in clipped:
        for key, value in properties.items():
            clipping.df["intersecting_" + key] = value
        segments.append(clipping)
    return segments
