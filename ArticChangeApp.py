# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
# --------------------
# Read data
data = pd.read_csv('others/AllData.csv', parse_dates=[1], index_col=[0])
data = data.set_index('Datetime')
data = data.resample('720T').mean()
data = data[:'24-08-2020']
data = data.reset_index()
data['CH4d_ppm'] = data['CH4d_ppm'] + 0.8
data['Date'] = data['Datetime'].dt.strftime('%d-%m-%y %H:%M')
data['CH4'] = data['CH4d_ppm'].round(2).astype(str)
data['Temperature'] = data['Temp °C'].round(2).astype(str)
data['Salinity'] = data['Sal psu'].round(2).astype(str)
data['CO2'] = data['CO2d_ppm'].round(1).astype(str)
data['Oxygen'] = data['ODO % sat'].round(1).astype(str)
data['Turbidity'] = data['Turbidity FNU'].round(1).astype(str)
data['Specific Conductivity \U0001D725\u2082\u2085'] = data['SpCond µS/cm'].round(1).astype(str)

mapbox_access_token = open(".mapbox_token").read()
lastloc = '%.2f°N, %.2f°E'  % (data['Latitude'].iloc[-1], data['Longitude'].iloc[-1])
lastime = data['Date'].iloc[-1]

epoch = dt.utcfromtimestamp(0)

def unix_time_millis(dt):
    return (dt-epoch).total_seconds()/60./24

def get_marks_from_start_end(start, end):
    ''' Returns dict with one item per month
    {1440080188.1900003: '2015-08',
    '''
    result = []
    current = start
    while current <= end:
        result.append(current)
        current += relativedelta(days=1)
    index = np.linspace(0, len(result)-1, 10).astype(int)
    return {int(unix_time_millis(result[i])):{'label': result[i].strftime('%d.%m.%Y'), 'style': {'color':'white'}} for i in index}
#------------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])
server = app.server

#------------------------------------------------------------------
# Cards

# cardmain = dbc.Card({{{
#         [
#             dbc.CardBody(
#                 [
#                     html.H2('Mauritius Information'),
#                     html.H5('Last location reported: %s' % lastloc),
#                     html.H5('Last date reported: %s' % lastime),
#                     html.H3('General selections'),
#                     html.Label(['Choose variable:'], style={'font-weight': 'bold', 'text-align': 'center'}),
#                     html.Br(),
#                     dbc.Row(
#                         [
#                             dbc.Col(
#                                 html.Label(['Select Dates:'], style={'font-weight': 'bold', 'text-align': 'center'}),
#                                 width={"size": 2.3, "order": "first", "offset": 0.2},
#                                 ),
#                             dbc.Col(
#                                 dcc.DatePickerRange(
#                                     id='date-picker',
#                                     min_date_allowed=data['Datetime'].min(),
#                                     max_date_allowed=data['Datetime'].max(),
#                                     initial_visible_month=data['Datetime'].mean(),
#                                     clearable=False,
#                                     display_format='D.M.YYYY'
#                                     ),
#                                 width={"size": 6.5, "offset": 0.2},
#                                 ),
#                             dbc.Col(
#                                 html.Button('Clear Selection', id='button-clear', n_clicks=0),
#                                 width={"size": 2.3, "offset": 0.2, "order": "last"},
#                                 ),
#                             ], align="center", justify='around'
#                     ),
#                     #style={'display': 'inline-block', 'padding': '10px 30px'}),
#                     #    style={'display': 'inline-block'}),
# 
#                     ]
#                 ),
#             ],
#         color="Dark",
#         inverse=True,
#         outline=False,
#         )}}}

graph_card = dbc.Card(# {{{
        [
            dbc.CardHeader(id='map_title'),#, className='card-title', style={'margin-left':5, 'margin-top':5}),
            dcc.Graph(id='map', figure={}, responsive='auto')#, style={'height': '80vh'}),
        ]
    )
