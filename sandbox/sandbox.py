# -*- coding: utf-8 -*-

"""
***************************************************************************
    sandbox.py
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
import unittest
import fiona
import pandas as pd 
import numpy as np
from geopandas import GeoDataFrame, read_file
from shapely.geometry import Point, LineString, Polygon
from shapely.affinity import translate
from datetime import datetime, timedelta
from numpy import nan

sys.path.append(os.path.join(os.path.dirname(__file__),".."))

from trajectory import Trajectory 
from trajectory_sampler import TrajectorySampler


if __name__ == '__main__':   
    
    pd.set_option('display.max_colwidth', -1)
    
    xmin, xmax, ymin, ymax = 10.30774, 12.13159, 57.25922, 58.03877
    
    all_data_path = "E:/Geodata/AISDK/aisdk_20180101.csv"
    extract_path = 'E:/Geodata/AISDK/extract.csv'
    grid_path = 'E:/Geodata/AISDK/grid.gpkg'
    output_path = 'E:/Geodata/AISDK/sample.csv'
    
    try:
        print("Loading data ...")
        df = pd.read_csv(extract_path)
    except:
        print("Extracting data based on bbox {} ...".format([xmin, xmax, ymin, ymax]))
        df = pd.read_csv(all_data_path)
        df = df[df['Latitude'] > ymin]
        df = df[df['Latitude'] < ymax]
        df = df[df['Longitude'] > xmin]
        df = df[df['Longitude'] < xmax]
        df.to_csv(extract_path, index = False)    
    
    print("Creating time index ...")
    df['# Timestamp'] = pd.to_datetime(df['# Timestamp'], format='%m/%d/%Y %H:%M:%S')
    df = df.set_index('# Timestamp')
    
    print("Creating geometries ...")
    geometry = [Point(xy) for xy in zip(df.Longitude, df.Latitude)]
    df = GeoDataFrame(df, geometry=geometry, crs={'init': '4326'})
        
    print("Creating trajectories ...")
    trajectories = []
    for key, values in df.groupby(['MMSI']):
        print("Adding trajectory {} ...".format(key))
        try:
            trajectories.append(Trajectory(key, values))
        except ValueError:
            print("Failed to create trajectory!")  
    n = len(trajectories)
    
    print("Extracting samples ...")
    desired_number_of_samples = 3
    samples = []    
    i= 0
    polygon_file = fiona.open(grid_path, 'r')
    for feature in polygon_file:
        counter = 0
        i = 0
        while counter < desired_number_of_samples and i < n:
            for traj in trajectories:
                print(traj.id)
                for intersection in traj.intersection(feature):
                    sampler = TrajectorySampler(intersection, timedelta(seconds=10))
                    try:
                        sample = sampler.get_sample(timedelta(minutes=5),timedelta(minutes=20),1,True)
                        samples.append(sample)
                        counter +=1
                    except RuntimeError as e:
                        print(e)     
                i += 1               
                    
        
    print("Writing output ...")
    output = open(output_path,'w')
    for sample in samples:
        output.write(str(sample))
        output.write('\n')
    output.close()
        
    polygon_file.close()
    
    
    