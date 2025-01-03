# -*- coding: utf-8 -*-

import warnings

import pandas as pd
from pandas.api.types import is_numeric_dtype

from copy import copy

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .unit_utils import UNITS, get_conversion
from .spatiotemporal_utils import TPoint, get_speed


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


class IqrCleaner(TrajectoryCleaner):
    """
    Interquantile range (IQR) based outlier cleaner.

    Parameters
    ----------
    columns: dictionary
        Information regarding the columns that will be used to clean the trajectory
        and the accompanying thresholds.

        Key-value pairs of columns and alpha (IQR multiplier).
        Note: Setting alpha=3 is widely used.

    Examples
    --------

    >>> mpd.IqrCleaner(traj).clean(columns={'speed': 3})
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
        return Trajectory(df[~indices], traj.id, traj_id_col=traj.get_traj_id_col())

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


class OutlierCleaner(TrajectoryCleaner):
    """
    Speed-based outlier cleaner that cuts away spikes in the trajectory
    when the speed exceeds the provided speed threshold value

    Parameters
    ----------
    v_max : numeric
        Speed threshold
    units : tuple
        Units in which to calculate speed
        For more info, check the list of supported units at
        https://movingpandas.org/units

    Examples
    --------

    >>> mpd.OutlierCleaner(traj).clean(alpha=2)

    >>> mpd.OutlierCleaner(traj).clean(v_max=100, units=("km", "h"))
    """

    def _clean_traj(self, traj, v_max=None, units=UNITS(), alpha=3):
        out_traj = traj.copy()
        conversion = get_conversion(units, traj.crs_units)

        if v_max is None:
            out_traj.add_speed(overwrite=True, units=units)
            speed_col = out_traj.get_speed_col()
            v_max = out_traj.df[speed_col].agg(lambda x: x.quantile(0.95))
            v_max = v_max * alpha

        ixs = []
        prev = None
        for index, row in out_traj.df.iterrows():
            curr = TPoint(index, row.geometry)
            if not prev:
                prev = curr
                continue

            v = get_speed(prev, curr, traj.is_latlon, conversion)
            if v > v_max:
                ixs.append(index)
                continue  # do NOT update the previous point
            prev = curr

        out_traj.df.drop(ixs, inplace=True)

        if not out_traj.is_valid():
            warnings.warn(
                f"Cleaning failed for trajectory {out_traj.id} "
                "due to invalid result (e.g. <2 points remaining). "
                "Returning original trajectory.",
                UserWarning,
            )
            out_traj = traj.copy()

        return out_traj