time_plots = dbc.Card(
        [
            dbc.CardHeader(id='time_series_title'),#, className='card-title', style={'margin-left':5, 'margin-top':5}),
            dcc.Graph(id='time-series', figure={}, responsive='auto')#, style={'height':'25vh'}),
        ],
        color='secondary', inverse=False,
    )# }}}

#------------------------------------------------------------------
# App layout
app.layout = dbc.Container(
        [

            dbc.Row([], style={'height':'1vh'}),
            dbc.Row(
                [# {{{
                    dbc.Col(
                        html.H2('Arctic Expedition 2020-2024', style={'font-weight':'bold'}),
                        width={'size': 6, 'offset':0}, xl={'size':5, 'offset':1}, #style={'height':'100%'}
                        ),
                    dbc.Col(
                        [
                            html.H6('Last location reported: ' + lastloc, style={'text-align':'right'}),
                            html.H6('Last date reported: ' + lastime, style={'text-align':'right'}),
                            ],
                        width={'size':5, 'offset':1}, xl={'size':4, 'offset':1}, #style={'height':'100%', 'background-color':'green'}
                        ),
                ],# }}}
                align='center', className='h-25',
                ),
            dbc.Row([], style={'height':'1vh'}),
            dbc.Row([], style={'backgroundColor': '#2A3E4F', 'height':'2vh'}),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H6('Select variable:'),
                            dcc.Dropdown(
                                id='slct_var',# {{{
                                options=[
                                    {"label":"Carbon Dioxide", "value":'CO2d_ppm'},
                                    {"label":"Methane", "value":"CH4d_ppm"},
                                    {"label":"Temperature", "value":"Temp °C"},
                                    {"label":"Salinity", "value":'Sal psu'},
                                    {"label":"Oxygen saturation", "value":'ODO % sat'},
                                    {"label":"Turbidity", "value":'Turbidity FNU'},
                                    {"label":"Specific Conductivity", "value":'SpCond µS/cm'},
                                    ],
                                multi=False,
                                optionHeight=35,
                                value='CO2d_ppm',
                                searchable=True,
                                placeholder='Please select...',
                                style={'color': '#000000'},
                                clearable=False,
                                ),# }}}
                            ],
                        width=3,
                        lg={'size':2, 'offset':1},
                        ),
                    dbc.Col(
                        html.H6(id='average_value'),
                        width={'size':2},
                        lg={'size':1},
                        align='center'
                        ),
                    dbc.Col(
                        [
                             dbc.Row(
                                 [
                                     dbc.Col(
                                         [
                                             html.H6('Select dates:'),
                                             dcc.DatePickerRange(# {{{
                                                 id='date_range',
                                                 min_date_allowed=data.Datetime.min(),
                                                 max_date_allowed=data.Datetime.max(),
                                                 initial_visible_month=data.Datetime.mean(),
                                                 clearable=False,
                                                 display_format='D.M.YYYY',
                                                 ),# }}}
                                             ],
                                         width=8,
                                         lg={'size':7, 'offset':1},
                                         #style={'backgroundColor':'red'}
                                         ),
                                     dbc.Col(
                                         dbc.Button('Clear selection', id='button-clear', n_clicks=0, color='success', style={'padding-left':2, 'padding-right':2}),
                                         width={'size':4, 'offset':0},
                                         lg={'size':3, 'offset':0},
                                         #style={'backgroundColor':'blue'}
                                         )
                                    ],
                                 align='center')
                             ],
                        width={'size':7, 'offset':0},
                        lg={'size':4, 'offset':1},
                        ),
                    ],
                    #style={'margin-bottom':0, 'backgroundColor': None}, align='center', justify='around', className='h-25'
                    style={'margin-bottom':0, 'backgroundColor': '#2A3E4F'}, align='center', #justify='around'
                ),
            dbc.Row([], style={'backgroundColor': '#2A3E4F', 'height':'2vh'}),
            dbc.Row(
                    [# {{{
                        dbc.Col(graph_card, width={'size':10, 'offset':1}, lg={'size': 10, 'offset':1}),
                        ],# }}}
                    #style={'backgroundColor':None}, className='h-75'
                    #style={'backgroundColor':'#2A3E4F', 'height':'155px'}
                    style={'backgroundColor':'#2A3E4F', 'height':'100%'}
                ),
            dbc.Row([],
                    style={'backgroundColor':'#2A3E4F', 'height':'2vh'},
                ),
            dbc.Row(
                    [# {{{
                        dbc.Col(time_plots, width={'size':10, 'offset':1}, lg={'size': 10, 'offset':1}),
                        ],# }}}
                    style={'backgroundColor':'#2A3E4F', 'height':'100%'},
                ),
            dbc.Row([],
                    style={'backgroundColor':'#2A3E4F', 'height':'2vh'},
                ),
            dbc.Row(
                    [
                        dbc.Col(
                            dbc.CardImg(src='/assets/AQUATIC_PHYSICS-Narrow-rgb_whiteletters.png', style={'width':'100%'}),
                            width={'offset':4, 'size':4},
                            lg={'offset':5, 'size':2}
                            )
                        ],
                    style={'backgroundColor':'#2A3E4F'}, align='center',
                ),
            dbc.Row([],
                    style={'backgroundColor':'#2A3E4F', 'height':'2vh'},
                ),
        ],
        style={'margin-left':0, 'margin-right':0, 'backgroundColor':'#1E2D39', 'height':'100%'}, fluid=True,
        #style={'margin-left':0, 'margin-right':0, 'backgroundColor':'#1E2D39', 'height':'40vh'}, fluid=True,
    )

