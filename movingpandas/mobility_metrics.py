# -*- coding: utf-8 -*-

import math

import numpy as np
import pandas as pd
from shapely.geometry import Point

from movingpandas.geometry_utils import measure_distance
from movingpandas.trajectory import Trajectory


class MobilityMetricsCalculator:
    """Calculate mobility metrics for a Trajectory or TrajectoryCollection."""

    def __init__(self, traj):
        if isinstance(traj, Trajectory):
            self._trajectories = [traj]
        else:
            self._trajectories = traj.trajectories

    def radius_of_gyration(self):
        """
        Radius of gyration for each trajectory.

        Computes the root mean square distance of all visited locations from
        the center of mass (mean x/y).
        Distances are calculated in meters (or CRS units for projected CRS).

        Returns
        -------
        float or pd.Series
            float if a single Trajectory was provided, otherwise pd.Series
            indexed by trajectory id

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj).radius_of_gyration()

        References
        ----------
        .. [GHB2008] González, M. C., Hidalgo, C. A. & Barabási, A. L. (2008) Understanding individual human mobility patterns. Nature, 453, 779–782, https://www.nature.com/articles/nature06958.
        .. [PRQPG2013] Pappalardo, L., Rinzivillo, S., Qu, Z., Pedreschi, D. & Giannotti, F. (2013) Understanding the patterns of car travel. European Physics Journal Special Topics 215(1), 61-73, https://link.springer.com/article/10.1140%2Fepjst%2Fe2013-01715-5
        """  # noqa: E501
        results = {}
        for traj in self._trajectories:
            pts = traj.df.geometry
            xs = pts.x.to_numpy()
            ys = pts.y.to_numpy()
            center = Point(xs.mean(), ys.mean())
            distances = np.array(
                [
                    measure_distance(Point(x, y), center, geodesic=traj.is_latlon)
                    for y, x in zip(ys, xs)
                ]
            )
            results[traj.id] = math.sqrt(float(np.mean(distances**2)))
        if len(self._trajectories) == 1:
            return next(iter(results.values()))
        return pd.Series(results)
