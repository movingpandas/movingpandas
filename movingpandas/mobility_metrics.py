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
            return results[self._trajectories[0].id]
        return pd.Series(results)

    def distance_straight_line(self):
        """
        Compute the straight-line distance in meters (or CRS units for
        projected CRS).

        The straight-line distance of an individual :math:`u` is defined as:

        .. math:: d_{SL} = \sum_{j=2}^{n_u} dist(r_{j-1}, r_j)

        where :math:`n_u` is the number of points recorded for :math:`u`,
        :math:`r_{j-1}` and :math:`r_j` are two consecutive points,
        described as a :math:`(latitude, longitude)` pair, in :math:`u`'s
        time-ordered trajectory, and :math:`dist` is the distance
        between the two points [WTDED2015]_.

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
        .. [WTDED2015] Williams, N. E., Thomas, T. A., Dunbar, M., Eagle, N. &
           Dobra, A. (2015) Measures of Human Mobility Using Mobile Phone
           Records Enhanced with GIS Data. PLOS ONE 10(7): e0133630.
           https://doi.org/10.1371/journal.pone.0133630
        """  # noqa: E501, W605
        results = {}
        for traj in self._trajectories:
            results[traj.id] = traj.get_length()
        if len(self._trajectories) == 1:
            return results[self._trajectories[0].id]
        return pd.Series(results)

    def k_radius_of_gyration(self, k=2):
        """
        Compute the k-radius of gyration.

        The k-radius of gyration of an individual :math:`u` is defined as
        [PSRPGB2015]_:

        .. math::
            r_g^{(k)}(u) = \\sqrt{ \\frac{1}{n_u^{(k)}}
            \\sum_{i=1}^{k} n_i \\cdot dist(r_i(u), r_{cm}^{(k)}(u))^2}

        where :math:`n_u^{(k)}` is the total number of visits to the top
        :math:`k` most visited locations, :math:`n_i` is the number of visits
        to location :math:`i`, and :math:`r_{cm}^{(k)}(u)` is the center of
        mass of those locations weighted by visit count. When :math:`k` is
        greater than or equal to the number of unique locations, the result
        equals the standard radius of gyration.

        Parameters
        ----------
        k : int, optional
            Number of most-visited locations to consider (default: 2)

        Returns
        -------
        float or pd.Series
            float if a single Trajectory was provided, otherwise pd.Series
            indexed by trajectory id

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj).k_radius_of_gyration(k=2)

        References
        ----------
        .. [PSRPGB2015] Pappalardo, L., Simini, F. Rinzivillo, S., Pedreschi,
           D. Giannotti, F. & Barabasi, A. L. (2015) Returners and Explorers
           dichotomy in human mobility. Nature Communications 6,
           https://www.nature.com/articles/ncomms9166
        """  # noqa: E501
        results = {}
        for traj in self._trajectories:
            pts = list(traj.df.geometry)
            counts = {}
            for pt in pts:
                counts[pt] = counts.get(pt, 0) + 1
            top_k = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:k]
            expanded = [pt for pt, n in top_k for _ in range(n)]
            xs = np.array([pt.x for pt in expanded])
            ys = np.array([pt.y for pt in expanded])
            center = Point(xs.mean(), ys.mean())
            distances = np.array(
                [
                    measure_distance(pt, center, geodesic=traj.is_latlon)
                    for pt in expanded
                ]
            )
            results[traj.id] = math.sqrt(float(np.mean(distances**2)))
        if len(self._trajectories) == 1:
            return results[self._trajectories[0].id]
        return pd.Series(results)

    def jump_lengths(self):
        """
        Compute the jump lengths between consecutive locations in meters 
        (or CRS units for projected CRS).

        The jump length :math:`\\Delta r_i` of an individual :math:`u` is
        defined as [BHG2006]_:

        .. math::
            \\Delta r_i = dist(r_i, r_{i+1})

        where :math:`r_i` and :math:`r_{i+1}` are two consecutive positions
        recorded for :math:`u` and :math:`dist` is the distance
        between the two points.

        Returns
        -------
        np.ndarray or pd.Series
            np.ndarray of jump lengths in meters (or CRS units for projected
            CRS) if a single Trajectory was provided, otherwise pd.Series of
            np.ndarrays indexed by trajectory id

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj).jump_lengths()

        References
        ----------
        .. [BHG2006] Brockmann, D., Hufnagel, L. & Geisel, T. (2006) The
           scaling laws of human travel. Nature 439, 462-465,
           https://www.nature.com/articles/nature04292
        """  # noqa: E501, W605
        results = {}
        for traj in self._trajectories:
            pts = list(traj.df.geometry)
            results[traj.id] = np.array(
                [
                    measure_distance(pts[i - 1], pts[i], geodesic=traj.is_latlon)
                    for i in range(1, len(pts))
                ]
            )
        if len(self._trajectories) == 1:
            return results[self._trajectories[0].id]
        return pd.Series(results)

    def home_location(self, start_night="22:00", end_night="07:00"):
        """
        Compute the home location.

        The home location :math:`h(u)` of an individual :math:`u` is defined
        as the location :math:`u` visits the most during nighttime
        [CBTDHVSB2012]_ [PSO2012]_:

        .. math::
            h(u) = \\arg\max_{i} |\{r_i | t(r_i) \in [t_{startnight}, t_{endnight}] \}|

        where :math:`r_i` is a location visited by :math:`u`, :math:`t(r_i)`
        is the time when :math:`u` visited :math:`r_i`, and
        :math:`t_{startnight}` and :math:`t_{endnight}` indicates the times
        when nighttime starts and ends, respectively. If no records fall
        within the nighttime window, the most visited location overall is
        returned instead.

        Parameters
        ----------
        start_night : str or datetime.time, optional
            Start of the nighttime window, as a string in HH:MM format or a
            datetime.time object (default: "22:00")
        end_night : str or datetime.time, optional
            End of the nighttime window, as a string in HH:MM format or a
            datetime.time object (default: "07:00")

        Returns
        -------
        Point or pd.Series
            Point if a single Trajectory was provided, otherwise pd.Series
            of Points indexed by trajectory id

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj).home_location(
        ...     start_night="20:00", end_night="06:00"
        ... )

        References
        ----------
        .. [CBTDHVSB2012] Csáji, B. C., Browet, A., Traag, V. A., Delvenne,
           J.-C., Huens, E., Van Dooren, P., Smoreda, Z. & Blondel, V. D.
           (2012) Exploring the Mobility of Mobile Phone Users. Physica A:
           Statistical Mechanics and its Applications 392(6), 1459-1473,
           https://www.sciencedirect.com/science/article/pii/S0378437112010059
        .. [PSO2012] Phithakkitnukoon, S., Smoreda, Z. & Olivier, P. (2012)
           Socio-geography of human mobility: A study using longitudinal
           mobile phone data. PLOS ONE 7(6): e39253.
           https://doi.org/10.1371/journal.pone.0039253
        """  # noqa: W605
        results = {}
        for traj in self._trajectories:
            pts = traj.df.geometry
            night_pts = pts.between_time(start_night, end_night)
            candidates = night_pts if len(night_pts) > 0 else pts
            results[traj.id] = self._most_visited_location(candidates)
        if len(self._trajectories) == 1:
            return results[self._trajectories[0].id]
        return pd.Series(results)

    @staticmethod
    def _most_visited_location(pts):
        coords = pd.Series(list(zip(pts.y, pts.x)), index=pts.index)
        counts = (
            coords.value_counts()
            .rename_axis("coords")
            .reset_index(name="count")
            .sort_values(["count", "coords"], ascending=[False, True])
        )
        lat, lon = counts.iloc[0]["coords"]
        return Point(lon, lat)

    def real_entropy(self):
        """
        Compute the real entropy.

        The real entropy of an individual :math:`u` is defined as
        [SQBB2010]_:

        .. math::
            E(u) = -\\sum_{T'_u} P(T'_u) \\log_2[P(T'_u)]

        where :math:`T'_u` represents all possible time-ordered subsequences
        of :math:`u`'s trajectory. The real entropy hence depends not only
        on the frequency of visitation, but also the order in which the nodes
        were visited and the time spent at each location, thus capturing the
        full spatiotemporal order present in an :math:`u`'s mobility patterns.
    

        Returns
        -------
        float or pd.Series
            float if a single Trajectory was provided, otherwise pd.Series
            indexed by trajectory id

        Examples
        --------
        >>> mpd.MobilityMetricsCalculator(traj).real_entropy()

        References
        ----------
        .. [SQBB2010] Song, C., Qu, Z., Blumm, N. & Barabási, A. L. (2010)
           Limits of Predictability in Human Mobility. Science 327(5968),
           1018-1021, https://science.sciencemag.org/content/327/5968/1018
        """
        results = {}
        for traj in self._trajectories:
            sequence = list(zip(traj.df.geometry.x, traj.df.geometry.y))
            results[traj.id] = self._true_entropy(sequence)
        if len(self._trajectories) == 1:
            return results[self._trajectories[0].id]
        return pd.Series(results)

    @staticmethod
    def _true_entropy(sequence):
        n = len(sequence)
        if n <= 1:
            return 0.0

        def in_seq(superseq, subseq):
            n_sub = len(subseq)
            return any(
                superseq[i : i + n_sub] == subseq
                for i in range(len(superseq) - n_sub + 1)
            )

        sum_lambda = 3.0
        for i in range(1, n - 1):
            j = i + 1
            while j < n and in_seq(sequence[:i], sequence[i:j]):
                j += 1
            if j == n:
                j += 1
            sum_lambda += j - i
        return (n * math.log2(n)) / sum_lambda

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
            return results[self._trajectories[0].id]
        return pd.Series(results)