#------------------------------------------------------------------
# Connect Plotly with Dash Components
selectedTS_prev = None
selectedMap_prev = None
@app.callback(
         [
             Output(component_id='map', component_property='figure'),# {{{
             Output(component_id='time-series', component_property='figure'),
             Output(component_id='average_value', component_property='children'),
             Output(component_id='time_series_title', component_property='children'),
             Output(component_id='map_title', component_property='children'),# }}}
             ],
         [
             Input(component_id='slct_var', component_property='value'),# {{{
             #Input(component_id='date-slider', component_property='value'),
             Input(component_id='date_range', component_property='start_date'),
             Input(component_id='date_range', component_property='end_date'),
             Input(component_id='map', component_property='selectedData'),
             Input('time-series', 'selectedData')# }}}
             ],
             )

def update_figures(option_slctd, start_date, end_date, selectedMap, selectedTS):
    global data
    global selectedTS_prev
    global selectedMap_prev

    dff = data.copy()
    selectedpoints = dff.index.values
    # Change in slider
    #mindate = dt.utcfromtimestamp(slider_value[0]*24*60)
    #maxdate = dt.utcfromtimestamp(slider_value[1]*24*60)
    if start_date is not None and end_date is not None:
        mindate = dt.strptime(start_date, '%Y-%m-%d')
        maxdate = dt.strptime(end_date, '%Y-%m-%d')
    else:
        mindate = dff.Datetime.min()
        maxdate = dff.Datetime.max()
    minindex = dff.loc[dff['Datetime'] >= mindate, :].index.values[0]
    maxindex = dff.loc[dff['Datetime'] >= maxdate, :].index.values[0]
    if selectedMap is not None and selectedMap_prev != selectedMap:
        selectedpoints = get_indexpoint(selectedMap)
        if selectedpoints:
            minindex = dff.loc[selectedpoints].Datetime.index.values[0]
            maxindex = dff.loc[selectedpoints].Datetime.index.values[-1]
            selectedMap_prev = selectedMap
    elif selectedTS is not None and selectedTS_prev != selectedTS:
        selectedpoints = get_indexpoint(selectedTS)
        if selectedpoints:
            minindex = dff.loc[selectedpoints].Datetime.index.values[0]
            maxindex = dff.loc[selectedpoints].Datetime.index.values[-1]
            selectedTS_prev = selectedTS
    # else:
    #     selectedpoints = selectedpoints[minindex:maxindex]
    colorscale, rev = colorscalesmap(option_slctd)
    figmap = create_map(dff, option_slctd, selectedpoints, colorscale, rev)
    figtime = create_time_series(dff, option_slctd, selectedpoints, minindex, maxindex)
    sc = dff.iloc[selectedpoints][option_slctd]
    average = sc.mean()
    average_str = 'Average value: %.2f %s' % (average, units(option_slctd))
    title_TS = title_timeseries(option_slctd)
    title_Map = title_timeseries(option_slctd, 'map')
    return figmap, figtime, average_str, title_TS, title_Map

