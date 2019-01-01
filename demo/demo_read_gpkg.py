# -*- coding: utf-8 -*-

"""
***************************************************************************
    demo_read_gpkg.py
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
import pandas as pd 
from geopandas import read_file
from shapely.geometry import Polygon
from datetime import datetime

script_path = os.path.dirname(__file__)
sys.path.append(os.path.join(script_path,".."))

from trajectory import Trajectory 


if __name__ == '__main__':
    xmin, xmax, ymin, ymax = 116.3685035,116.3702945,39.904675,39.907728 
    polygon = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)])
    
    t_start = datetime.now()
    df = read_file(os.path.join(script_path,'demodata_geolife.gpkg'))
    df['t'] = pd.to_datetime(df['t'])
    df = df.set_index('t')
    print("Finished reading {} rows in {}".format(len(df),datetime.now() - t_start))
    
    t_start = datetime.now()
    trajectories = []
    for key, values in df.groupby(['trajectory_id']):
        trajectory = Trajectory(key, values)
        print(trajectory)
        trajectories.append(trajectory)
    print("Finished creating {} trajectories in {}".format(len(trajectories),datetime.now() - t_start))
    
    t_start = datetime.now()    
    intersections = []
    for key, values in df.groupby(['trajectory_id']):
        traj = Trajectory(key, values)
        for intersection in traj.clip(polygon):
            intersections.append(intersection)
    print("Found {} intersections in {}".format(len(intersections),datetime.now() - t_start))
