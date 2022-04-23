# -*- coding: utf-8 -*-

import os
import pytest
from movingpandas.io import read_mf_json, _create_objects_from_mf_json_dict


class TestIO:
    test_dir = os.path.dirname(os.path.realpath(__file__))

    def test_mf_file(self):
        traj = read_mf_json(os.path.join(self.test_dir, "movingfeatures.json"), "id")
        assert traj.id == "9569"
        assert traj.size() == 5
        actual = traj.df.columns
        expected = ["pressure", "wind", "class", "geometry"]
        assert len(actual) == len(expected)
        assert all([a == b for a, b in zip(actual, expected)])
        actual = list(traj.df["pressure"])
        expected = [1004.0, 1004.0, 1004.0, 1004.0, 1000.0]
        assert actual == expected

    def test_wrong_property_raises_error(self):
        with pytest.raises(ValueError):
            read_mf_json(os.path.join(self.test_dir, "movingfeatures.json"), "foo")

    def test_dict(self):
        data = {
            "type": "Feature",
            "properties": {"id": 5},
            "temporalGeometry": {
                "type": "MovingPoint",
                "datetimes": ["2008-02-02T15:02:18Z", "2008-02-02T18:32:28Z"],
                "coordinates": [[116.52299, 40.07757], [116.52302, 39.92129]],
            },
        }
        traj = _create_objects_from_mf_json_dict(data, "id")
        assert traj.id == 5
        assert traj.size() == 2

    def test_dict_without_id(self):
        data = {
            "type": "Feature",
            "temporalGeometry": {
                "type": "MovingPoint",
                "datetimes": ["2008-02-02T15:02:18Z", "2008-02-02T18:32:28Z"],
                "coordinates": [[116.52299, 40.07757], [116.52302, 39.92129]],
            },
        }
        traj = _create_objects_from_mf_json_dict(data)
        assert traj.id == 0
        assert traj.size() == 2

    def test_no_dict(self):
        data = []
        with pytest.raises(ValueError):
            _create_objects_from_mf_json_dict(data, "id")

    def test_unsupported_type(self):
        data = {"type": "FeatureCollection", "temporalGeometry": []}
        with pytest.raises(RuntimeError):
            _create_objects_from_mf_json_dict(data, "id")

    def test_unsupported_geometry_type(self):
        data = {"type": "Feature", "temporalGeometry": {"type": "MovingPolygon"}}
        with pytest.raises(RuntimeError):
            _create_objects_from_mf_json_dict(data, "id")
