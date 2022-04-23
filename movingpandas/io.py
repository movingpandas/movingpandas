import json

from pandas import DataFrame

from movingpandas import Trajectory


def read_mf_json(json_file_path, traj_id_property=None, traj_id=0):
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
        Name of the MovingFeature JSON property to be used as trajectory ID
    traj_id : any
        Trajectory ID value to be used if no traj_id_property is supplied

    Returns
    -------
    Trajectory or TrajectoryCollection
    """
    with open(json_file_path, "r") as f:
        data = json.loads(f.read())
    return _create_objects_from_mf_json_dict(data, traj_id_property, traj_id)


def _create_objects_from_mf_json_dict(data, traj_id_property=None, traj_id=0):
    if not isinstance(data, dict):
        raise ValueError("Not a supported MovingFeatures JSON")
    if not ("type" in data and "temporalGeometry" in data):
        raise ValueError("Not a supported MovingFeatures JSON")
    if data["type"] == "Feature":
        return _create_traj_from_movingfeature_json(data, traj_id_property, traj_id)
    elif data["type"] == "FeatureCollection":
        return _create_trajcollection_from_movingfeaturecollection_json(data)
    else:
        raise ValueError(
            f"Not a supported MovingFeatures JSON: "
            f"expected Feature or FeatureCollection"
            f"but got {data['type']}"
        )


def _create_geometry(data):
    if data["temporalGeometry"]["type"] != "MovingPoint":
        raise RuntimeError(
            f"Not a supported MovingFeatures JSON: "
            f"temporalGeometry type must be MovingPoint "
            f"(but is {data['temporalGeometry']['type']}"
        )
    t = data["temporalGeometry"]["datetimes"]
    x, y = map(list, zip(*data["temporalGeometry"]["coordinates"]))
    return DataFrame(list(zip(t, x, y)), columns=["t", "x", "y"])


def _get_id_property_value(data, traj_id_property):
    try:
        return data["properties"][traj_id_property]
    except KeyError:
        raise ValueError(
            f"No property '{traj_id_property}'. "
            f"Available properties are: {data['properties'].keys()}"
        )


def _get_temporal_properties(data):
    cols = []
    props = []
    for key, values in data.items():
        if key == "datetimes":
            cols.append("t")
            props.append(values)
        else:
            cols.append(key)
            props.append(values["values"])
    transposed = [list(i) for i in zip(*props)]
    return DataFrame(transposed, columns=cols)


def _create_traj_from_movingfeature_json(data, traj_id_property, traj_id):
    df = _create_geometry(data)
    if traj_id_property:
        traj_id = _get_id_property_value(data, traj_id_property)
    if "temporalProperties" in data:
        for property_group in data["temporalProperties"]:
            df.set_index("t", inplace=True)
            df = df.join(_get_temporal_properties(property_group).set_index("t"))
            df["t"] = df.index
    return Trajectory(df, traj_id, t="t", x="x", y="y")


def _create_trajcollection_from_movingfeaturecollection_json(data):
    raise RuntimeError("MovingFeatureCollection support is not available yet.")
