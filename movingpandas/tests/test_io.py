# -*- coding: utf-8 -*-
import json
import os

import pandas as pd
import pytest

from movingpandas.io import (
    _create_objects_from_mf_json_dict,
    gdf_to_mf_json,
    read_mf_json,
    read_mf_dict,
)


class TestIO:
    test_dir = os.path.dirname(os.path.realpath(__file__))

    def test_mf_file_movingpoint(self):
        traj = read_mf_json(os.path.join(self.test_dir, "movingfeatures.json"), "id")
        assert traj.id == "9569"
        assert traj.size() == 5
        actual = traj.df.columns
        expected = ["pressure", "wind", "class", "geometry", "id"]
        assert len(actual) == len(expected)
        assert all([a == b for a, b in zip(actual, expected)])
        actual = list(traj.df["pressure"])
        expected = [1004.0, 1004.0, 1004.0, 1004.0, 1000.0]
        assert actual == expected

    def test_mf_file_mftrajectory(self):
        traj = read_mf_json(
            os.path.join(self.test_dir, "mftrajectory.json"), traj_id=9569
        )
        assert traj.id == 9569
        assert traj.size() == 5
        actual = traj.df.columns
        expected = ["pressure", "wind", "class", "geometry", "traj_id"]
        assert len(actual) == len(expected)
        assert all([a == b for a, b in zip(actual, expected)])
        actual = list(traj.df["pressure"])
        expected = [1004.0, 1004.0, 1004.0, 1004.0, 1000.0]
        assert actual == expected

    def test_read_mf_dict(self):
        collection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": 5},
                    "temporalGeometry": {
                        "type": "MovingPoint",
                        "datetimes": ["2008-02-02T15:02:18Z", "2008-02-02T18:32:28Z"],
                        "coordinates": [[116.52299, 40.07757], [116.52302, 39.92129]],
                    },
                }
            ],
        }
        trajs_collection = read_mf_dict(collection, traj_id_property="id")

        assert len(trajs_collection) == 1
        assert trajs_collection.get_trajectory(5).id == 5

        traj = read_mf_dict(collection["features"][0], traj_id_property="id")

        assert traj.id == 5

    def test_mf_collection_file(self):
        trajs_collection = read_mf_json(
            os.path.join(self.test_dir, "movingfeatures_collection.json"), "id"
        )
        assert len(trajs_collection) == 2
        assert trajs_collection.get_trajectory(1).id == 1
        assert trajs_collection.get_trajectory(2).id == 2
        actual = list(trajs_collection.get_trajectory(2).df["pressure"])[:5]
        expected = [
            1008.0,
            1006.0,
            1006.0,
            1006.0,
            1006.0,
        ]
        assert actual == expected

    def test_mf_collection_needs_id(self):
        with pytest.raises(AssertionError):
            read_mf_json(
                os.path.join(self.test_dir, "movingfeatures_collection.json"), None
            )

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

    def test_invalid_feature_collection(self):
        data = {"type": "FeatureCollection", "temporalGeometry": []}
        with pytest.raises(ValueError):
            _create_objects_from_mf_json_dict(data, "id")

    def test_unsupported_geometry_type(self):
        data = {"type": "Feature", "temporalGeometry": {"type": "MovingPolygon"}}
        with pytest.raises(RuntimeError):
            _create_objects_from_mf_json_dict(data, "id")

    def test_gdf_to_mf_json(self):
        # Load a GeoDataFrame from a Moving-Features JSON file.
        loaded_gdf = read_mf_json(
            os.path.join(self.test_dir, "movingfeatures.json"), "id"
        ).df

        loaded_gdf["t"] = loaded_gdf.index
        loaded_gdf["id"] = "9569"

        # Convert the GeoDataFrame to a Moving-Features JSON dictionary.
        entity_mf_json = json.loads(
            json.dumps(
                gdf_to_mf_json(
                    loaded_gdf,
                    traj_id_column="id",
                    datetime_column="t",
                    datetime_encoder=lambda x: x.isoformat() + "Z",
                    temporal_columns=["wind", "pressure", "class"],
                    interpolation="Linear",
                    temporal_columns_static_fields={
                        "wind": {
                            "form": "KNT",
                            "interpolation": "Linear",
                            "type": "Measure",
                        },
                        "pressure": {
                            "form": "A97",
                            "interpolation": "Linear",
                            "type": "Measure",
                        },
                        "class": {"interpolation": "Linear", "type": "Measure"},
                    },
                )["features"][0]
            )
        )

        # Load the expected result from the original Moving-Features JSON file.
        with open(os.path.join(self.test_dir, "movingfeatures.json"), "r") as f:
            expected_mf_json = json.load(f)

        # Compare the expected and actual Moving-Features JSON dictionaries.
        assert entity_mf_json == expected_mf_json

    def test_not_geodataframe_raises_error(self):
        with pytest.raises(TypeError):
            gdf_to_mf_json(
                pd.DataFrame(),
                traj_id_column="id",
                datetime_column="t",
            )

    def test_missing_datetime_column_raises_error(self):
        with pytest.raises(TypeError):
            gdf_to_mf_json(
                pd.DataFrame(),
                traj_id_column="id",
            )

    def test_missing_traj_id_property_raises_error(self):
        with pytest.raises(TypeError):
            gdf_to_mf_json(
                pd.DataFrame(),
                datetime_column="t",
            )
