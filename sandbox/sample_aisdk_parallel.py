# -*- coding: utf-8 -*-

"""
***************************************************************************
    sample_aisdk_parallel.py
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
import multiprocessing as mp
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
DESIRED_NO_SAMPLES = 3
PAST_MINUTES = 5
FUTURE_MINUTES = 5
BUFFER_MINUTES = 5

def worker(feature, trajectories, past_timedelta, future_timedelta, 
           min_starting_speed_ms, buffer_timedelta):
    print("Processing feature {} ...".format(feature))
    samples = []
    counter = 0
    for traj in trajectories:
        for intersection in traj.intersection(feature):
            if counter >= DESIRED_NO_SAMPLES:
                break
            sampler = TrajectorySampler(intersection, timedelta(seconds=10))
            try:
                sample = sampler.get_sample(past_timedelta, future_timedelta, min_starting_speed_ms, True, buffer_timedelta)
                samples.append(sample)
                counter +=1
                print(traj.id)
            except RuntimeError as e:
                print(e)   
    return samples

def listener(my_queue):
    print("Writing output ...")
    output = open(OUTPUT, 'w')
    output.write("id;start_secs;past_secs;future_secs;past_traj;future_pos;future_traj\n")
    while 1:
        result = my_queue.get()
        if result == 'kill':
            break
        for sample in samples:
            try:
                output.write(str(sample))
            except:
                pass
            output.write('\n')
    output.close()

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
    min_starting_speed_ms = 1
    past_timedelta = timedelta(minutes=PAST_MINUTES)
    future_timedelta = timedelta(minutes=FUTURE_MINUTES)
    buffer_timedelta = timedelta(minutes=BUFFER_MINUTES)
    polygon_file = fiona.open(GRID, 'r')
    samples = []    
    
    manager = mp.Manager()
    my_queue = manager.Queue()    
    pool = mp.Pool(mp.cpu_count() + 2)
    watcher = pool.apply_async(listener, (my_queue,))
    jobs = []
    
    for feature in polygon_file:
        job = pool.apply_async(worker, (
            feature, trajectories, past_timedelta, future_timedelta, 
            min_starting_speed_ms, buffer_timedelta))
        jobs.append(job)        
        
    for job in jobs:
        job.get()
        
    my_queue.put('kill')
    pool.close()   
        
    polygon_file.close()
    
    
    