def calc_zoom(min_lat, max_lat, min_lng, max_lng):

    width_y = max_lat - min_lat
    width_x = max_lng - min_lng
    zoom_y = -1.446*np.log(width_y) + 7.2753
    zoom_x = -1.415*np.log(width_x) + 8.7068
    return min(round(zoom_y, 2), round(zoom_x, 2))

def create_map(dff, option_slctd, selectedpoints, cscale, rev):# {{{
    unit = units(option_slctd)
    sc = dff[option_slctd]
    vmean = sc.iloc[selectedpoints].mean()
    nameev = namevar(option_slctd)
    midlat = (1.15*dff.Latitude.max()+dff.Latitude.min())/2.
    midlon = (dff.Longitude.max()+dff.Longitude.min())/2.
    zoom = calc_zoom(dff.Latitude.min(), dff.Latitude.max(), dff.Longitude.min(), dff.Longitude.max())
    fig = go.Figure()
    mapplot = go.Scattermapbox(# {{{
            lat=dff.Latitude,
            lon=dff.Longitude,
            visible=True,
            showlegend=False,
            text=dff.Date,
            name=nameev,
            customdata=dff[nameev],
            meta=unit,
            hovertemplate=# {{{
                '<b>Date</b>: %{text}' +
                '<br><b>Latitude</b>: %{lat:.2f}°N</br>' +
                '<b>Longitude</b>: %{lon:.2f}°E'
                '<br><b>Value</b>: %{customdata} %{meta}</br>',# }}}
            selectedpoints=selectedpoints,
            marker=dict(size=15, opacity=0.7, color=sc, showscale=True, colorscale=cscale, reversescale=rev, colorbar=dict(title=unit, len=1), cmid=vmean),
            unselected=dict(marker=dict(opacity=0.3, size=5, color='rgb(150,150,150)')),
              )# }}}
    mapbox = dict(# {{{
        # here you need the token from Mapbox
        accesstoken=mapbox_access_token,
        bearing=0,
        # where we want the map to be centered
        center=dict(lat=midlat, lon=midlon),
        # we want the map to be "parallel" to our screen, with no angle
        pitch=0,
        # default level of zoom
        zoom=zoom,
        # default map style

        # style="carto-positron" # "stamen-terrain" #"stamen-toner" #"stamen-watercolor" #"carto-darkmatter" #"carto-positron" #'stamen-terrain'
        style='mapbox://styles/ceordonezv/ckeiivabr4t9919qzavkja1mk'
        )# }}}
    # updatemenus=list([# {{{
    #     dict(# {{{
    #             buttons=list([
    #                 dict(
    #                     args=["marker.colorscale", "Cividis"],
    #                     label="Cividis",
    #                     method="restyle"
    #                 ),
    #                 dict(
    #                     args=["marker.colorscale", "Blues"],
    #                     label="Blues",
    #                     method="restyle"
    #                 ),
    #                 dict(
    #                     args=["marker.colorscale", "Greens"],
    #                     label="Greens",
    #                     method="restyle"
    #                 ),
    #             ]),
    #             direction="down",
    #             pad={"r": 10, "t": 10},
    #             showactive=True,
    #             x=1.01,
    #             xanchor="left",
    #             y=1.02,
    #             yanchor="bottom"
    #         ),# }}}
    #     dict(# {{{
    #            buttons=list([
    #                dict(
    #                    args=['mapbox.style', 'stamen-terrain'],
    #                    label='Stamen-terrain',
    #                    method='relayout'
    #                    ),
    #                dict(
    #                    args=['mapbox.style', 'stamen-watercolor'],
    #                    label='Stamen-watercolor',
    #                    method='relayout'
    #                    ),
    #                dict(
    #                    args=['mapbox.style', 'carto-darkmatter'],
    #                    label='Carto-darkmatter',
    #                    method='relayout'
    #                    )
    #                ]),
    #            direction='down',
    #            x=0.98,
    #            xanchor='right',
    #            y=0.95,
    #            yanchor='top'
    #            )# }}}
    # ])# }}}
    #fig.update_layout(
    #    mapbox_style="white-bg",
    #    mapbox_layers=[
    #        {
    #            "below": 'traces',
    #            "sourcetype": "raster",
    #            "source": [
    #                "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
    #            ]
    #        }
    #      ])
    fig.add_trace(mapplot)
    annotations = [dict(# {{{
            x=1.1,
            y=0.5,
            text='Average',
            yref='paper',
            xref='paper',
            showarrow=True,
            ax=-35,
            ay=0,
            )]# }}}
    fig.update_layout(
            mapbox=mapbox,
            height=900,
            margin=dict(t=35, b=25),
            autosize=True,
            uirevision='foo',
            #annotations=annotations,
        )
    return fig# }}}
