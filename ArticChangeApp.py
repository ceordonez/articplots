
import pandas as pd
from datetime import datetime as dt

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
# --------------------
# Read data
data = pd.read_csv('AllData.csv', parse_dates=[1], index_col=[0])
data = data.set_index('Datetime')
data = data.resample('60T').mean()
data = data.reset_index()
data['Date'] = data['Datetime'].dt.strftime('%d-%m-%y %H:%M')
data['CH4'] = data['CH4d_ppm'].round(2).astype(str)
data['CO2'] = data['CO2d_ppm'].round(1).astype(str)
mapbox_access_token = open(".mapbox_token").read()
lastloc = '%.2f°N, %.2f°E'  % (data['Latitude'].iloc[-1], data['Longitude'].iloc[-1])
lastime = data['Date'].iloc[-1]
mindatepicker = None
maxdatepicker = None
mapselector = None
tsselector = None
cleardata = True

# --------------------
# App layout

app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div([
        html.H2('Mauritius Information'),
        html.H4('Last location reported: %s' % lastloc),
        html.H4('Last date reported: %s' % lastime),
        html.H2('General selections'),
        html.Label(['Choose variable:'], style={'font-weight': 'bold', 'text-align': 'center'}),
        dcc.Dropdown(id='slct_var',# {{{
            options=[
                {"label":"Carbon Dioxide", "value":'CO2d_ppm'},
                {"label":"Methane", "value":"CH4d_ppm"},
                {"label":"Temperature", "value":"Temp", "disabled":True},
                {"label":"Salinity", "value":"Temp", "disabled":True},
                ],
            multi=False,
            optionHeight=35,
            value='CO2d_ppm',
            searchable=True,
            placeholder='Please select...',
            style={'width':"100%"},
            clearable=False,
            ),# }}}
        html.Br(),
        html.Label(['Select Dates: '], style={'font-weight': 'bold', 'text-align': 'center'}),
        html.Div([
            html.Div([dcc.DatePickerRange(
                id='date-picker',
                min_date_allowed=data['Datetime'].min(),
                max_date_allowed=data['Datetime'].max(),
                initial_visible_month=data['Datetime'].mean(),
                clearable=False,
                display_format='D.M.YYYY')],
                style={'display': 'inline-block', 'padding': '10px 30px'}),
            html.Div([html.Button('Clear Selection', id='button-clear', n_clicks=0)], 
                style={'display': 'inline-block'}),
            ]),
        ],
        style={'width': '29%', 'display': 'inline-block', 'padding': '10px 10px',
            'BorderBottom': 'thin lightgrey solid', 'backgroundColor':'rgb(250,250,250)'}),
    html.Div([
        dcc.Graph(id='map', figure={}),
        dcc.Graph(id='time-series', figure={})
        ], style={'width':'69%', 'display': 'inline-block', 'float': 'right'})
    ])
# --------------------
# Connect Plotly with Dash Components
@app.callback(
        [Output(component_id='map', component_property='figure'),
         Output(component_id='time-series', component_property='figure')],
        [Input(component_id='slct_var', component_property='value'),
         Input(component_id='date-picker', component_property='start_date'),
         Input(component_id='date-picker', component_property='end_date'),
         Input(component_id='map', component_property='selectedData'),
         Input(component_id='time-series', component_property='selectedData'),
         Input(component_id='button-clear', component_property='n_clicks')])

def update_graph(option_slctd, mindate, maxdate, selectedMap, selectedTS, btnclear):
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
    nameev = option_slctd[:3]
    figmap = create_map(dff, nameev, selectedpoints, sc)
    figtime = create_time_series(dff, sc, nameev, mindate, maxdate, selectedpoints, cleardata)
    return figmap, figtime

def create_map(dff, nameev, selectedpoints, sc):
    fig = go.Figure()
    mapplot = go.Scattermapbox(# {{{
            lat=dff.Latitude,
            lon=dff.Longitude,
            visible=True,
            showlegend=False,
            text=dff.Date,
            name=nameev,
            customdata=dff[nameev],
            hovertemplate=# {{{
                '<b>Date</b>: %{text}' +
                '<br><b>Latitude</b>: %{lat:.2f}°N</br>' +
                '<b>Longitude</b>: %{lon:.2f}°E'
                '<br><b>Value</b>: %{customdata} (ppm)</br>',# }}}
            selectedpoints=selectedpoints,
            marker=dict(size=15, opacity=0.7, color=sc, showscale=True, colorscale=px.colors.sequential.Cividis, colorbar=dict(title="(ppm)", len=1)),
            unselected=dict(marker=dict(opacity=0.3, size=5, color='rgb(150,150,150)')),
              )# }}}
    mapbox = dict(# {{{
        # here you need the token from Mapbox
        accesstoken=mapbox_access_token,
        bearing=0,
        # where we want the map to be centered
        center=dict(lat=dff.Latitude.mean(), lon=dff.Longitude.mean()),
        # we want the map to be "parallel" to our screen, with no angle
        pitch=0,
        # default level of zoom
        zoom=1,
        # default map style
        style="stamen-terrain" #"stamen-toner" #"stamen-watercolor" #"carto-darkmatter" #"carto-positron" #'stamen-terrain'
        )# }}}
    updatemenus=list([# {{{
    dict(# {{{
            buttons=list([
                dict(
                    args=["marker.colorscale", "Cividis"],
                    label="Cividis",
                    method="restyle"
                ),
                dict(
                    args=["marker.colorscale", "Blues"],
                    label="Blues",
                    method="restyle"
                ),
                dict(
                    args=["marker.colorscale", "Greens"],
                    label="Greens",
                    method="restyle"
                ),
            ]),
            direction="up",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=1.01,
            xanchor="left",
            y=1.02,
            yanchor="bottom"
        ),# }}}
    dict(# {{{
           buttons=list([
               dict(
                   args=['mapbox.style','stamen-terrain'],
                   label='Stamen-terrain',
                   method='relayout'
                   ),
               dict(
                   args=['mapbox.style','stamen-watercolor'],
                   label='Stamen-watercolor',
                   method='relayout'
                   ),
               dict(
                   args=['mapbox.style','carto-darkmatter'],
                   label='Carto-darkmatter',
                   method='relayout'
                   )
               ]),
           direction='down',
           x=0.98,
           xanchor='right',
           y=0.95,
           yanchor='top'
           )# }}}
    ])# }}}
    fig.update_layout(
            mapbox=mapbox, updatemenus=updatemenus,
        )
    fig.add_trace(mapplot)
    return fig

def create_time_series(dff, sc, nameev, mindate, maxdate, selectedpoints, cleardata):
    fig = go.Figure()
    TimeSeries = go.Scatter(x=dff.Datetime, y=sc, mode='markers',# {{{
            showlegend=False, visible=True, name=nameev, text=dff.Date,
            customdata=dff[nameev], hovertemplate=
            '<b>Date</b>: %{text}'+
            '<br><b>Value</b>: %{customdata} (ppm)</br>')# }}}
    layout = dict(
            yaxis_title=nameev + ' (ppm)')
    if not cleardata:
        df = dff.loc[selectedpoints]
        mindate = df['Datetime'].min()
        maxdate = df['Datetime'].max()
        layout = dict(
                yaxis_title=nameev + ' (ppm)',
                xaxis=dict(range=[mindate, maxdate])
                )
    fig.update_layout(layout)
    fig.add_trace(TimeSeries)
    return fig

if __name__=="__main__":
    app.run_server(debug=True)
