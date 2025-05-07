"""
`movingpandas`: Implementation of Trajectory classes and functions built on top
of GeoPandas
"""

import warnings


from .trajectory import Trajectory  # noqa F401
from .trajectory_generalizer import (  # noqa F401
    TrajectoryGeneralizer,
    MaxDistanceGeneralizer,
    MinDistanceGeneralizer,
    MinTimeDeltaGeneralizer,
    DouglasPeuckerGeneralizer,
    TopDownTimeRatioGeneralizer,
)
from .trajectory_collection import TrajectoryCollection  # noqa F401
from .io import read_mf_json, read_mf_dict, gdf_to_mf_json  # noqa F401
from .trajectory_aggregator import (  # noqa F401
    TrajectoryCollectionAggregator,
    PtsExtractor,
)
from .trajectory_splitter import (  # noqa F401
    TrajectorySplitter,
    TemporalSplitter,
    ObservationGapSplitter,
    SpeedSplitter,
    StopSplitter,
    AngleChangeSplitter,
    ValueChangeSplitter,
)
from .trajectory_cleaner import IqrCleaner, OutlierCleaner  # noqa F401
from .trajectory_stop_detector import TrajectoryStopDetector  # noqa F401
from .point_clusterer import PointClusterer  # noqa F401
from .tools._show_versions import show_versions  # noqa F401

try:
    from .trajectory_smoother import KalmanSmootherCV  # noqa F401
except ImportError as e:
    warnings.warn(e.msg, UserWarning)

name = "movingpandas"
__version__ = "0.22.0"
