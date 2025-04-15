import json
from typing import Callable, Dict

from geopandas import GeoDataFrame
from pandas import DataFrame


def _datetime_to_string(dt, format="%Y-%m-%d %H:%M:%S"):
    return dt.strftime(format)


def gdf_to_mf_json(
    gdf: GeoDataFrame,
    traj_id_column: str,
    datetime_column: str,
    temporal_columns: list = None,
    temporal_columns_static_fields: Dict[str, Dict] = None,
    interpolation: str = None,
    crs=None,
    trs=None,
    datetime_encoder: Callable = None,
    datetime_to_str: bool = False,
    # simplified typing hint due to https://github.com/movingpandas/movingpandas/issues/345  # noqa F401
) -> dict:
    """
    Converts a GeoDataFrame to a dictionary compatible with the Moving Features JSON
    (MF-JSON) specification.

    Args:
        gdf (GeoDataFrame): The input GeoDataFrame to convert.
        traj_id_column (str): The name of the column in the GeoDataFrame that
            represents the trajectory identifier.
        datetime_column (str): The name of the column in the GeoDataFrame that
            represents the datetime information.
        temporal_columns (list, optional): A list of column names in the GeoDataFrame
         that represent additional temporal properties. Defaults to None.
        temporal_columns_static_fields (Dict[str, Dict], optional): A dictionary mapping
            column names to static fields associated with the corresponding temporal
            property. Defaults to None.
        interpolation (str, optional): The interpolation method used for the temporal
            geometry. Defaults to None.
        crs (optional): Coordinate reference system for the MF-JSON. Defaults to None.
        trs (optional): Temporal reference system for the MF-JSON. Defaults to None.
        datetime_encoder (Callable[[any], str|int], optional): A function that encodes
            the datetime values in the GeoDataFrame to a string ( IETF RFC 3339 ) or
            integer ( Timestamp, milliseconds ). Defaults to None.
    Returns:
        dict: The MF-JSON representation of the GeoDataFrame as a dictionary.
    """

    _raise_error_if_invalid_arguments(gdf, datetime_column, traj_id_column)

    if not temporal_columns:
        temporal_columns = []

    rows = []

    if datetime_to_str:
        datetime_encoder = _datetime_to_string

    for identifier, row in gdf.groupby(traj_id_column):
        datetimes = _retrieve_datetimes_from_row(datetime_column, datetime_encoder, row)

        properties = row.drop(
            columns=[
                "geometry",
                datetime_column,
                traj_id_column,
                *temporal_columns,
            ]
        )

        if properties.empty:
            encoded_properties = {}
        else:
            encoded_properties = properties.to_dict(orient="records")[0]

        trajectory_data = {
            "type": "Feature",
            "properties": {
                traj_id_column: identifier,
                **encoded_properties,
            },
            "temporalGeometry": {
                "type": "MovingPoint",
                "coordinates": list(zip(row.geometry.x, row.geometry.y)),
                "datetimes": datetimes,
            },
        }

        if interpolation:
            trajectory_data["temporalGeometry"]["interpolation"] = interpolation

        if crs:
            trajectory_data["crs"] = crs

        if trs:
            trajectory_data["trs"] = trs

        if temporal_columns:
            temporal_properties_data = _encode_temporal_properties(
                datetimes, row, temporal_columns, temporal_columns_static_fields
            )

            trajectory_data["temporalProperties"] = [temporal_properties_data]

        # Appending each trajectory data to the list of rows
        rows.append(trajectory_data)

    return {"type": "FeatureCollection", "features": rows}


def _raise_error_if_invalid_arguments(
    gdf: GeoDataFrame, datetime_column: str, traj_id_property: str
):
    if not isinstance(gdf, GeoDataFrame):
        raise TypeError(
            "Not a GeoDataFrame, but a {} was supplied. This function only works with"
            " GeoDataFrames.".format(type(gdf))
        )
    # Check if both datetime_column and trip_id_property are in the GeoDataFrame
    if datetime_column not in gdf.columns:
        raise ValueError(
            f"The datetime_column {datetime_column} is not in the GeoDataFrame."
        )
    if traj_id_property not in gdf.columns:
        raise ValueError(
            f"The traj_id_property {traj_id_property} is not in the GeoDataFrame."
        )


def _retrieve_datetimes_from_row(datetime_column, datetime_encoder, row):
    datetimes = row[datetime_column].tolist()
    if datetime_encoder:
        datetimes = [datetime_encoder(dt) for dt in datetimes]
    return datetimes


def _encode_temporal_properties(
    datetimes, row, temporal_properties, temporal_properties_static_fields
):
    temporal_properties_data = {
        "datetimes": datetimes,
    }
    for prop in temporal_properties:
        temporal_properties_data[prop] = {
            "values": row[prop].tolist(),
        }
        if prop in (temporal_properties_static_fields or {}):
            temporal_properties_data[prop].update(
                temporal_properties_static_fields[prop]
            )
    return temporal_properties_data


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
    return read_mf_dict(data, traj_id, traj_id_property)


