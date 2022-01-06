# -*- coding: utf-8 -*-

import pandas as pd
from pandas.api.types import is_numeric_dtype

from copy import copy

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection


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

    def clean(self, columns):
        """
        Clean the input Trajectory/TrajectoryCollection.

        Parameters
        ----------
        columns: dictionary
            Information regarding the columns that will be used to clean the trajectory
            and the accompanying thresholds. ex. - {'speed': 30, 'heading': 360} etc.

        Returns
        -------
        Trajectory/TrajectoryCollection
            Cleaned Trajectory or TrajectoryCollection
        """
        if isinstance(self.traj, Trajectory):
            return self._clean_traj(self.traj, columns)
        elif isinstance(self.traj, TrajectoryCollection):
            return self._clean_traj_collection(columns)
        else:
            raise TypeError

    def _clean_traj_collection(self, columns):
        cleaned = []
        for traj in self.traj:
            cleaned.append(self._clean_traj(traj, columns))
        result = copy(self.traj)
        result.trajectories = cleaned
        return result

    def _clean_traj(self, traj, columns):
        return traj


class OutlierCleaner(TrajectoryCleaner):
    """
    Outlier (interquantile range - iqr) based cleaner.

    columns : dictionary
        Key - value pairs of columns and alpha (iqr multiplier).

        Note: Setting alpha=3 is widely used.

    Examples
    --------

    >>> mpd.OutlierCleaner(traj).clean({'speed': 3})
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
        # return the indexes of rows that are over/under the calculated threshold
        return (series > q_high) | (series < q_low)
