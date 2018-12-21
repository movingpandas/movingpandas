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
FILTER_BY_SHIPTYPE = True
SHIPTYPE = 'Cargo'
DESIRED_NO_SAMPLES = 10
PAST_MINUTES = [1,3,5]
FUTURE_MINUTES = [1,2,3,5,10,15,20]
FUTURE_TRAJ_DURATION = timedelta(hours=1)

DATA_PATH = '/media/agraser/Elements/AIS_DK/2018/aisdk_20180101.csv' # "E:/Geodata/AISDK/aisdk_20180101.csv" #
TEMP_EXTRACT = '/home/agraser/tmp/extract.csv' # 'E:/Geodata/AISDK/extract.csv' # 
GRID = '/home/agraser/tmp/grid.gpkg' # 'E:/Geodata/AISDK/grid.gpkg' #
OUTPUT = '/home/agraser/tmp/sample.csv' # 'E:/Geodata/AISDK/sample.csv' # 

if FILTER_BY_SHIPTYPE:
    TEMP_INTERSECTIONS = '/home/agraser/tmp/intersections_{}.pickle'.format(SHIPTYPE)
else: 
    TEMP_INTERSECTIONS = '/home/agraser/tmp/intersections.pickle'
    

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
    samples = []
    counter = 0
    shuffle(trajectories)
    for traj in trajectories:
        if counter >= DESIRED_NO_SAMPLES:
            break
        sampler = TrajectorySampler(traj, timedelta(seconds=10))
        try:
            sample = sampler.get_sample(past_timedelta, future_timedelta, min_starting_speed_ms, True, FUTURE_TRAJ_DURATION)
            samples.append(sample)
            counter +=1
            #print(traj.id)
        except RuntimeError as e:
            pass #print(e)
    return samples   

def filter_df_by_bbox(df, XMIN, XMAX, YMIN, YMAX):
    df = df[df['Latitude'] > YMIN]
    df = df[df['Latitude'] < YMAX]
    df = df[df['Longitude'] > XMIN]
    df = df[df['Longitude'] < XMAX]  
    return df
    
def create_trajectories(df):
    print("Creating time index ...")
    df['# Timestamp'] = pd.to_datetime(df['# Timestamp'], format='%m/%d/%Y %H:%M:%S')
    df = df.set_index('# Timestamp')
    
    print("Creating geometries ...")
    geometry = [Point(xy) for xy in zip(df.Longitude, df.Latitude)]
    df = GeoDataFrame(df, geometry=geometry, crs={'init': '4326'})
        
    print("Creating trajectories ...")
    trajectories = []
    for key, values in df.groupby(['MMSI']):
        try:
            trajectories.append(Trajectory(key, values))
        except ValueError:
            print("Failed to create trajectory!")
    return trajectories
    
def compute_intersections(trajectories, polygon_file, pool):
    print("Computing all intersections for future use (this can take a while!) ...")
    intersections = {}
    for cell, intersections in pool.starmap(intersection_worker, zip(polygon_file, repeat(trajectories))): 
        cell = cell['id']
        intersections[cell] = intersections
    return intersections
        
def prepare_data(pool):
    try:
        df = pd.read_csv(TEMP_EXTRACT)
        print("Loading filtered data from {} ...".format(TEMP_EXTRACT))
    except:
        print("Extracting data based on bbox {} ...".format([XMIN, XMAX, YMIN, YMAX]))
        df = pd.read_csv(DATA_PATH)
        df = filter_df_by_bbox(df, XMIN, XMAX, YMIN, YMAX)
        df.to_csv(TEMP_EXTRACT, index = False)  
        
    if FILTER_BY_SHIPTYPE:
        print("Filtering: Only {} vessels ...".format(SHIPTYPE))
        df = df[df['Ship type'] == SHIPTYPE]        
    
    trajectories = create_trajectories(df)
    polygon_file = fiona.open(GRID, 'r')
    intersections_per_grid_cell = compute_intersections(trajectories, polygon_file, pool)            
    polygon_file.close()
    
    print("Writing intersections to {} ...".format(TEMP_INTERSECTIONS))
    with open(TEMP_INTERSECTIONS, 'wb') as f: 
        pickle.dump(intersections_per_grid_cell, f)

    return intersections_per_grid_cell
    
def create_sample(intersections_per_grid_cell, past, future, pool):
    with open(OUTPUT.replace('sample.csv','sample_{}_{}_{}.csv'.format(SHIPTYPE, past, future)), 'w') as output:
        output.write("id;start_secs;past_secs;future_secs;past_traj;future_pos;future_traj\n")
        for samples in pool.starmap(sampling_worker, zip(intersections_per_grid_cell.values(), repeat(past), repeat(future))): 
            for sample in samples:
                try:
                    output.write(str(sample))
                except:
                    pass
                output.write('\n')
    output.close()    

if __name__ == '__main__':   
    print("{} Started! ...".format(datetime.now()))
    script_start = datetime.now()   
    pool = mp.Pool(mp.cpu_count())
    
    try:
        with open(TEMP_INTERSECTIONS, 'rb') as f: 
            intersections_per_grid_cell = pickle.load(f)
        print("Loading pickled data from {} ...".format(TEMP_INTERSECTIONS))
    except:
        intersections_per_grid_cell = prepare_data(pool)
    
    for past in PAST_MINUTES:
        for future in FUTURE_MINUTES:
            print("Extracting samples ({},{})...".format(past, future))
            create_sample(intersections_per_grid_cell, past, future, pool)
    
    print("{} Finished! ...".format(datetime.now()))
    print("Runtime: {}".format(datetime.now()-script_start))
    
    