def create_map2(dff, option_slctd, selectedpoints, cscale, rev):# {{{

    sc = dff[option_slctd]
    vmean = sc.iloc[selectedpoints].mean()
    vmax = sc.iloc[selectedpoints].max()
    vmin = sc.iloc[selectedpoints].min()
    vmax = vmean + max([abs(vmin-vmean), abs(vmax-vmin)])
    vmax = vmean - max([abs(vmin-vmean), abs(vmax-vmin)])
    unit = units(option_slctd)
    nameev = namevar(option_slctd)
    fig = go.Figure(
            go.Scattergeo(# {{{
                lat=dff.Latitude,
                lon=dff.Longitude,
                visible=True,
                showlegend=False,
                text=dff.Date,
                name=nameev,
                customdata=dff[nameev],
                meta=unit,
                hovertemplate=# {{{
                    '<b>Date</b>: %{text}' +
                    '<br><b>Latitude</b>: %{lat:.2f}°N</br>' +
                    '<b>Longitude</b>: %{lon:.2f}°E'
                    '<br><b>Value</b>: %{customdata} %{meta}</br>',# }}}
                selectedpoints=selectedpoints,
                marker=dict(size=10, opacity=0.7, color=sc, showscale=True, colorscale=cscale, reversescale=rev, colorbar=dict(title=unit, len=1), cmid=vmean),
                unselected=dict(marker=dict(opacity=0.3, size=5, color='rgb(150,150,150)')),
                )# }}}
        )
    fig.update_geos(# {{{
            #center=dict(lat=90),#, lon=0*dff.Longitude.mean()),
            #projection_rotation=dict(lat=90),
            projection=dict(type='azimuthal equal area'),
            fitbounds='locations',
            scope='world',
            lonaxis=dict(showgrid=True),# range=[-60, 60]),
            lataxis=dict(showgrid=True, dtick=5, range=[50, 90]),
            showsubunits=True,
            showcountries=True,
            showocean=True,
            resolution=50,
            landcolor="#3E3E3E",
            #landcolor="#E3E4EB",
            subunitcolor="rgb(255, 255, 255)",
            countrycolor="rgb(255, 255, 255)",
            coastlinecolor="rgb(255, 255, 255)",
            #countrycolor='black',#"rgb(255, 255, 255)",
            oceancolor="#2B3E50",
            #oceancolor="#4C5C7F",
            )# }}}
    fig.update_layout(# {{{
            height=800,
            width=800,
            autosize=True,
            #yaxis=dict(scaleanchor='x',scaleratio=1),
            margin={"r":20,"t":30,"l":30,"b":20},
            )# }}}
    return fig# }}}
