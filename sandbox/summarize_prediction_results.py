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


def create_interactive_linked_charts(df):
    df = df[df['future']>=5]
    #df = df[df['distance_error']<=4000]
    
    future_selection = alt.selection_multi(fields=['future'])#,'past'])
    future_color = alt.condition(future_selection, alt.Color('future:N', legend=None), alt.value('lightgray'))
    
    hist = alt.Chart(df, title='Error Distribution').mark_area(
            clip=True,
            opacity=1,
            interpolate='step'
        ).encode(
            alt.X('distance_error', bin=alt.Bin(step=100),  scale=alt.Scale(domain=(0, 4000))),
            alt.Y('count()', stack=None,  scale=alt.Scale(domain=(0, 600))),#scale=alt.Scale(type='log')),
            color = future_color 
        ).add_selection(
            future_selection
        ).transform_filter(
            future_selection
        )
    
    legend = alt.Chart(df).mark_rect().encode(
            #x=alt.X('past:N'),
            y=alt.Y('future:N', axis=alt.Axis(orient='right')),
            color=future_color
        ).add_selection(
            future_selection
        )
        
    context_selection = alt.selection_multi(fields=['context'])
    context_color = alt.condition(context_selection, alt.Color('future:N', legend=None), alt.value('lightgray'))
    map_color = alt.condition(context_selection, alt.value('#4c78a8'), alt.value('#f5f5f5'))
        
    scatter = alt.Chart(df, title='Along-track & Cross-track Error').mark_point(
            clip=True
        ).encode(
            alt.X('along_track_error', scale=alt.Scale(domain=(0, 4000))),
            alt.Y('cross_track_error', scale=alt.Scale(domain=(0, 4000))),
            color=context_color,
            tooltip=['context','future','along_track_error','cross_track_error']
        ).add_selection(
            context_selection
        ).transform_filter(
            future_selection
        )
        
    countries = alt.topo_feature('https://raw.githubusercontent.com/anitagraser/sandbox/master/land.topojson','land')
    land = alt.Chart(countries).mark_geoshape(
            stroke='white',
            strokeWidth=2
        ).encode(
            color=alt.value('lightgray'),
        ).project(
            type='equirectangular'            
        ).properties(
            width=350,
            height=230
        )

    cities = pd.DataFrame([
        {"lon":11.9667, "lat":57.7, "city":"Gothenburg"},
        {"lon":10.534, "lat":57.441, "city":"Frederikshavn"}
    ]) 
    city_points = alt.Chart(cities).mark_point().encode(
            color=alt.value('black'),
            longitude='lon:Q',
            latitude='lat:Q'
        )
    city_labels = alt.Chart(cities).mark_text(dy=-5).encode(
            longitude='lon:Q',
            latitude='lat:Q',
            text='city:N'
        )
    
    grid = alt.topo_feature('https://raw.githubusercontent.com/anitagraser/sandbox/master/grid.topojson', 'grid')
    variable_list = ['distance_error', 'along_track_error', 'cross_track_error', 'context', 'future']
    map1 = alt.Chart(grid, title='Spatial Distribution').mark_geoshape(
            stroke='white',
            strokeWidth=2    
        ).encode(
            color=map_color, 
            tooltip=['context:N']
        ).transform_lookup(
            lookup='properties.id',
            from_=alt.LookupData(df, 'context', variable_list)
        ).project(
            type='equirectangular'
        ).add_selection(
            context_selection
        )
        
    map1 = map1 + land + city_points + city_labels
        
    literature = alt.Chart(df, title='Literature Comparison').mark_line().encode(
            x = alt.X('future:Q', 
                      scale=alt.Scale(domain=(0, 20))),
            y = alt.Y('mean(distance_error):Q',
                      scale=alt.Scale(domain=(0,4000))),
            color='past:Q'#alt.value('#4c78a8')#
        ).transform_filter(
            context_selection
        ) 
    literature = literature + alt.Chart(LITERATURE_ERRORS).mark_point(color='#999').encode(
            x = alt.X('future'),# ,scale=alt.Scale(domain=(0, 20))),
            y = alt.Y('error'), # ,scale=alt.Scale(domain=(0,2000)))
            tooltip=['method','future','error']
        ).properties(
            width=300,
            height=200
        )   
        
    upper = alt.hconcat(scatter, hist, title='Vessel Trajetory Prediction Errors (in Meters)')
    lower = alt.hconcat(map1, legend)
    lower = alt.hconcat(lower, literature)
    chart = alt.vconcat(upper, lower)

    with open(INPUT.replace('.csv','_interactive.vega'),'w') as chart_output:
        chart_output.write(chart.to_json(indent=2))

def create_error_over_future_graph(df):
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
        
    return chart
        
def create_single_map(df):
    df2 = df.groupby('context').mean()
    df2['context'] = df2.index
    print(df2)
        
    countries = alt.topo_feature('https://raw.githubusercontent.com/anitagraser/sandbox/master/land.topojson','land')
    basemap = alt.Chart(countries).mark_geoshape(
        stroke='white',
        strokeWidth=2
    ).encode(
        color=alt.value('#eee'),
    ).project(
        type='equirectangular'        
    ).properties(
        width=700,
        height=400
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
    )
    
    cities = pd.DataFrame([
        {"lon":11.9667, "lat":57.7, "city":"Gothenburg"},
        {"lon":10.534, "lat":57.441, "city":"Frederikshavn"}
    ]) 
    city_points = alt.Chart(cities).mark_point().encode(
            color=alt.value('black'),
            longitude='lon:Q',
            latitude='lat:Q'
        )
    city_labels = alt.Chart(cities).mark_text(dy=-5).encode(
            longitude='lon:Q',
            latitude='lat:Q',
            text='city:N'
        )

    map_chart = map_chart + basemap + city_points + city_labels
    
    with open(INPUT.replace('.csv','_single_map.vega'),'w') as map_output:
        map_output.write(map_chart.to_json(indent=2))
                
def create_map_series(df):
    # Note that a LayeredChart cannot contain faceted charts as its elements.
    # Therefore, we cannot use a basemap in this configuration, since it would produce an invalid specification.
    # More info: https://github.com/altair-viz/altair/issues/785
    
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
        ).project(
            type='equirectangular'
        ).properties(
            width=300,
            height=200
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
            #df = df[df['future']==5]
            means = df.groupby('context').mean()
            print(means)
            df['code'] = '{}_{}'.format(past,future)
            frames.append(df)
            means.to_csv(input_file.replace('.csv','_summary.csv'))
            
    df = pd.concat(frames)
    df.to_csv(INPUT.replace('.csv','_summary.csv'))
  
    #create_error_over_future_graph(df)
    #create_single_map(df)
    #create_map_series(df)
    
    create_interactive_linked_charts(df)
    
    
    print("{} Finished! ...".format(datetime.now()))
    print("Runtime: {}".format(datetime.now()-script_start))
    
    