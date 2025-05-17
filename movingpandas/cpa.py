"""Calculates the Closest Point of Approach (CPA) between two trajectories.

This module provides functionality to determine the point in time and space
where two trajectories are predicted to be closest to each other, assuming
current speed and direction between consecutive observations.

The core calculation determines:
- The minimum distance expected between the two objects (Distance at CPA).
- The time until this minimum distance occurs (Time to CPA, TCPA).
- The linestring connecting the two objects at the moment of CPA

You can instantiate a calculation `CPACalculator`, with two MovingPandas
Trajectory objects as input. Using the `min` function allows to find the CPA
distance, TCPA, and the corresponding locations on each trajectory.

This type of analysis is used in several domains, including:
- Maritime traffic management for collision risk assessment.
- Air traffic control.
"""

import datetime
from typing import Iterator, Optional, Union, get_args
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

import movingpandas as mpd

# these calculations work for all datetime types
date_type = Union[np.datetime64, datetime.datetime, pd.Timestamp]


class CPACalculator:
    """Closest Point of Approach calculator. The algorithm works in 2d or 3d.
    Coordinates are expected to be cartesian, in meters.

    Parameters:
    -----------
    traj_a: Trajectory
         First trajectory to use in the closest point of approach calculations.
    traj_b: Trajectory
         Second trajectory to use in the closest point of approach calculations.

    Examples:
    ---------
    >>> mpd.cpa.CPA(traj_a, traj_b).min()

    """

    variable_doc = """
        Results contain the following variables:
            t_at: time at closest point of approach (datetime)
            t_to: time to closest point of approach (timedelta)
            geometry: line between traj_a and traj_b at closest approach
            dist: distance at cpa

            status: A string indicating the relative movement pattern between
            two trajectories (traj_a and traj_b). The following status values
            can occur:
            - "no-overlap": The time periods covered by the two trajectories do
              not overlap at all.
            - "converging": The objects are currently moving closer together,
              but their point of closest approach (CPA) is predicted to occur
              after the current time interval (t_to < 0).
            - "diverging": The objects are currently moving apart, indicating
              their point of closest approach (CPA) occurred before the current
              time interval (t_to > t1 - t0).
            - "approaching": The objects are moving towards their point of
              closest approach (CPA), which is predicted to occur within the
              current time interval (0 < t_to < (t1 - t0)).
            - "parallel": The objects are moving in parallel directions relative
              to each other (dist2 == 0).
            - "touching": The time intervals of the two trajectories only
              intersect at a single, instantaneous point in time (t1 == t0).
    """

    def __init__(self, traj_a: mpd.Trajectory, traj_b: mpd.Trajectory):
        """Generate a CPA calculation"""
        if not isinstance(traj_a, mpd.Trajectory):
            raise TypeError(f"traj_a should be a trajectory, got a {type(traj_a)}")
        if not isinstance(traj_b, mpd.Trajectory):
            raise TypeError(f"traj_b should be a trajectory, got a {type(traj_b)}")

        if traj_a.is_latlon:
            message = (
                f"Distances in CPA are computed using Euclidean geometry but "
                f"the trajectory coordinate system is {traj_a.crs}."
            )
            warnings.warn(message, UserWarning)
        if traj_b.is_latlon:
            message = (
                f"Distances in CPA are computed using Euclidean geometry but "
                f"the traj_b coordinate system is {traj_b.crs}."
            )
            warnings.warn(message, UserWarning)

        self.traj_a = traj_a
        self.traj_b = traj_b

    @staticmethod
    def _no_overlap():
        """Generate a result for the case if there is no temporal overlap
        between two trajectories."""
        # Time is not defined
        t_at = pd.NaT
        # time delta undefined is also NaT
        t_to = pd.NaT
        # Distance is not defined
        dist = np.nan
        status = "no-overlap"

        # empty LineString (check with is_empty)
        geometry = shapely.LineString()
        data = {
            "t_at": t_at,
            "t_to": t_to,
            "dist": dist,
            "geometry": geometry,
            "status": status,
        }
        return pd.Series(data=data)

    def _touching_times(self):
        """Return a result if temporal intervals of traj a and b are touching."""
        traj_a = self.traj_a
        traj_b = self.traj_b

        # check temporal overlap
        t_min = max(traj_a.get_start_time(), traj_b.get_start_time())
        t_max = min(traj_a.get_end_time(), traj_b.get_end_time())

        assert t_min == t_max, f"t_min should equal t_max, but got {t_min}, {t_max}"

        # lookup  position at time t_min
        pos_a = traj_a.get_position_at(t_min)
        pos_b = traj_b.get_position_at(t_min)

        # compute distance between a and b (in 2 or 3d, depending on length of coords)
        d_ab = np.asarray(pos_a.coords)[0] - np.asarray(pos_b.coords)[0]
        # distances computed with np.dot, instead of shapely distance, so that
        # 3d is supported
        dist2 = np.dot(d_ab, d_ab).item()
        dist = dist2**0.5

        t_at = pd.Timestamp(t_min)
        t_to = pd.Timedelta(0)
        dist = dist
        status = "touching"
        geometry = shapely.LineString([pos_a, pos_b])
        data = {
            "t_at": t_at,
            "t_to": t_to,
            "dist": dist,
            "geometry": geometry,
            "status": status,
        }
        return pd.Series(data=data)

    @staticmethod
    def _segment(
        p0: shapely.Point,
        p1: shapely.Point,
        q0: shapely.Point,
        q1: shapely.Point,
        t0: date_type,
        t1: date_type,
    ) -> pd.Series:
        (
            """
        Compute the closest point of approach (cpa) for one segment,
            a two pairs of points ((p0, p1), (q0, q1)) for time window (t0, t1)
        """
            + CPACalculator.variable_doc
        )

        if not isinstance(p0, shapely.Point):
            raise TypeError(f"p0 should be a shapely.Point, got a {type(p0)}")
        if not isinstance(p1, shapely.Point):
            raise TypeError(f"p1 should be a shapely.Point, got a {type(p1)}")
        if not isinstance(q0, shapely.Point):
            raise TypeError(f"q0 should be a shapely.Point, got a {type(q0)}")
        if not isinstance(q1, shapely.Point):
            raise TypeError(f"q1 should be a shapely.Point, got a {type(q1)}")
        if not isinstance(t0, get_args(date_type)):
            raise TypeError(f"t0 should be a datetime, got a {type(t0)}")
        if not isinstance(t1, get_args(date_type)):
            raise TypeError(f"t1 should be a datetime, got a {type(t1)}")

        # we follow the implementation of postgis
        # In particalur the function segments_tcpa in
        # https://github.com/postgis/postgis/blob/master/liblwgeom/lwlinearreferencing.c

        # This function corresponds with segments_tcpa Here we keep track of
        # cpa, distance and tcpa, so the function is renamed to cpa_segment.

        # We keep track of the original points
        p0_orig = p0
        q0_orig = q0

        # We convert to vectors because the - operator in shapely is the spatial
        # difference operator Here we are thinking in arrays / vectors Coords
        # returns a 1x2 matrix. By using [0] we get the vector of length 2
        p0 = np.asarray(p0.coords)[0]
        p1 = np.asarray(p1.coords)[0]
        q0 = np.asarray(q0.coords)[0]
        q1 = np.asarray(q1.coords)[0]

        # velocity of p, trajectory a
        pv = p1 - p0

        # velocity of q, trajectory b
        qv = q1 - q0

        # velocity difference of p an q
        dv = pv - qv

        # dv2 is the squared length of the vector of dv
        # Dot operator returns a vector of length 1, we only want the scalar
        dv2 = np.dot(dv, dv).item()

        # This is a special case. This happens when p and q are moving in the
        # same direction. If this is the case we are done. We'll introduce a
        # special status (parallel)
        if dv2 == 0.0:
            # /* Distance is the same at any time, we pick the earliest */
            # relative distance is similar we can't compute approach
            status = "parallel"

            # Now for a bit of extra work We have to return a similar series to
            # what we return when we did find a cpa We'll use the point,
            # distance, time at t0
            p = p0_orig
            q = q0_orig
            # compute distance at t0
            d_pq = np.asarray(p.coords)[0] - np.asarray(q.coords)[0]
            dist2 = np.dot(d_pq, d_pq).item()
            dist = dist2**0.5

            pq = shapely.LineString([p0_orig, q0_orig])

            t_at = pd.Timestamp(t0)
            t_to = t_at - t0
            result = pd.Series(
                {
                    "t_at": t_at,
                    "t_to": t_to,
                    "geometry": pq,
                    "dist": dist,
                    "status": status,
                }
            )
            return result

        # Now we have to find out if the objects meet in our time window, in the
        # past or in the future.

        # Vector between current points in trajectory a and b
        w0 = p0 - q0

        assert dv2 != 0, "dv2 should not be 0"
        # This is the relative time (as a fraction of t1 - t0)
        # when objects are closest together.
        # In nautical applications is referred to as time to/until closest point
        # of approach, e.g. http://dx.doi.org/10.12716/1001.09.01.06
        t_tot = -np.dot(w0, dv).item() / dv2

        # We introduce the concept of status so we can recall if objects are
        # diverging or not.
        status = ""

        # Now that we know the fractional time to the closest point of approach we can
        # determine if trajectories are moving closer together (converging) or
        # away from each other (diverging), or in the time window t0 - t1, are
        # approaching (reaching the closest point).
        #
        # Compute t as the clipped version of t_tot when converging or
        # diverging (naming of t_tot, t are in line with naming in postgis / lwgeom)
        #
        t = t_tot
        if t_tot > 1:
            # converging
            t = 1
            status = "converging"
        elif t < 0.0:
            # diverging
            t = 0
            status = "diverging"
        else:
            status = "approaching"

        # Create new coordinates when moving over the duration of
        # We'll create a separate variable.
        p_coords = p0 + pv * t
        q_coords = q0 + qv * t

        # p and q are the position at the cpa
        p = shapely.Point(*p_coords)
        q = shapely.Point(*q_coords)

        # We can now also compute time of the closest point of approach (also
        # referred to as TCPA in aerial applications) We refer to t_at
        # (datetime) as time at the closest point of approach and t_to as the
        # time to the closest point of approach. In python you can operate on
        # datetimes with fractions (t1 - t0) is a time delta, t is a fraction
        # Added to t0 this gives a datetime. This saves us from converting to
        # timestamps and back. t = t0 + (t1 - t0) * t;

        # t_to is not clipped to the current time window
        t_to = (pd.Timestamp(t1) - pd.Timestamp(t0)) * t_tot
        # t_at is clipped, so we use t
        t_at = t0 + (t1 - t0) * t
        # make sure we have a timestamp
        t_at = pd.Timestamp(t_at)

        # Now we can compute the distance Because we do everything using coords
        # this also works when geometry contains a z coordinate For example for
        # airplanes and submarines.
        d_pq = np.asarray(p.coords)[0] - np.asarray(q.coords)[0]
        dist2 = np.dot(d_pq, d_pq).item()
        dist = dist2**0.5

        # Geopandas (in particular certain gis formats) do not support multiple
        # geometry columns. So we'll return the closest point of approach as the
        # closest line of approach. The line runs from a point on p0-p1 to a
        # point on q0-q1.
        pq = shapely.LineString([p, q])
        geometry = pq
        result = pd.Series(
            {
                "t_at": t_at,
                "t_to": t_to,
                "geometry": geometry,
                "dist": dist,
                "status": status,
            }
        )
        return result

    def iter_segments(self) -> Iterator[pd.Series]:
        (
            """Generate the closest point of approach variables for all time
        steps of trajectories a and b.

        """
            + CPACalculator.variable_doc
        )

        traj_a = self.traj_a
        traj_b = self.traj_b

        cpa = None
        # we follow the implementation of postgis
        # https://github.com/postgis/postgis/blob/9637dc369361ac118e1ad37da7a519dae9dfab5e/postgis/lwgeom_functions_temporal.c#L83

        # check temporal overlap
        t_min = max(traj_a.get_start_time(), traj_b.get_start_time())
        t_max = min(traj_a.get_end_time(), traj_b.get_end_time())

        # check if we have an overlapping range
        if t_max < t_min:
            return self._no_overlap()

        # Filter t_ab on common range (t_min, t_max)....
        # and collect values in common time range from inputs
        t_ab = np.unique(np.sort(np.r_[traj_a.df.index, traj_b.df.index]))

        # filter, inclusive
        t_ab = t_ab[
            np.logical_and(t_ab >= np.datetime64(t_min), t_ab <= np.datetime64(t_max))
        ]

        t_ab_intervals = np.c_[t_ab[:-1], t_ab[1:]]

        for interval in t_ab_intervals:
            t0, t1 = interval

            # Equivalent code from lwgeom ptarray_locate_along_linear
            p0 = traj_a.interpolate_position_at(t0)
            p1 = traj_a.interpolate_position_at(t1)
            q0 = traj_b.interpolate_position_at(t0)
            q1 = traj_b.interpolate_position_at(t1)

            # Equivalent code from lwgeom:
            # t = segments_tcpa(&p0, &p1, &q0, &q1, t0, t1);
            cpa = self._segment(p0=p0, p1=p1, q0=q0, q1=q1, t0=t0, t1=t1)
            yield cpa

    def min(self) -> Optional[pd.Series]:
        (
            """
        Generate the minimum closest point of approach over all time
        steps of trajectories a and b.

        """
            + CPACalculator.variable_doc
        )

        # gbox is the bounding box in x,y,z,m
        # tmin = FP_MAX(gbox1.mmin, gbox2.mmin);
        # tmax = FP_MIN(gbox1.mmax, gbox2.mmax);

        traj_a = self.traj_a
        traj_b = self.traj_b

        # check temporal overlap
        t_min = max(traj_a.get_start_time(), traj_b.get_start_time())
        t_max = min(traj_a.get_end_time(), traj_b.get_end_time())

        # check if we have an overlapping range
        if t_max < t_min:
            return self._no_overlap()

        if t_min == t_max:
            return self._touching_times()

        min_dist = np.finfo(np.double).max
        min_cpa = None
        for cpa in self.iter_segments():
            if cpa.dist < min_dist:
                min_dist = cpa.dist
                min_cpa = cpa

        return min_cpa

    def segments_gdf(self) -> gpd.GeoDataFrame:
        (
            """Generate a GeoDataFrame with all closest point of approach
        variables for all time steps of trajectories a and b. The geometry
        column is set to the pq linestring. The crs is reused from traj_a.

        """
            + CPACalculator.variable_doc
        )

        cpas = []
        for cpa in self.iter_segments():
            cpas.append(cpa)
        result = gpd.GeoDataFrame(cpas, geometry="geometry", crs=self.traj_a.crs)
        return result
