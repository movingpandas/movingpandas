import warnings

from collections import namedtuple
from datetime import datetime


UNITS = namedtuple(
    "UNITS", "distance time time2 crs", defaults=(None, None, None, None)
)


DISTANCE_UNIT_LIST = [
    {"abbr": "km", "conv": 1000, "fullname": "Kilometer"},
    {"abbr": "m", "conv": 1, "fullname": "metre"},
    {"abbr": "dm", "conv": 0.1, "fullname": "Decimeter"},
    {"abbr": "cm", "conv": 0.01, "fullname": "Centimeter"},
    {"abbr": "mm", "conv": 0.001, "fullname": "Millimeter"},
    {"abbr": "nm", "conv": 1852.0, "fullname": "International Nautical Mile"},
    {"abbr": "inch", "conv": 0.0254, "fullname": "International Inch"},
    {"abbr": "ft", "conv": 0.3048, "fullname": "International Foot"},
    {"abbr": "yd", "conv": 0.9144, "fullname": "International Yard"},
    {"abbr": "mi", "conv": 1609.344, "fullname": "International Statute Mile"},
    {"abbr": "link", "conv": 0.201168, "fullname": "International Link"},
    {"abbr": "chain", "conv": 20.1168, "fullname": "International Chain"},
    {"abbr": "fathom", "conv": 1.8288, "fullname": "International Fathom"},
    {
        "abbr": "british_ft",
        "conv": 0.304799471538676,
        "fullname": "British foot (Sears 1922)",
        "epsg": 9041,
    },
    {
        "abbr": "british_yd",
        "conv": 0.914398414616029,
        "fullname": "British yard (Sears 1922)",
        "epsg": 9040,
    },
    {
        "abbr": "british_chain_sears",
        "conv": 20.11677651215526,
        "fullname": "British chain (Sears 1922)",
        "epsg": 9042,
    },
    {
        "abbr": "british_link_sears",
        "conv": 0.20116767651215526,
        "fullname": "British link (Sears 1922)",
        "epsg": 9043,
    },
    {"abbr": "sears_yd", "conv": 0.914398414616029, "fullname": "Yard (Sears)"},
    {"abbr": "link_sears", "conv": 0.20116767651215526, "fullname": "Link (Sears)"},
    {"abbr": "chain_sears", "conv": 20.11677651215526, "fullname": "Chain (Sears)"},
    {
        "abbr": "british_ft_sears_truncated",
        "conv": 0.914398,
        "fullname": "British foot (Sears 1922 truncated)",
        "epsg": 9300,
    },
    {
        "abbr": "british_chain_sears_truncated",
        "conv": 20.11676,
        "fullname": "British chain (Sears 1922 truncated)",
        "epsg": 9301,
    },
    {
        "abbr": "british_chain_benoit",
        "conv": 20.116782494375872,
        "fullname": "British chain (Benoit 1895 B)",
        "epsg": 9062,
    },
    {
        "abbr": "chain_benoit",
        "conv": 20.116782494375872,
        "fullname": "Chain (Benoit)",
        "epsg": 9062,
    },
    {
        "abbr": "link_benoit",
        "conv": 0.20116782494375872,
        "fullname": "Link (Benoit)",
        "epsg": 9063,
    },
    {
        "abbr": "clarke_yd",
        "conv": 0.9143917962,
        "fullname": "Clarke's yard",
        "epsg": 9037,
    },
    {
        "abbr": "clarke_ft",
        "conv": 0.3047972654,
        "fullname": "Clarke's Foot",
        "epsg": 9005,
    },
    {
        "abbr": "clarke_link",
        "conv": 0.201166195164,
        "fullname": "Clarke's link",
        "epsg": 9039,
    },
    {
        "abbr": "clarke_chain",
        "conv": 20.1166195164,
        "fullname": "Clarke's chain",
        "epsg": 9038,
    },
    {
        "abbr": "british_ft_1936",
        "conv": 0.3048007491,
        "fullname": "British foot (1936)",
        "epsg": 9095,
    },
    {
        "abbr": "gold_coast_ft",
        "conv": 0.3047997101815,
        "fullname": "Gold Coast foot",
        "epsg": 9094,
    },
    {"abbr": "rod", "conv": 0.1988387815, "fullname": "Rod"},
    {"abbr": "furlong", "conv": 201.168, "fullname": "Furlong"},
    {
        "abbr": "german_m",
        "conv": 1.0000135965,
        "fullname": "German legal metre",
        "epsg": 9031,
    },
    {"abbr": "survey_in", "conv": 0.0254000508001016, "fullname": "US survey inch"},
    {
        "abbr": "survey_ft",
        "conv": 0.3048006096012192,
        "fullname": "US survey foot",
        "epsg": 9003,
    },
    {"abbr": "survey_yd", "conv": 0.9144018288036575, "fullname": "US survey yard"},
    {
        "abbr": "survey_lk",
        "conv": 0.20116840233680463,
        "fullname": "US survey link",
        "epsg": 9034,
    },
    {
        "abbr": "survey_ch",
        "conv": 20.116840233680463,
        "fullname": "US survey chain",
        "epsg": 9033,
    },
    {
        "abbr": "survey_mi",
        "conv": 1609.3472186944373,
        "fullname": "US survey mile",
        "epsg": 9035,
    },
    {
        "abbr": "indian_yd",
        "conv": 0.914398530744441,
        "fullname": "Indian Yard",
        "epsg": 9084,
    },
    {
        "abbr": "indian_ft",
        "conv": 0.3047995104977167,
        "fullname": "Indian Foot",
        "epsg": 9080,
    },
    {
        "abbr": "indian_ft_1937",
        "conv": 0.30479841,
        "fullname": "Indian Foot",
        "epsg": 9081,
    },
    {
        "abbr": "indian_ft_1962",
        "conv": 0.3047996,
        "fullname": "Indian Foot",
        "epsg": 9082,
    },
    {
        "abbr": "indian_ft_1975",
        "conv": 0.3047995,
        "fullname": "Indian Foot",
        "epsg": 9083,
    },
    {
        "abbr": "deg",
        "conv": 1,
        "fullname": "degree",
        "epsg": 4326,
    },  # To allow geodesic conversions
]


