# -*- coding: utf-8 -*-

"""
***************************************************************************
    summarize_prediction_results.py
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
import pandas as pd
import numpy as np
import altair as alt
from datetime import timedelta, datetime
from itertools import repeat

import warnings
import past
warnings.filterwarnings('ignore')

sys.path.append(os.path.join(os.path.dirname(__file__),".."))

FILTER_BY_SHIPTYPE = True
SHIPTYPE = 'Cargo'
PAST_MINUTES = [1,3,5]
FUTURE_MINUTES = [1,2,3,5,10,15,20]
PREDICTION_MODE = 'linear' # 'kinetic'
LITERATURE_ERRORS = pd.read_csv('./literature_errors.csv')
LITERATURE_ERRORS = LITERATURE_ERRORS[LITERATURE_ERRORS['future']<=20]

if PREDICTION_MODE == 'linear':
    INPUT = 'E:/Geodata/AISDK/predictions_lin.csv' # '/home/agraser/tmp/predictions_lin.csv' 
elif PREDICTION_MODE == 'kinetic':
    INPUT = 'E:/Geodata/AISDK/predictions_kin.csv' # '/home/agraser/tmp/predictions_kin.csv' 


def plot_error_over_future(df):
    df1 = df.groupby('code').agg({"distance_error": [np.mean, np.std],
                                 "along_track_error": [np.mean, np.std],
                                 "cross_track_error": [np.mean, np.std],
                                 "past":[np.mean],
                                 "future":[np.mean]})
    df1.columns = ['_'.join(col).strip() for col in df1.columns.values]
    df1['distance_error_ci0'] = df1['distance_error_mean'] - 0.5*df1['distance_error_std'] 
    df1['distance_error_ci1'] = df1['distance_error_mean'] + 0.5*df1['distance_error_std']

    print(df1)
    print(LITERATURE_ERRORS)
  
    chart = alt.Chart(df1).mark_area(opacity=0.2).encode(
        x = alt.X('future_mean:Q', 
                  scale=alt.Scale(domain=(0, 20))),
        y = alt.Y('distance_error_ci0', 
                  axis=alt.Axis(title='distance_error_mean'),
                  scale=alt.Scale(domain=(0,2000))),
        y2='distance_error_ci1',
        color='past_mean:N'
    )
    chart = chart + alt.Chart(df1).mark_line().encode(
        x = alt.X('future_mean:Q', 
                  scale=alt.Scale(domain=(0, 20))),
        y = alt.Y('distance_error_mean',
                  scale=alt.Scale(domain=(0,2000))),
        color='past_mean:N'
    ) 
    chart = chart + alt.Chart(LITERATURE_ERRORS).mark_point(color='black').encode(
        x = alt.X('future'),# ,scale=alt.Scale(domain=(0, 20))),
        y = alt.Y('error'), # ,scale=alt.Scale(domain=(0,2000)))
        tooltip=['method','future','error']
    )
    
    with open(INPUT.replace('.csv','_chart.vega'),'w') as chart_output:
        chart_output.write(chart.to_json(indent=2))
        
def plot_single_map(df):
    df2 = df.groupby('context').mean()
    df2['context'] = df2.index
    print(df2)
        
    countries = alt.topo_feature('https://raw.githubusercontent.com/anitagraser/sandbox/master/land.topojson','land')
    basemap = alt.Chart(countries).mark_geoshape(
        stroke='white',
        strokeWidth=2
    ).encode(
        color=alt.value('#eee'),
    ).properties(
        width=700,
        height=500
    )
    
    grid = alt.topo_feature('https://raw.githubusercontent.com/anitagraser/sandbox/master/grid.topojson', 'grid')
    variable_list = ['distance_error', 'along_track_error', 'cross_track_error']
    map_chart = alt.Chart(grid).mark_geoshape(
        stroke='white',
        strokeWidth=2    
    ).encode(
        alt.Color('distance_error' , type='quantitative')
    ).transform_lookup(
        lookup='properties.id',
        from_=alt.LookupData(df2, 'context', variable_list)
    ).properties(
        width=500,
        height=500
    )

    map_chart = map_chart + basemap
    
    with open(INPUT.replace('.csv','_single_map.vega'),'w') as map_output:
        map_output.write(map_chart.to_json(indent=2))
                
def plot_map_series(df):
    df2 = df.groupby('context').mean()
    df2['context'] = df2.index
    print(df2)
    
    grid = alt.topo_feature('https://raw.githubusercontent.com/anitagraser/sandbox/master/grid.topojson', 'grid')
    variable_list = ['distance_error', 'along_track_error', 'cross_track_error']
    map_chart = alt.Chart(grid).mark_geoshape(
        stroke='white',
        strokeWidth=2    
    ).encode(
        alt.Color(alt.repeat('row') , type='quantitative')
    ).transform_lookup(
        lookup='properties.id',
        from_=alt.LookupData(df2, 'context', variable_list)
    ).properties(
        width=300,
        height=300
    ).repeat(
        row=variable_list
    ).resolve_scale(
        color='independent'
    )
    
    with open(INPUT.replace('.csv','_map_series.vega'),'w') as map_output:
        map_output.write(map_chart.to_json(indent=2))

if __name__ == '__main__':   
    print("{} Started! ...".format(datetime.now()))
    script_start = datetime.now()   
    
    
    frames = []
    
    for past in PAST_MINUTES:
        for future in FUTURE_MINUTES:
            input_file = INPUT.replace('in.csv', 'in_{}_{}_{}.csv'.format(SHIPTYPE, past, future))
            df = pd.read_csv(input_file, ';')
            df['past'] = past
            df['future'] = future
            df = df[df['future']==5]
            means = df.groupby('context').mean()
            print(means)
            df['code'] = '{}_{}'.format(past,future)
            frames.append(df)
            means.to_csv(input_file.replace('.csv','_summary.csv'))
            
    df = pd.concat(frames)
    df.to_csv(INPUT.replace('.csv','_summary.csv'))
  
    plot_error_over_future(df)
    plot_single_map(df)
    plot_map_series(df)
    
    
    print("{} Finished! ...".format(datetime.now()))
    print("Runtime: {}".format(datetime.now()-script_start))
    
    