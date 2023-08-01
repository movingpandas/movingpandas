from copy import copy
from abc import ABC, abstractmethod

import numpy as np
from shapely.geometry import Point

try:
    from stonesoup.types.detection import Detection
    from stonesoup.models.transition.linear import (
        CombinedLinearGaussianTransitionModel,
        ConstantVelocity,
    )
    from stonesoup.models.measurement.linear import LinearGaussian
    from stonesoup.predictor.kalman import KalmanPredictor
    from stonesoup.updater.kalman import KalmanUpdater
    from stonesoup.types.array import CovarianceMatrix, StateVector
    from stonesoup.types.prediction import GaussianStatePrediction
    from stonesoup.initiator.simple import SimpleMeasurementInitiator
    from stonesoup.types.hypothesis import SingleHypothesis
    from stonesoup.smoother.kalman import KalmanSmoother
    from stonesoup.reader.base import DetectionReader
    from stonesoup.base import Property
    from stonesoup.buffered_generator import BufferedGenerator
except ImportError as error:
    raise ImportError(
        "Missing optional dependencies. To use the trajectory smoother classes please "
        "install Stone Soup "
        "(see https://stonesoup.readthedocs.io/en/latest/#installation)."
    ) from error

from .trajectory import Trajectory
from .trajectory_collection import TrajectoryCollection


class TrajectorySmoother(ABC):
    """
    TrajectorySmoother base class

    Base class for trajectory smoothers. This class is abstract and thus cannot be
    instantiated.
    """

    def __init__(self, traj):
        """
        Create TrajectorySmoother

        Parameters
        ----------
        traj : Trajectory or TrajectoryCollection
        """
        self.traj = traj

    def smooth(self, **kwargs):
        """
        Smooth the input Trajectory/TrajectoryCollection

        Parameters
        ----------
        kwargs : any type
            Keyword arguments, differs by smoother

        Returns
        -------
        Trajectory/TrajectoryCollection
            Smoothed Trajectory or TrajectoryCollection

        """
        if isinstance(self.traj, Trajectory):
            return self._smooth_traj(self.traj, **kwargs)
        elif isinstance(self.traj, TrajectoryCollection):
            return self._smooth_traj_collection(**kwargs)
        else:
            raise TypeError

    def _smooth_traj_collection(self, **kwargs):
        smoothed = []
        for traj in self.traj:
            smoothed.append(self._smooth_traj(traj, **kwargs))
        result = copy(self.traj)
        result.trajectories = smoothed
        return result

    @abstractmethod
    def _smooth_traj(self, traj, **kwargs):
        raise NotImplementedError


