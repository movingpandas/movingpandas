"""
`movingpandas`: Implementation of Trajectory classes and functions built on top of GeoPandas
"""

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection
from .trajectory_plotter import TrajectoryPlotter
from .trajectory_sampler import TrajectorySampler, TrajectoryCollectionSampler
from .trajectory_predictor import TrajectoryPredictor
from .trajectory_prediction_evaluator import TrajectoryPredictionEvaluator

name = 'movingpandas'
__version__ = '0.1.dev2'
