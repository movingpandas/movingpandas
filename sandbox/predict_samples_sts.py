# -*- coding: utf-8 -*-

"""
***************************************************************************
    predict_samples_sts.py
    ---------------------
    Date                 : January 2019
    Copyright            : (C) 2019 by Anita Graser
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
import pickle
import pandas as pd
import numpy as np
from geopandas import GeoDataFrame
import multiprocessing as mp
from datetime import timedelta, datetime
from itertools import repeat
from sklearn.cluster import DBSCAN
from scipy.spatial import cKDTree
from geopy.distance import great_circle
from shapely.geometry import MultiPoint, Point
from shapely import wkt

import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.join(os.path.dirname(__file__),".."))

from trajectory_predictor import TrajectoryPredictor
from trajectory_prediction_evaluator import TrajectoryPredictionEvaluator, EvaluatedPrediction


FILTER_BY_SHIPTYPE = True
SHIPTYPE = 'Cargo' #'Fishing' #
PAST_MINUTES = [1,3,5]
FUTURE_MINUTES = [1,5,10,15,20]
PREDICTION_MODE = 'similar_traj'

INPUT_SAMPLE = 'E:/Dropbox/AIT/MARNG/data/prediction_input/sample.csv'
INPUT_POTENTIAL_LOCATIONS = 'E:/Dropbox/AIT/MARNG/data/prediction_output_20190215/sample.csv'
OUTPUT = 'E:/Dropbox/AIT/MARNG/data/prediction_output_20190215/predictions_sts.csv'

kms_per_radian = 6371.0088


def most_common(a):
    (values, counts) = np.unique(a, return_counts=True)
    ind = np.argmax(counts)
    return values[ind]

def get_centroid(cluster):
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    return centroid

def get_nearest_cluster_point(cluster, pt):
    if type(pt) == Point:
        pt = (pt.y, pt.x)
    nearest_pt = min(cluster, key=lambda point: great_circle(point, pt).m)
    nearest_pt = Point(nearest_pt[1],nearest_pt[0])
    return nearest_pt

def get_main_cluster(df, epsilon, x='lon', y='lat'):
    # represent points consistently as (lat, lon) and convert to radians to fit using haversine metric
    coords = df.as_matrix(columns=[y, x])
    db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))
    print('Number of clusters: {:,}'.format(num_clusters))
    main_cluster_label = most_common(cluster_labels)
    print('Main cluster: {}'.format(main_cluster_label))
    main_cluster = [coords[cluster_labels == main_cluster_label]][0]
    return main_cluster

def dbscan_main_center(df, epsilon):
    main_cluster = get_main_cluster(df, epsilon)
    centroid = get_centroid(main_cluster)
    return get_nearest_cluster_point(main_cluster, centroid)

def get_center_of_main_cluster(df, past, future):
    if len(df) == 0:
        return None
    eps_rad = 0.5 / kms_per_radian
    center = dbscan_main_center(df, epsilon=eps_rad)
    return center

def get_location_closest_to_linear_prediction(df, sample, future, x='lon', y='lat'):
    prediction_timedelta = timedelta(minutes=future)
    predictor = TrajectoryPredictor(sample.past_traj)
    predicted_location = predictor.predict_linearly(prediction_timedelta)
    if len(df) == 0:
        return predicted_location
    main_cluster = df.as_matrix(columns=[y, x])
    return get_nearest_cluster_point(main_cluster, predicted_location)

def get_centermost_location(df, sample, future):
    prediction_timedelta = timedelta(minutes=future)
    predictor = TrajectoryPredictor(sample.past_traj)
    predicted_location = predictor.predict_linearly(prediction_timedelta)
    if len(df) == 0:
        return predicted_location
    elif len(df) <= 2:
        x = 0
    elif len(df) == 3:
        x = get_centermost_id(df, 2)
    else:
        x = get_centermost_id(df, 3)
    return Point(df.iloc[x].lon, df.iloc[x].lat)

def get_centermost_id(df, k):
    # note that this approach uses euclidean distances!
    df = df.reset_index()
    df['prediction_id'] = df.index
    pts = np.array(list(zip(df.lon, df.lat)) )
    btree = cKDTree(pts)
    dist, idx = btree.query(pts, k=k)
    #print(idx)
    counts = [0]*len(df)
    if k==2:
        for id, n1 in idx:
            counts[n1] += 1
    else:
        for id, n1, n2 in idx:
            counts[n1] += 1
            counts[n2] += 2
    return counts.index(max(counts))


def compute_final_sts_prediction(df, sample, past, future):
    #print(sample.id)
    #print(df[df['ID']==sample.id])
    predictions_for_current_sample = df[df['ID']==sample.id]
    #print(len(predictions_for_current_sample))
    #predicted_location = get_center_of_main_cluster(predictions_for_current_sample, past, future)
    #predicted_location = get_location_closest_to_linear_prediction(predictions_for_current_sample, sample, future)
    predicted_location = get_centermost_location(predictions_for_current_sample, sample, future)
    if predicted_location is None:
        return None
    errors = TrajectoryPredictionEvaluator(sample, predicted_location, 'epsg:25832').get_errors()
    context = sample.past_traj.context
    prediction = EvaluatedPrediction(predicted_location, context, errors)
    return prediction

def compute_final_sts_predictions(input_predictions, input_samples, past, future):
    out = OUTPUT.replace('.csv', '_{}_{}_{}.csv'.format(SHIPTYPE, past, future))
    print("Writing to {}".format(out))
    with open(out, 'w') as output:
        output.write(EvaluatedPrediction.get_csv_header())
        for counter, sample in enumerate(input_samples):
            sample.id = '{}_{}'.format(counter, sample.id)
            prediction = compute_final_sts_prediction(input_predictions, sample, past, future)
            try:
                output.write(prediction.to_csv())
            except TypeError as e:
                print(e)
            except AttributeError as e:
                pass
    output.close()

def clean_file(file):
    content = []
    counter = 0
    for line in open(file,'r'):
        line = line.strip()
        if len(content) == 0:
            header = line
            content.append(line+';lat;lon\n')
        elif line != header:
            pt = wkt.loads(line.split(';')[2])
            lat = pt.y
            lon = pt.x
            content.append('{}_{};{};{}\n'.format(counter,line,lat,lon))
        else:
            counter += 1
    cleaned = file+'.clean'
    with open(cleaned, 'w') as f:
        f.writelines(content)
    return cleaned

if __name__ == '__main__':
    # the previous step of Similar Trajectory Search returns a set of potential future locations
    # to provide one final prediction, we determine the centermost coordinate
    print("{} Started! ...".format(datetime.now()))
    script_start = datetime.now()
    
    for past in PAST_MINUTES:
        for future in FUTURE_MINUTES:
            samples_file = INPUT_SAMPLE.replace('.csv','_{}_{}_{}.pickle'.format(SHIPTYPE, past, future))
            try:
                with open(samples_file, 'rb') as f:
                    input_samples = pickle.load(f)
                print("Loading pickled data from {} ...".format(samples_file))
            except:
                print("Failed to load pickled data from {}!".format(samples_file))

            predictions_file = INPUT_POTENTIAL_LOCATIONS.replace('.csv', '_{}_{}_{}.csv.prediction'.format(SHIPTYPE, past, future))
            cleaned = clean_file(predictions_file)
            predictions = pd.read_csv(cleaned, ';')

            compute_final_sts_predictions(predictions, input_samples, past, future)
    
    print("{} Finished! ...".format(datetime.now()))
    print("Runtime: {}".format(datetime.now()-script_start))
    
    