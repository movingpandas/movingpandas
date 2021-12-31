"""
`movingpandas`: Implementation of Trajectory classes and functions built on top of GeoPandas
"""

from .trajectory import Trajectory
from .trajectory_generalizer import TrajectoryGeneralizer, MaxDistanceGeneralizer, MinDistanceGeneralizer, \
    MinTimeDeltaGeneralizer, DouglasPeuckerGeneralizer, TopDownTimeRatioGeneralizer
from .trajectory_collection import TrajectoryCollection
from .trajectory_aggregator import TrajectoryCollectionAggregator
from .trajectory_splitter import TrajectorySplitter, TemporalSplitter, ObservationGapSplitter, SpeedSplitter, \
    StopSplitter
from .trajectory_stop_detector import TrajectoryStopDetector
from .point_clusterer import PointClusterer

name = 'movingpandas'
__version__ = '0.8.rc1'
