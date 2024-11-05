# -*- coding: utf-8 -*-

import importlib
import platform
import sys


def _get_sys_info():
    """System information

    Returns
    -------
    sys_info : dict
        system and Python version information
    """
    python = sys.version.replace("\n", " ")

    blob = [
        ("python", python),
        ("executable", sys.executable),
        ("machine", platform.platform()),
    ]

    return dict(blob)


def _get_C_info():
    """Information on system PROJ, GDAL, GEOS
    Returns
    -------
    c_info: dict
        system PROJ information
    """
    try:
        import pyproj

        proj_version = pyproj.proj_version_str
    except Exception:
        proj_version = None
    try:
        import pyproj

        proj_dir = pyproj.datadir.get_data_dir()
    except Exception:
        proj_dir = None

    blob = [
        ("PROJ", proj_version),
        ("PROJ data dir", proj_dir),
    ]

    return dict(blob)


def _get_deps_info():
    """Overview of the installed version of main dependencies

    Returns
    -------
    deps_info: dict
        version information on relevant Python libraries
    """
    deps = [
        "numpy",
        "geopandas",
        "geopy",
        "geoviews",
        "holoviews",
        "hvplot",
        "mapclassify",
        "matplotlib",
        "pandas",
        "pyproj",
        "shapely",
        "stonesoup",
    ]

    def get_version(module):
        return module.__version__

    deps_info = {}

    for modname in deps:
        try:
            if modname in sys.modules:
                mod = sys.modules[modname]
            else:
                mod = importlib.import_module(modname)
            ver = get_version(mod)
            deps_info[modname] = ver
        except Exception:
            deps_info[modname] = None

    return deps_info


def show_versions():
    """
    Print system information and installed module versions.
    """
    from movingpandas import __version__ as mpd_version

    sys_info = _get_sys_info()
    deps_info = _get_deps_info()
    proj_info = _get_C_info()

    maxlen = max(len(x) for x in deps_info)
    print(f"\nMovingPandas {mpd_version}")
    print("\nSYSTEM INFO")
    print("-----------")
    for k, stat in sys_info.items():
        print(f"{k: <{maxlen}}: {stat}")
    print("\nPROJ INFO")
    print("-----------")
    for k, stat in proj_info.items():
        print(f"{k: <{maxlen}}: {stat}")
    print("\nPYTHON DEPENDENCIES")
    print("-------------------")
    for k, stat in deps_info.items():
        print(f"{k: <{maxlen}}: {stat}")