def colorscalesmap(option_slctd):# {{{
    if option_slctd == 'CH4d_ppm':
        colorscale = px.colors.diverging.Geyser
        rev = False
    elif option_slctd == 'CO2d_ppm':
        colorscale = px.colors.diverging.RdYlBu
        rev = True
    elif option_slctd == 'Sal psu':
        colorscale = px.colors.sequential.OrRd
        rev = False
    elif option_slctd == 'Temp °C':
        colorscale = px.colors.sequential.RdBu
        rev = True
    elif option_slctd == 'ODO % sat':
        colorscale = px.colors.sequential.BuGn
        rev = False
    elif option_slctd == 'Turbidity FNU':
        colorscale = px.colors.sequential.Viridis
        rev = True
    elif option_slctd == 'SpCond µS/cm':
        colorscale = px.colors.sequential.OrRd
        rev = False
    return colorscale, rev# }}}

def title_timeseries(option_slctd, kind=None):# {{{
    if option_slctd in ('CH4d_ppm', 'CO2d_ppm'):
        title_timeseries = '%s concentration in the atmosphere %s' % (namevar(option_slctd), units(option_slctd))
    elif option_slctd in ('Sal psu', 'Temp °C', 'SpCond µS/cm', 'Turbidity FNU'):
        title_timeseries = 'Water %s %s' % (namevar(option_slctd).lower(), units(option_slctd))
    elif option_slctd in ('ODO % sat'):
        title_timeseries = '%s saturation in the water %s ' % (namevar(option_slctd), units(option_slctd))
   # elif option_slctd in ('Turbidity FNU'):
   #     title_timeseries = '%s in the water %s' % (namevar(option_slctd), units(option_slctd))
   # elif option_slctd in ('Cond µS/cm'):
   #     title_timeseries = '%s in the water %s' % name
    return title_timeseries# }}}

@app.callback(# {{{
        [
            #Output('date-slider', 'value'),
            Output('date_range', 'start_date'),
            Output('date_range', 'end_date'),
            Output('map', 'selectedData'),
            Output('time-series', 'selectedData')
            ],
        [
            Input(component_id='button-clear', component_property='n_clicks')
            ],
        )# }}}

def update(reset):# {{{
    global data
    dff = data.copy()
    t0 = unix_time_millis(dff.Datetime.min())
    tf = unix_time_millis(dff.Datetime.max())
    #return [t0, tf], None, None# }}}
    return None, None, None, None# }}}

def get_indexpoint(selectedMap):# {{{
    selectedpoint = []
    for point in selectedMap['points']:
        selectedpoint.append(point['pointIndex'])
    return selectedpoint# }}}



def create_time_series(dff, option_slctd, selectedpoints, minindex, maxindex):
    nameev = namevar(option_slctd)
    unit = units(option_slctd)
    sc = dff[option_slctd]
    mindate = dff.loc[selectedpoints].Datetime.min()
    maxdate = dff.loc[selectedpoints].Datetime.max()
    fig = go.Figure()
    TimeSeries = go.Scatter(x=dff.Datetime, y=sc, mode='markers',# {{{
            showlegend=False, visible=True, name=nameev, text=dff.Date, meta=unit,
            customdata=dff[nameev], hovertemplate=
            '<b>Date</b>: %{text}'+
            '<br><b>Value</b>: %{customdata} %{meta}</br>')# }}}
    layout = dict(
            template='seaborn',
            height=300,
            yaxis_title=' '.join([nameev, unit]),
            margin=dict(t=30, b=15, r=20, l=25),
            autosize=True,
            xaxis=dict(range=[mindate, maxdate]),
            )
    fig.update_layout(layout)
    fig.add_trace(TimeSeries)
    return fig

