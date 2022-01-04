"""
`movingpandas`: Implementation of Trajectory classes and functions built on top
of GeoPandas
"""

from .trajectory import Trajectory  # noqa F401
from .trajectory_generalizer import (  # noqa F401
    TrajectoryGeneralizer,
    MaxDistanceGeneralizer,
    MinDistanceGeneralizer,
    MinTimeDeltaGeneralizer,
    DouglasPeuckerGeneralizer,
)
from .trajectory_collection import TrajectoryCollection  # noqa F401
from .trajectory_aggregator import TrajectoryCollectionAggregator  # noqa F401
from .trajectory_splitter import (  # noqa F401
    TrajectorySplitter,
    TemporalSplitter,
    ObservationGapSplitter,
    SpeedSplitter,
    StopSplitter,
)
from .trajectory_stop_detector import TrajectoryStopDetector  # noqa F401
from .point_clusterer import PointClusterer  # noqa F401

name = "movingpandas"
__version__ = "0.8.rc1"
