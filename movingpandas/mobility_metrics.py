# -*- coding: utf-8 -*-
#
# Methods and docstrings adapted from scikit-mobility
# https://github.com/scikit-mobility/scikit-mobility
# Copyright (c) 2021, scikit-mobility contributors
# BSD 3-Clause License

import math

import numpy as np
import pandas as pd
from shapely.geometry import Point

from movingpandas.geometry_utils import measure_distance
from movingpandas.trajectory import Trajectory


class MobilityMetricsCalculator:
    """Calculate mobility metrics for a Trajectory or TrajectoryCollection."""

    def __init__(self, traj):
        """
        Create a MobilityMetricsCalculator.

        Parameters
        ----------
        traj : Trajectory or TrajectoryCollection
            Trajectory or TrajectoryCollection to calculate metrics for.

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj)
        """
        if isinstance(traj, Trajectory):
            self._trajectories = [traj]
        else:
            self._trajectories = traj.trajectories

    def radius_of_gyration(self):
        """
        Compute the radius of gyration in meters (or CRS units for projected
        CRS).

        The radius of gyration of an individual :math:`u` is defined as
        [GHB2008]_ [PRQPG2013]_:

        .. math::
            r_g(u) = \sqrt{ \\frac{1}{n_u} \sum_{i=1}^{n_u} dist(r_i(u) - r_{cm}(u))^2}

        where :math:`r_i(u)` represents the :math:`n_u` positions recorded for
        :math:`u`, and :math:`r_{cm}(u)` is the center of mass of :math:`u`'s
        trajectory. In mobility analysis, the radius of gyration indicates the
        characteristic distance travelled by :math:`u`.

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
        .. [GHB2008] González, M. C., Hidalgo, C. A. & Barabási, A. L. (2008)
           Understanding individual human mobility patterns. Nature, 453,
           779-782, https://www.nature.com/articles/nature06958.
        .. [PRQPG2013] Pappalardo, L., Rinzivillo, S., Qu, Z., Pedreschi, D. &
           Giannotti, F. (2013) Understanding the patterns of car travel.
           European Physics Journal Special Topics 215(1), 61-73,
           https://link.springer.com/article/10.1140%2Fepjst%2Fe2013-01715-5
        """  # noqa: E501, W605
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

    def distance_straight_line(self):
        """
        Compute the straight-line distance.

        The straight-line distance of an individual :math:`u` is defined as
        [SQBB2010]_:

        .. math::
            d_{SL}(u) = \sum_{j=2}^{n_u} dist(r_{j-1}(u), r_j(u))

        where :math:`r_j(u)` represents the :math:`n_u` positions recorded
        for :math:`u`, and :math:`dist` is the geographic distance between
        two points. This is the total distance covered by :math:`u`.

        Returns
        -------
        float or pd.Series
            float if a single Trajectory was provided, otherwise pd.Series
            indexed by trajectory id

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj).distance_straight_line()

        References
        ----------
        .. [SQBB2010] Song, C., Qu, Z., Blumm, N. & Barabási, A. L. (2010)
           Limits of Predictability in Human Mobility. Science 327(5968),
           1018-1021, https://science.sciencemag.org/content/327/5968/1018
        """  # noqa: W605
        results = {}
        for traj in self._trajectories:
            results[traj.id] = traj.get_length()
        if len(self._trajectories) == 1:
            return next(iter(results.values()))
        return pd.Series(results)

    def random_entropy(self):
        """
        Compute the random entropy.

        The random entropy of an individual :math:`u` is defined as
        [EP2009]_ [SQBB2010]_:

        .. math::
            E_{rand}(u) = log_2(N_u)

        where :math:`N_u` is the number of distinct locations visited by
        :math:`u`, capturing the degree of predictability of :math:`u`’s
        whereabouts if each location is visited with equal probability.

        Returns
        -------
        float or pd.Series
            float if a single Trajectory was provided, otherwise pd.Series
            indexed by trajectory id

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj).random_entropy()

        References
        ----------
        .. [EP2009] Eagle, N. & Pentland, A. S. (2009) Eigenbehaviors:
           identifying structure in routine. Behavioral Ecology and
           Sociobiology 63(7), 1057-1066,
           https://link.springer.com/article/10.1007/s00265-009-0830-6
        .. [SQBB2010] Song, C., Qu, Z., Blumm, N. & Barabási, A. L. (2010)
           Limits of Predictability in Human Mobility. Science 327(5968),
           1018-1021, https://science.sciencemag.org/content/327/5968/1018
        """
        results = {}
        for traj in self._trajectories:
            n_locations = traj.df.geometry.nunique()
            results[traj.id] = math.log2(n_locations)
        if len(self._trajectories) == 1:
            return next(iter(results.values()))
        return pd.Series(results)