class KalmanSmootherCV(TrajectorySmoother):
    """
    Smooths using a Kalman Filter with a Constant Velocity model.

    The Constant Velocity model assumes that the speed between consecutive locations is
    nearly constant. For trajectories where ``traj.is_latlon = True`` the smoother
    converts to EPSG:3395 (World Mercator) internally to perform filtering and smoothing

    .. note::
        This class makes use of
        `Stone Soup <https://stonesoup.readthedocs.io/en/latest/>`_, which is an
        optional dependency and not installed by default. To use this class, you need
        to install Stone Soup directly
        (see `here <https://stonesoup.readthedocs.io/en/latest/#installation>`_).
    """

    def smooth(self, process_noise_std=0.5, measurement_noise_std=1):
        """
        Smooth the input Trajectory/TrajectoryCollection

        Parameters
        ----------
        process_noise_std: float or sequence of floats of length 2, default is 0.5.
            The process (acceleration) noise standard deviation.

            If a sequence (e.g. list, tuple, etc.) is provided, the first index is used
            for the x coordinate, while the second is used for the y coordinate. If
            ``traj.is_latlon=True`` the values are applied to the  easting and northing
            coordinate (in EPSG:3395) respectively.

            Alternatively, a single float can be provided, which is assumed to be the
            same for both coordinates.

            This governs the uncertainty associated with the adherence of the new
            (smooth) trajectories to the CV model assumption; higher values relax
            the assumption, therefore leading to less-smooth trajectories,
            and vice-versa.

        measurement_noise_std: float or sequence of floats of length 2, default is 1.
            The measurement noise standard deviation.

            If a sequence (e.g. list, tuple, etc.) is provided, the first index is used
            for the x coordinate, while the second is used for the y coordinate. If
            ``traj.is_latlon=True`` the values are applied to the  easting and northing
            coordinate (in EPSG:3395) respectively.

            Alternatively, a single float can be provided, which is assumed to be the
            same for both coordinates.

            This controls the assumed error in the original trajectories; higher values
            dictate that the original trajectories are expected to be noisier
            (and therefore, less reliable), thus leading to smoother trajectories,
            and vice-versa.
        """
        return super().smooth(
            process_noise_std=process_noise_std,
            measurement_noise_std=measurement_noise_std,
        )

    def _smooth_traj(self, traj, process_noise_std=0.5, measurement_noise_std=1):
        # Get detector
        detector = self._get_detector(traj)

        # Models
        if not isinstance(process_noise_std, (list, tuple, np.ndarray)):
            process_noise_std = [process_noise_std, process_noise_std]
        if not isinstance(measurement_noise_std, (list, tuple, np.ndarray)):
            measurement_noise_std = [measurement_noise_std, measurement_noise_std]
        transition_model = CombinedLinearGaussianTransitionModel(
            [
                ConstantVelocity(process_noise_std[0] ** 2),
                ConstantVelocity(process_noise_std[1] ** 2),
            ]
        )
        measurement_model = LinearGaussian(
            ndim_state=4,
            mapping=[0, 2],
            noise_covar=np.diag(
                [measurement_noise_std[0] ** 2, measurement_noise_std[1] ** 2]
            ),
        )
        # Predictor and updater
        predictor = KalmanPredictor(transition_model)
        updater = KalmanUpdater(measurement_model)
        # Initiator
        state_vector = StateVector([0.0, 0.0, 0.0, 0.0])
        covar = CovarianceMatrix(np.diag([0.0, 0.0, 0.0, 0.0]))
        prior_state = GaussianStatePrediction(state_vector, covar)
        initiator = SimpleMeasurementInitiator(prior_state, measurement_model)
        # Filtering
        track = None
        for i, (timestamp, detections) in enumerate(detector):
            if i == 0:
                tracks = initiator.initiate(detections, timestamp)
                track = tracks.pop()
            else:
                detection = detections.pop()
                prediction = predictor.predict(track.state, timestamp=timestamp)
                hypothesis = SingleHypothesis(prediction, detection)
                posterior = updater.update(hypothesis)
                track.append(posterior)
        # Smoothing
        smoother = KalmanSmoother(transition_model)
        smooth_track = smoother.smooth(track)

        # Create new trajectory
        if traj.is_latlon:
            df = traj.df.to_crs("EPSG:3395")
            df.geometry = [
                Point(state.state_vector[0], state.state_vector[2])
                for state in smooth_track
            ]
            df.to_crs(traj.crs, inplace=True)
        else:
            df = traj.df.copy()
            df.geometry = [
                Point(state.state_vector[0], state.state_vector[2])
                for state in smooth_track
            ]
        new_traj = Trajectory(df, traj.id, traj_id_col=traj.get_traj_id_col())
        return new_traj

    @staticmethod
    def _get_detector(traj):
        class Detector(DetectionReader):
            trajectory: Trajectory = Property(doc="")

            @BufferedGenerator.generator_method
            def detections_gen(self):
                detections_df = traj.df.loc[:, "geometry"].to_frame()
                if traj.is_latlon:
                    detections_df.to_crs("EPSG:3395", inplace=True)
                detections_df["x"] = [
                    row.geometry.coords[0][0] for _, row in detections_df.iterrows()
                ]
                detections_df["y"] = [
                    row.geometry.coords[0][1] for _, row in detections_df.iterrows()
                ]
                detections_df.drop(columns="geometry", inplace=True)
                for time, row in detections_df.iterrows():
                    detection = Detection([row.x, row.y], timestamp=time)
                    yield time, {detection}

        return Detector(traj)
