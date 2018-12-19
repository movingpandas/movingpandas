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
import pickle
import pandas as pd 
import multiprocessing as mp
from geopandas import GeoDataFrame
from shapely.geometry import Point
from datetime import timedelta, datetime
from itertools import repeat
from random import shuffle

import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.join(os.path.dirname(__file__),".."))

from trajectory import Trajectory 
from trajectory_sampler import TrajectorySampler


pd.set_option('display.max_colwidth', -1)

XMIN, YMIN, XMAX, YMAX = 9.90353, 56.89971, 12.79016, 58.18372 # 10.30774, 57.25922, 12.13159, 58.03877 #

DATA_PATH = '/media/agraser/Elements/AIS_DK/2018/aisdk_20180101.csv' # "E:/Geodata/AISDK/aisdk_20180101.csv" #
TEMP_EXTRACT = '/home/agraser/tmp/extract.csv' # 'E:/Geodata/AISDK/extract.csv' # 
TEMP_INTERSECTIONS = '/home/agraser/tmp/intersections.pickle'
GRID = '/home/agraser/tmp/grid.gpkg' # 'E:/Geodata/AISDK/grid.gpkg' #
OUTPUT = '/home/agraser/tmp/sample.csv' # 'E:/Geodata/AISDK/sample.csv' # 

FILTER_BY_SHIPTYPE = True
SHIPTYPE = 'Cargo'
DESIRED_NO_SAMPLES = 10
PAST_MINUTES = [5]
FUTURE_MINUTES = [20]
BUFFER_MINUTES = 5

def intersection_worker(feature, trajectories):
    intersections = []
    for traj in trajectories:
        for intersection in traj.intersection(feature):
            intersections.append(intersection)
    return feature, intersections
    
def sampling_worker(trajectories, past, future):
    min_starting_speed_ms = 1
    past_timedelta = timedelta(minutes=past)
    future_timedelta = timedelta(minutes=future)
    buffer_timedelta = timedelta(minutes=BUFFER_MINUTES)
    samples = []
    counter = 0
    shuffle(trajectories)
    for traj in trajectories:
        if counter >= DESIRED_NO_SAMPLES:
            break
        sampler = TrajectorySampler(traj, timedelta(seconds=10))
        try:
            sample = sampler.get_sample(past_timedelta, future_timedelta, min_starting_speed_ms, True, buffer_timedelta)
            samples.append(sample)
            counter +=1
            print(traj.id)
        except RuntimeError as e:
            print(e)
    return samples   

if __name__ == '__main__':   
    script_start = datetime.now()
    print("{} Loading data ...".format(script_start))
    
    try:
        df = pd.read_csv(TEMP_EXTRACT)
    except:
        print("Extracting data based on bbox {} ...".format([XMIN, XMAX, YMIN, YMIN]))
        df = pd.read_csv(DATA_PATH)
        df = df[df['Latitude'] > YMIN]
        df = df[df['Latitude'] < YMAX]
        df = df[df['Longitude'] > XMIN]
        df = df[df['Longitude'] < XMAX]
        df.to_csv(TEMP_EXTRACT, index = False)    
    
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
        #print("Adding trajectory {} ...".format(key))
        try:
            trajectories.append(Trajectory(key, values))
        except ValueError:
            print("Failed to create trajectory!")  
    
    pool = mp.Pool(mp.cpu_count())
    
    polygon_file = fiona.open(GRID, 'r')
    try:
        with open(TEMP_INTERSECTIONS, 'rb') as f: intersections_per_grid_cell = pickle.load(f)
    except:
        print("Computing all intersections for future use (this can take a while!) ...")
        intersections_per_grid_cell = {}
        for cell, intersections in pool.starmap(intersection_worker, zip(polygon_file, repeat(trajectories))): 
            cell = cell['id']
            intersections_per_grid_cell[cell] = intersections
        print("Writing intersections to pickle ...")
        with open(TEMP_INTERSECTIONS, 'wb') as f: pickle.dump(intersections_per_grid_cell, f)
    
    print("Extracting samples ...")
    for past in PAST_MINUTES:
        for future in FUTURE_MINUTES:
            samples = []
            with open(OUTPUT.replace('sample.csv','sample_{}_{}.csv'.format(past,future)), 'w') as output:
                output.write("id;start_secs;past_secs;future_secs;past_traj;future_pos;future_traj\n")
                for samples in pool.starmap(sampling_worker, zip(intersections_per_grid_cell.values(), repeat(past), repeat(future))): 
                    for sample in samples:
                        try:
                            output.write(str(sample))
                        except:
                            pass
                        output.write('\n')
            output.close()
    
    
    polygon_file.close()
    print("{} Finished! ...".format(datetime.now()))
    print("Runtime: {}".format(datetime.now()-script_start))
    
    