def namevar(option_slctd):# {{{
    if 'CO2' in option_slctd or 'CH4' in option_slctd:
        nameev = option_slctd[:3]
    elif 'Sal' in option_slctd:
        nameev = 'Salinity'
    elif 'Temp' in option_slctd:
        nameev = 'Temperature'
    elif 'ODO % sat' in option_slctd:
        nameev = 'Oxygen'
    elif 'Turbidity FNU' in option_slctd:
        nameev = 'Turbidity'
    elif 'SpCond µS/cm' in option_slctd:
        nameev = 'Specific Conductivity \U0001D725\u2082\u2085'
    return nameev# }}}

def units(option_slctd):# {{{
    units = '()'
    if 'CH4' in option_slctd or 'CO2' in option_slctd:
        units = '(ppm)'
    elif 'Temp' in option_slctd:
        units = '(°C)'
    elif 'Sal' in option_slctd:
        units = '(psu)'
    elif 'ODO' in option_slctd:
        units = '(%)'
    elif 'Turbidity' in option_slctd:
        units = '(FNU)'
    elif 'SpCond' in option_slctd:
        units = '(µS/cm)'
    return units# }}}

def update_graph(option_slctd, mindate, maxdate, selectedMap, selectedTS, btnclear):# {{{
    global data
    global mindatepicker
    global maxdatepicker
    global mapselector
    global tsselector
    global cleardata

    dff = data.copy()
    dff = dff.reset_index()
    selectedpoints = dff.index.values
    if mindate is not None and maxdate is not None and (mindatepicker != mindate or maxdatepicker != maxdate):
        # Case selection for datepicker
        maxdatepicker = maxdate
        mindatepicker = mindate
        mindate = dt.strptime(mindate, '%Y-%m-%d')
        maxdate = dt.strptime(maxdate, '%Y-%m-%d')
        minindex = dff.loc[dff['Datetime'] == mindate, :].index.values[0]
        maxindex = dff.loc[dff['Datetime'] == maxdate, :].index.values[0]
        selectedpoints = selectedpoints[minindex:maxindex+1]
        cleardata = False
    elif selectedMap is not None and mapselector != selectedMap:
        # case map selection
        selectedpoints = []
        for point in selectedMap['points']:
            selectedpoints.append(point['pointIndex'])
        mapselector = selectedMap
        cleardata = False
    elif selectedTS is not None and tsselector != selectedTS:
        # case time series selection
        selectedpoints = []
        for point in selectedTS['points']:
            selectedpoints.append(point['pointIndex'])
        tsselector = selectedTS
        cleardata = False
    else:
        # No selection
        cleardata = True
        selectedpoints = dff.index.values
        dff = data.copy()
    # if mindate is None and maxdate is None and mindatepicker is not None and maxdatepicker is not None:{{{
    # Case with clearable datepicker
    #     selectedpoints = dff.index.values
    #     maxdatepicker = maxdate
    #     mindatepicker = mindate
    #     cleardata = True
    #     dff = data.copy()}}}
    change_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-clear' in change_id:
        cleardata = True
        selectedpoints = dff.index.values
        dff = data.copy()
    dff = dff.reset_index()
    sc = dff[option_slctd]
    figmap = create_map2(dff, namevar(option_slctd), selectedpoints, sc, units(option_slctd))
    #figmap = create_map(dff, namevar(option_slctd), selectedpoints, sc, units(option_slctd))
    figtime = create_time_series(dff, sc, namevar(option_slctd), mindate, maxdate, selectedpoints, cleardata, units(option_slctd))
    return figmap, figtime# }}}

#             Output(component_id='map', component_property='figure'),{{{
#          Output(component_id='time-series', component_property='figure')],
#        [])
#         [Input(component_id='slct_var', component_property='value'),
#          Input(component_id='date-picker', component_property='start_date'),
#          Input(component_id='date-picker', component_property='end_date'),
#          Input(component_id='time-series', component_property='selectedData'),
#          Input(component_id='button-clear', component_property='n_clicks')])}}}
#------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=False)
