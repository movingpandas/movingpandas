# -*- coding: utf-8 -*-

"""
***************************************************************************
    demo_spatial_intersections.py
    ---------------------
    Date                 : December 2018
    Copyright            : (C) 2018 by Anita Graser
    Email                : anitagraser@gmx.at
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import os
import sys 
import fiona
import pandas as pd 
from geopandas import read_file
from datetime import timedelta

script_path = os.path.dirname(__file__)
sys.path.append(os.path.join(script_path,".."))

from trajectory import Trajectory 


if __name__ == '__main__':       
    df = read_file(os.path.join(script_path,'demodata_geolife.gpkg'))
    df['t'] = pd.to_datetime(df['t'])
    df = df.set_index('t')       
    trajectories = []
    for key, values in df.groupby(['trajectory_id']):
        trajectories.append(Trajectory(key, values))        
        
    intersections = []            
    polygon_file = fiona.open(os.path.join(script_path,'demodata_grid.gpkg'), 'r')
    for feature in polygon_file:
        for traj in trajectories:
            for intersection in traj.intersection(feature):
                intersections.append(intersection)
        
    for intersection in intersections:
        print(intersection)
        
    polygon_file.close()
    
    