TIME_UNIT_LIST = [
    {"abbr": "s", "conv": 1, "fullname": "seconds"},
    {"abbr": "min", "conv": 60, "fullname": "minutes"},
    {"abbr": "h", "conv": 3600, "fullname": "hours"},
    {"abbr": "d", "conv": 86400, "fullname": "days"},
    {"abbr": "a", "conv": 31557600, "fullname": "years"},
]


def to_unixtime(t):
    """
    Return float of total seconds since Unix time.
    """
    return (t - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()


def get_conversion(units, crs_units):
    """
    Looks up unit conversions in the unit dictionaries
    If distance specified, lookup distance and crs conversions and check time
    If time specified, lookup time conversion and check if time2 specified
    If time2 specified, lookup time2 conversion
    Unit conversions default to 1 if not specified
    """
    d_conv, t_conv, t2_conv, crs_conv = 1, 1, 1, 1

    if isinstance(units, tuple):
        units = UNITS(*units)
    else:
        units = UNITS(units)

    if units.distance is not None:
        d_conv = next(
            (d["conv"] for d in DISTANCE_UNIT_LIST if d.get("abbr") == units.distance),
            None,
        )
        if d_conv is None:
            raise ValueError("Invalid distance units!")
        crs_conv = next(
            (d["conv"] for d in DISTANCE_UNIT_LIST if d.get("fullname") == crs_units),
            None,
        )
        if crs_conv is None:
            crs_conv = 1
            warnings.warn(
                "No valid CRS distance units. Computations will "
                "assume CRS distance units are meters",
                category=MissingCRSWarning,
            )
        if units.time is not None:
            t_conv = next(
                (t["conv"] for t in TIME_UNIT_LIST if t.get("abbr") == units.time), None
            )
            if t_conv is None:
                raise ValueError("Invalid time units!")
        if units.time2 is not None:
            t2_conv = next(
                (t["conv"] for t in TIME_UNIT_LIST if t.get("abbr") == units.time2),
                None,
            )
            if t2_conv is None:
                raise ValueError("Invalid second time units!")
    return UNITS(d_conv, t_conv, t2_conv, crs_conv)


class MissingCRSWarning(UserWarning, ValueError):
    pass
