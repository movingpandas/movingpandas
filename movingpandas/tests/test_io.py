# -*- coding: utf-8 -*-

import pytest
from movingpandas.io import read_mf_json, _create_objects_from_mf_json_dict


class TestIO:
    def test_mf_file(self):
        traj = read_mf_json("movingfeatures.json", "id")
        assert traj.id == "9569"
        assert traj.size() == 5

    def test_wrong_property_raises_error(self):
        with pytest.raises(ValueError):
            read_mf_json("movingfeatures.json", "wrong id property")

    def test_dict(self):
        data = {
            "type": "MovingFeature",
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

    def test_no_dict(self):
        data = []
        with pytest.raises(ValueError):
            _create_objects_from_mf_json_dict(data, "id")

    def test_unsupported_type(self):
        data = {"type": "MovingFeatureCollection", "temporalGeometry": []}
        with pytest.raises(RuntimeError):
            _create_objects_from_mf_json_dict(data, "id")

    def test_unsupported_geometry_type(self):
        data = {"type": "MovingFeature", "temporalGeometry": {"type": "MovingPolygon"}}
        with pytest.raises(RuntimeError):
            _create_objects_from_mf_json_dict(data, "id")
