# -*- coding: utf-8 -*-

"""
***************************************************************************
    predict_samples.py
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
import pickle
import multiprocessing as mp
from datetime import timedelta, datetime
from itertools import repeat

import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.join(os.path.dirname(__file__),".."))

from trajectory_predictor import TrajectoryPredictor
from trajectory_prediction_evaluator import TrajectoryPredictionEvaluator, EvaluatedPrediction


FILTER_BY_SHIPTYPE = True
SHIPTYPE = 'Passenger' # 'Cargo' # 'Fishing' #
PAST_MINUTES = [1,3,5]
FUTURE_MINUTES = [1,5,10,15,20]
PREDICTION_MODE = 'linear' # 'kinetic'

INPUT = 'E:/Geodata/AISDK/sample.csv' # '/home/agraser/tmp/sample.csv' 
if PREDICTION_MODE == 'linear':
    OUTPUT = 'E:/Geodata/AISDK/predictions_lin.csv' # '/home/agraser/tmp/predictions_lin.csv' 
elif PREDICTION_MODE == 'kinetic':
    OUTPUT = 'E:/Geodata/AISDK/predictions_kin.csv' # '/home/agraser/tmp/predictions_kin.csv' 

def prediction_worker(sample, prediction_timedelta):
    predictor = TrajectoryPredictor(sample.past_traj) 
    if PREDICTION_MODE == 'linear':
        predicted_location = predictor.predict_linearly(prediction_timedelta)
    elif PREDICTION_MODE == 'kinetic':
        predicted_location = predictor.predict_kinetically(prediction_timedelta)
    errors = TrajectoryPredictionEvaluator(sample, predicted_location, 'epsg:25832').get_errors()
    context = sample.past_traj.context
    prediction = EvaluatedPrediction(predicted_location, context, errors)
    return prediction
    
def compute_predictions(samples, past, future, pool):
    out = OUTPUT.replace('in.csv', 'in_{}_{}_{}.csv'.format(SHIPTYPE, past, future))
    print("Writing to {}".format(out))
    future = timedelta(minutes=future)
    with open(out, 'w') as output:
        output.write(EvaluatedPrediction.get_csv_header())
        for prediction in pool.starmap(prediction_worker, zip(samples, repeat(future))): 
            try:
                output.write(prediction.to_csv())
                #print(prediction)
            except TypeError as e:
                print(e)
    output.close()    

if __name__ == '__main__':   
    print("{} Started! ...".format(datetime.now()))
    script_start = datetime.now()   
    pool = mp.Pool(mp.cpu_count())
    
    for past in PAST_MINUTES:
        for future in FUTURE_MINUTES:
            input_file = INPUT.replace('sample.csv','sample_{}_{}_{}.pickle'.format(SHIPTYPE, past, future))
            try:
                with open(input_file, 'rb') as f: 
                    input_samples = pickle.load(f)
                print("Loading pickled data from {} ...".format(input_file))
            except:    
                print("Failed to load pickled data from {}!".format(input_file))
            compute_predictions(input_samples, past, future, pool)
    
    print("{} Finished! ...".format(datetime.now()))
    print("Runtime: {}".format(datetime.now()-script_start))
    
    