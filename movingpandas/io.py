import json

from pandas import DataFrame

from movingpandas import Trajectory


def read_mf_json(json_file_path, traj_id_property):
    """
    Reads OGC Moving Features Encoding Extension JSON files.
    MovingFeatures files are turned into Trajectory objects.
    MovingFeatureCollection files are turned into TrajectoryCollection objects.
    More info: http://www.opengis.net/doc/BP/mf-json/1.0

    Parameters
    ----------
    json_file_path : str
        Path to the JSON file
    traj_id_property : str
        Name of the property to be used as trajectory ID

    Returns
    -------
    Trajectory or TrajectoryCollection
    """
    with open(json_file_path, "r") as f:
        data = json.loads(f.read())
    return _create_objects_from_mf_json_dict(data, traj_id_property)


def _create_objects_from_mf_json_dict(data, traj_id_property):
    if not isinstance(data, dict):
        raise ValueError("Not a supported MovingFeatures JSON")
    if not ("type" in data and "temporalGeometry" in data):
        raise ValueError("Not a supported MovingFeatures JSON")
    if data["type"] == "MovingFeature":
        return _create_traj_from_movingfeature_json(data, traj_id_property)
    elif data["type"] == "MovingFeatureCollection":
        return _create_trajcollection_from_movingfeaturecollection_json(data)
    else:
        raise ValueError(
            f"Not a supported MovingFeatures JSON: "
            f"expected MovingFeature or MovingFeatureCollection"
            f"but got {data['type']}"
        )


def _create_traj_from_movingfeature_json(data, traj_id_property):
    if data["temporalGeometry"]["type"] != "MovingPoint":
        raise RuntimeError(
            f"Not a supported MovingFeatures JSON: "
            f"temporalGeometry type must be MovingPoint "
            f"(but is {data['temporalGeometry']['type']}"
        )
    try:
        traj_id = data["properties"][traj_id_property]
    except KeyError:
        raise ValueError(
            f"No property '{traj_id_property}'. "
            f"Available properties are: {data['properties'].keys()}"
        )
    t = data["temporalGeometry"]["datetimes"]
    x, y = map(list, zip(*data["temporalGeometry"]["coordinates"]))
    df = DataFrame(list(zip(t, x, y)), columns=["t", "x", "y"])
    return Trajectory(df, traj_id, t="t", x="x", y="y")


def _create_trajcollection_from_movingfeaturecollection_json(data):
    raise RuntimeError("MovingFeatureCollection support is not available yet.")
