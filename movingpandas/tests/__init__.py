import pytest
import importlib


def _importorskip(modname):
    try:
        importlib.import_module(modname)
        has = True
    except ImportError:
        has = False
    func = pytest.mark.skipif(not has, reason=f"requires {modname}")
    return has, func


def _skip_if_geopandas_pre_1():
    from importlib.metadata import version

    if version("geopandas") >= "1.0.0":
        has = True
    else:
        has = False
    func = pytest.mark.skipif(not has, reason="requires geopandas >= 1.0")
    return has, func


has_stonesoup, requires_stonesoup = _importorskip("stonesoup")
has_holoviews, requires_holoviews = _importorskip("holoviews")
has_folium, requires_folium = _importorskip("folium")
has_geopandas1, requires_geopandas1 = _skip_if_geopandas_pre_1()
