# -*- coding: utf-8 -*-

"""
***************************************************************************
    sample_aisdk.py
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
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import timedelta

sys.path.append(os.path.join(os.path.dirname(__file__),".."))

from trajectory import Trajectory 
from trajectory_sampler import TrajectorySampler


pd.set_option('display.max_colwidth', -1)

XMIN, YMIN, XMAX, YMAX = 10.30774, 57.25922, 12.13159, 58.03877 # 11.30746, 57.47915, 12.10191, 57.77084 #

DATA_PATH = "E:/Geodata/AISDK/aisdk_20180101.csv" # '/media/agraser/Elements/AIS_DK/2018/aisdk_20180101.csv' #
EXTRACT = 'E:/Geodata/AISDK/extract.csv' # '/home/agraser/tmp/extract.csv' #
GRID = 'E:/Geodata/AISDK/grid.gpkg' #'/home/agraser/tmp/grid.gpkg' #
OUTPUT = 'E:/Geodata/AISDK/sample.csv' # '/home/agraser/tmp/sample.csv' #

FILTER_BY_SHIPTYPE = True
SHIPTYPE = 'Cargo'


if __name__ == '__main__':   
    try:
        print("Loading data ...")
        df = pd.read_csv(EXTRACT)
    except:
        print("Extracting data based on bbox {} ...".format([XMIN, XMAX, YMIN, YMIN]))
        df = pd.read_csv(DATA_PATH)
        df = df[df['Latitude'] > YMIN]
        df = df[df['Latitude'] < YMAX]
        df = df[df['Longitude'] > XMIN]
        df = df[df['Longitude'] < XMAX]
        df.to_csv(EXTRACT, index = False)    
    
    print("Creating time index ...")
    df['# Timestamp'] = pd.to_datetime(df['# Timestamp'], format='%m/%d/%Y %H:%M:%S')
    df = df.set_index('# Timestamp')
    
    if FILTER_BY_SHIPTYPE:
        print("Filtering: Only {} vessels ...".format(SHIPTYPE))
        df = df[df['Ship type'] == SHIPTYPE]
    
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
    
    print("Extracting samples ...")
    desired_number_of_samples = 3
    min_starting_speed_ms = 1
    past_timedelta = timedelta(minutes=5)
    future_timedelta = timedelta(minutes=5)
    buffer_timedelta = timedelta(minutes=5)
    samples = []    

    polygon_file = fiona.open(GRID, 'r')
    for feature in polygon_file:
        print("Processing feature {} ...".format(feature))
        counter = 0
        for traj in trajectories:
            for intersection in traj.intersection(feature):
                if counter >= desired_number_of_samples:
                    break
                sampler = TrajectorySampler(intersection, timedelta(seconds=10))
                try:
                    sample = sampler.get_sample(past_timedelta, future_timedelta, min_starting_speed_ms, True, buffer_timedelta)
                    samples.append(sample)
                    counter +=1
                    print(traj.id)
                except RuntimeError as e:
                    print(e)     
                      
    print("Writing output ...")
    output = open(OUTPUT, 'w')
    output.write("id;start_secs;past_secs;future_secs;past_traj;future_pos;future_traj\n")
    for sample in samples:
        try:
            output.write(str(sample))
        except:
            pass
        output.write('\n')
    output.close()
        
    polygon_file.close()
    
    
    