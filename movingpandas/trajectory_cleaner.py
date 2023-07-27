# -*- coding: utf-8 -*-

import pandas as pd
from pandas.api.types import is_numeric_dtype

from copy import copy

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .geometry_utils import measure_distance_geodesic, measure_distance_euclidean
from .unit_utils import UNITS, get_conversion


class TrajectoryCleaner:
    """
    Cleaner base class
    """

    def __init__(self, traj):
        """
        Create TrajectoryCleaner

        Parameters
        ----------
        traj : Trajectory or TrajectoryCollection
        """
        self.traj = traj

    def clean(self, **kwargs):
        """
        Clean the input Trajectory/TrajectoryCollection.

        Returns
        -------
        Trajectory/TrajectoryCollection
            Cleaned Trajectory or TrajectoryCollection
        """
        if isinstance(self.traj, Trajectory):
            return self._clean_traj(self.traj, **kwargs)
        elif isinstance(self.traj, TrajectoryCollection):
            return self._clean_traj_collection(**kwargs)
        else:
            raise TypeError

    def _clean_traj_collection(self, **kwargs):
        cleaned = []
        for traj in self.traj:
            cleaned.append(self._clean_traj(traj, **kwargs))
        result = copy(self.traj)
        result.trajectories = cleaned
        return result

    def _clean_traj(self, traj, **kwargs):
        return traj


class OutlierCleaner(TrajectoryCleaner):
    """
    Interquantile range (IQR) based outlier cleaner.

    Parameters
    ----------
    columns: dictionary
        Information regarding the columns that will be used to clean the trajectory
        and the accompanying thresholds. ex. - {'speed': 30, 'heading': 360} etc.

        Key-value pairs of columns and alpha (IQR multiplier).
        Note: Setting alpha=3 is widely used.

    Examples
    --------

    >>> mpd.OutlierCleaner(traj).clean(columns={'speed': 3})
    """

    def _clean_traj(self, traj, columns):
        df = traj.df.copy()
        ixs = []

        for column, alpha in columns.items():
            if not is_numeric_dtype(df[column]):
                raise TypeError(
                    f"'{column}' column of type '{df[column].dtype}' is not numeric"
                )
            ix = self._calc_outliers(df[column], alpha)
            ixs.append(ix.tolist())

        indices = pd.Series(list(map(any, zip(*ixs))), index=df.index)
        return Trajectory(df[~indices], traj.id)

    def _calc_outliers(self, series, alpha=3):
        """
        Returns a series of indexes of row that are to be considered outliers
        using the quantiles of the data.
        """
        q25, q75 = series.quantile((0.25, 0.75))
        iqr = q75 - q25
        q_high = q75 + alpha * iqr
        q_low = q25 - alpha * iqr
        # return the row indexes that are over/under the calculated threshold
        return (series > q_high) | (series < q_low)


class SpikeCleaner(TrajectoryCleaner):
    """
    Speed-based trajectory cleaner that cuts away spikes in the trajectory
    when the speed exceeds the provided speed threshold value

    Parameters
    ----------
    v_max: speed threshold
    units : tuple
        Units in which to calculate speed
        distance : str
            Abbreviation for the distance unit
            (default: CRS units, or metres if geographic)
        time : str
            Abbreviation for the time unit (default: seconds)

        Allowed distance units:
            "km": Kilometer
            "m": metre
            "dm": Decimeter
            "cm": Centimeter
            "mm": Millimeter
            "nm": International Nautical Mile
            "inch": International Inch
            "ft": International Foot
            "yd": International Yard
            "mi": International Statute Mile
            "link": International Link
            "chain": International Chain
            "fathom": International Fathom
            "british_ft": British foot (Sears 1922)
            "british_yd": British yard (Sears 1922)
            "british_chain_sears": British chain (Sears 1922)
            "british_link_sears": British link (Sears 1922)
            "sears_yd": Yard (Sears)
            "link_sears": Link (Sears)
            "chain_sears": Chain (Sears)
            "british_ft_sears_truncated": British foot (Sears 1922 truncated)
            "british_chain_sears_truncated": British chain (Sears 1922 truncated)
            "british_chain_benoit": British chain (Benoit 1895 B)
            "chain_benoit": Chain (Benoit)
            "link_benoit": Link (Benoit)
            "clarke_yd": Clarke's yard
            "clarke_ft": Clarke's Foot
            "clarke_link": Clarke's link
            "clarke_chain": Clarke's chain
            "british_ft_1936": British foot (1936)
            "gold_coast_ft": Gold Coast foot
            "rod": Rod
            "furlong": Furlong
            "german_m": German legal metre
            "survey_in": US survey inch
            "survey_ft": US survey foot
            "survey_yd": US survey yard
            "survey_lk": US survey link
            "survey_ch": US survey chain
            "survey_mi": US survey mile
            "indian_yd": Indian Yard
            "indian_ft": Indian Foot
            "indian_ft_1937": Indian Foot 1937
            "indian_ft_1962": Indian Foot 1962
            "indian_ft_1975": Indian Foot 1975

        Allowed time units:
            "s": seconds
            "min": minutes
            "h": hours
            "d": days
            "a": years

    Examples
    --------

    >>> mpd.SpikeCleaner(traj).clean(v_max=100, units=("km", "h"))
    """

    def _clean_traj(self, traj, v_max, units=UNITS()):
        ixs = []
        prev = None
        conversion = get_conversion(units, traj.crs_units)
        out_traj = traj.copy()

        for index, row in out_traj.df.iterrows():
            if not prev:
                prev = (index, row.geometry)
                continue
            func = (
                measure_distance_geodesic
                if traj.is_latlon
                else measure_distance_euclidean
            )
            d = func(prev[1], row.geometry) * conversion.crs / conversion.distance
            v = d / (index - prev[0]).total_seconds() * conversion.time
            if v > v_max:
                ixs.append(index)
                continue  # do NOT update the previous point
            prev = (index, row.geometry)

        out_traj.df.drop(ixs, inplace=True)
        return out_traj