def read_mf_dict(data: dict, traj_id=0, traj_id_property=None):
    """
    Reads OGC Moving Features Encoding Extension JSON files from a dictionary.
    MovingFeatures files are turned into Trajectory objects.
    MovingFeatureCollection files are turned into TrajectoryCollection objects.
    More info: http://www.opengis.net/doc/BP/mf-json/1.0

    data : dict
        JSON data as a dictionary
    traj_id_property : str
        Name of the MovingFeature JSON property to be used as trajectory ID
    traj_id : any
        Trajectory ID value to be used if no traj_id_property is supplied

    Returns
    """
    return _create_objects_from_mf_json_dict(data, traj_id_property, traj_id)


def _create_objects_from_mf_json_dict(data, traj_id_property=None, traj_id=0):
    if not isinstance(data, dict):
        raise ValueError("Not a supported MovingFeatures JSON")
    if data["type"] == "Feature" and "temporalGeometry" in data:
        return _create_traj_from_mfjson_movingpoint(data, traj_id_property, traj_id)
    elif data["type"] == "Feature" and "geometry" in data:
        return _create_traj_from_mfjson_trajectory(data, traj_id_property, traj_id)
    elif data["type"] == "FeatureCollection" and "features" in data:
        return _create_tc_from_mfcollection_json(data, traj_id_property)
    else:
        raise ValueError(
            f"Not a supported MovingFeatures JSON: "
            f"expected Feature or FeatureCollection "
            f"but got {data['type']}"
        )


def _get_id_property_value(data, traj_id_property):
    try:
        return data["properties"][traj_id_property]
    except KeyError:
        raise ValueError(
            f"No property '{traj_id_property}'. "
            f"Available properties are: {data['properties'].keys()}"
        )


def _create_geometry_from_linestring(data):
    if data["geometry"]["type"] == "LineString":
        t = data["properties"]["datetimes"]
        x, y = map(list, zip(*data["geometry"]["coordinates"]))
        return DataFrame(list(zip(t, x, y)), columns=["t", "x", "y"])
    else:
        raise RuntimeError(
            f"Not a supported MovingFeatures JSON: "
            f"geometry type must be LineString "
            f"(but is {data['geometry']['type']}"
        )


def _add_properties(df, data):
    # https://docs.ogc.org/is/19-045r3/19-045r3.html#_mf_json_trajectory_encoding

    for property_name, values in data["properties"].items():
        if len(values) == len(df):
            # The array of a time-varying attribute with linear interpolation
            # has elements with the same number of positions of the "datetimes"
            # member; and
            if property_name != "datetimes":
                df[property_name] = values
        elif len(values) == len(df) - 1:
            # The array of a time-varying attribute with step interpolation
            # has elements with one less than the number of positions of the
            # "datetimes" member;
            values.append(values[-1])
            df[property_name] = values
        elif len(values) == 1:
            # The array of a fixed attribute during the whole of "datetimes"
            # has only one element.
            df[property_name] = values[0]
        else:
            pass

    return df


def _create_traj_from_mfjson_trajectory(data, traj_id_property, traj_id):
    from movingpandas import Trajectory

    df = _create_geometry_from_linestring(data)

    if "properties" in data:
        df = _add_properties(df, data)

    traj = Trajectory(df, traj_id, t="t", x="x", y="y")
    traj.populate_geometry_column()
    return traj


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


def _create_geometry_from_movingpoint(data):
    if data["temporalGeometry"]["type"] == "MovingPoint":
        t = data["temporalGeometry"]["datetimes"]
        x, y = map(list, zip(*data["temporalGeometry"]["coordinates"]))
        return DataFrame(list(zip(t, x, y)), columns=["t", "x", "y"])
    else:
        raise RuntimeError(
            f"Not a supported MovingFeatures JSON: "
            f"temporalGeometry type must be MovingPoint "
            f"(but is {data['temporalGeometry']['type']}"
        )


def _create_traj_from_mfjson_movingpoint(data, traj_id_property, traj_id):
    from movingpandas import Trajectory

    df = _create_geometry_from_movingpoint(data)
    if traj_id_property:
        traj_id = _get_id_property_value(data, traj_id_property)
    if "temporalProperties" in data:
        for property_group in data["temporalProperties"]:
            df.set_index("t", inplace=True)
            df = df.join(_get_temporal_properties(property_group).set_index("t"))
            df["t"] = df.index
    traj = Trajectory(df, traj_id, t="t", x="x", y="y", traj_id_col=traj_id_property)
    traj.populate_geometry_column()
    return traj


def _create_tc_from_mfcollection_json(data, traj_id_property):
    from movingpandas import TrajectoryCollection

    assert (
        traj_id_property is not None
    ), "traj_id_property must be supplied when reading a collection of trajectories"

    trajectories = []
    for feature in data["features"]:
        trajectories.append(
            _create_traj_from_mfjson_movingpoint(feature, traj_id_property, None)
        )

    return TrajectoryCollection(trajectories)
