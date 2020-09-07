import fiona
from shapely.geometry import shape
import pandas as pd
from geopandas import GeoDataFrame

from .trajectory import Trajectory

def read_gpx_to_trajectory(fname, to_crs=None):
    """
    Reads a GPX file to a Trajectory

    Parameters
    ----------
    fname : str
        File path to the GPX file
    to_crs
        CRS to project trajectory into
    
    Returns
    -------
    Trajectory
        GPX file as a Trajectory
    """
    if not isinstance(fname, str):
        raise TypeError

    # TODO add check on to_crs

    # Check to make sure GPX has track recorded
    if 'track_points' not in fiona.listlayers(fname):
        raise ValueError("GPX file does not appear to be well-formed - missing track_points.")
    
    # Read the track points
    track_points = fiona.open(fname, layer='track_points')
    
    # parse the layer
    df = pd.DataFrame(
        [{  
            'geometry': shape(x['geometry']), 
            't': pd.to_datetime(x['properties']['time']), 
            'ele': x['properties']['ele']
            } 
        for x in track_points
        ]).set_index('t')
    geo_df = GeoDataFrame(df, crs=track_points.crs)

    # Project it if desired
    if to_crs is not None:
        geo_df = geo_df.to_crs(to_crs)

    # Make the Trajectory
    traj = Trajectory(geo_df, 1)
    return traj

