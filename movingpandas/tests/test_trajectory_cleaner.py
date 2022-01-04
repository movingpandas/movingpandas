# -*- coding: utf-8 -*-

from .test_trajectory import make_traj, Node
from movingpandas.trajectory_cleaner import OutlierCleaner


class TestTrajectoryCleaner:
    def test_outlier_cleaner(self):
        traj = make_traj(
            [
                Node(),
                Node(1, 0.1, day=1, value=1),
                Node(2, 0.2, day=2, value=3),
                Node(3, 0, day=3, value=10),
                Node(3, 3, day=4, value=2),
                Node(4, 3, day=5, value=1),
                Node(5, 5, day=6, value=1),
            ]
        )
        result = OutlierCleaner(traj).clean(features={"value": 3})
        assert result == make_traj(
            [
                Node(),
                Node(1, 0.1, day=1, value=1),
                Node(2, 0.2, day=2, value=3),
                Node(3, 3, day=4, value=2),
                Node(4, 3, day=5, value=1),
                Node(5, 5, day=6, value=1),
            ]
        )
