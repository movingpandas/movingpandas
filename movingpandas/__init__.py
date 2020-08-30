"""
`movingpandas`: Implementation of Trajectory classes and functions built on top of GeoPandas
"""

from .trajectory import Trajectory
from .trajectory_generalizer import TrajectoryGeneralizer, MaxDistanceGeneralizer, MinDistanceGeneralizer, \
    MinTimeDeltaGeneralizer, DouglasPeuckerGeneralizer
from .trajectory_collection import TrajectoryCollection
from .trajectory_aggregator import TrajectoryCollectionAggregator
from .trajectory_splitter import TrajectorySplitter, TemporalSplitter, ObservationGapSplitter, SpeedSplitter

name = 'movingpandas'
__version__ = '0.5.rc1'
