import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.io as pio

def plot_data(data):
    """TODO: Docstring for plot_data.

    Parameters
    ----------
    LGRdata : TODO
    GPSdata : TODO

    Returns
    -------
    TODO

    """

    plot_timeseries(data)

    #plot_map(data)
    #combinated_plots(data)


def plot_timeseries(data):
    """TODO: Docstring for plot_timeseries.

    Parameters
    ----------
    LGRdata : TODO

    Returns
    -------
    TODO

    """
    # Create figure
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=list(data.Datetime), y=list(data.CH4d_ppm)))
    # Add range slider
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        )
    )

    #fig.show()
    pio.write_html(fig, 'timeseries_LGR.html', auto_open=False)

def plot_map(data):
    """TODO: Docstring for plot_map.

    Parameters
    ----------
    data : TODO

    Returns
    -------
    TODO

    """
    data['Date'] = data['Datetime'].dt.strftime('%d-%m-%Y %H:%M')
    data['CH4'] = data['CH4d_ppm'].round(2).astype(str)
    data['CO2'] = data['CO2d_ppm'].round(1).astype(str)

    plotdata = []
    for event in ['CH4d_ppm', 'CO2d_ppm']:
        ssc = True
        sc = data[event]
        nameev = event[:3]
        if 'CO2' in event:
            visible = True
        else:
            visible = False
        event_data = dict(# {{{
                lat=data.Latitude,
                lon=data.Longitude,
                name=nameev,
                marker=dict(size=15, opacity=.5, color=sc, showscale=ssc, colorscale=px.colors.sequential.Cividis, colorbar=dict(title="(ppm)")),
                text=data.Date,
                customdata=data[nameev],
                visible=visible,
                type='scattermapbox',
                hovertemplate=
                   '<b>Date</b>: %{text}' +
                   '<br><b>Latitude</b>: %{lat:.2f}°N</br>' +
                   '<b>Longitude</b>: %{lon:.2f}°E'
                   '<br><b>Value</b>: %{customdata} (ppm)</br>'
        )# }}}
        plotdata.append(event_data)

    layout = dict(# {{{
        #height = 800,
        # top, bottom, left and right margins
        margin = dict(t = 0, b = 0, l = 0, r = 0),
        #font = dict(color = '#FFFFFF', size = 11),
        #paper_bgcolor = '#000000',
        showlegend=False,
        mapbox = dict(# {{{
            # here you need the token from Mapbox
            # accesstoken = mapbox_access_token,
            bearing=0,
            # where we want the map to be centered
            center=dict(lat=60, lon=4),
            # we want the map to be "parallel" to our screen, with no angle
            pitch=0,
            # default level of zoom
            zoom=3,
            # default map style
            style="stamen-terrain" #"stamen-toner" #"stamen-watercolor" #"carto-darkmatter" #"carto-positron" #'stamen-terrain'
            )# }}}
        )# }}}
    updatemenus=list([# {{{
    dict(# {{{
          # for each button I specify which dictionaries of my data list I want to visualize. Remember I have 7 different
          # types of storms but I have 8 options: the first will show all of them, while from the second to the last option, only
          # one type at the time will be shown on the map
          buttons=list([
             dict(label='Carbon Dioxide',
                  method='update',
                  args=[{'visible': [False, True]}]),
             dict(label='Methane',
                  method='restyle',
                  args=[{'visible': [True, False]}])

         ]),
         # direction where the drop-down expands when opened
         type="buttons",
         direction='right',
         # positional arguments
         x=0.1,
         xanchor='left',
         y=1.12,
         yanchor='top',
         # fonts and border
         #bgcolor = '#000000',
         #bordercolor = '#FFFFFF',
         font=dict(size=11)
         ),# }}}
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
            direction="down",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.1,
            xanchor="left",
            y=1.07,
            yanchor="top"
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
           direction='up',
           x=0.9,
           xanchor='left',
           y=0.05,
           yanchor='top'
           )# }}}
    ])# }}}
    layout["annotations"] = [# {{{
        dict(text="Colorscale", x=0, xref="paper", y=1.05, yref="paper",
                             align="left", showarrow=False),
        dict(text="Variable", x=0, xref="paper", y=1.12, yref="paper",
                             align="left", showarrow=False)
        ]# }}}
    # assign the list of dictionaries to the layout dictionary
    layout['updatemenus'] = updatemenus
    fig = go.Figure(dict(data=plotdata, layout=layout))
    #fig.show()
    pio.write_html(fig, 'map_data.html', auto_open=False)


def combinated_plots(data):

    fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.5, 0.5],
            specs=[[{"type": "scattermapbox"}], [{"type":"xy"}]])
    fig.add_trace(go.Scattermapbox(lat=data['Latitude'], lon=data['Longitude'], mode='markers+text', customdata=data, showlegend=False, marker=dict(color=data['CH4d_ppm'], size=10, showscale=True),
       hovertemplate=
       '<b>Date</b>: %{customdata[5]}' +
       '<br><b>Latitude</b>: %{lat:.2f}</br>' +
       '<b>Longitude</b>: %{lon:.2f}'+
       '<br><b>CH4</b>: %{customdata[6]} (ppm)</br><extra></extra>',
       subplot='mapbox'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data['Datetime'], y=data['CH4d_ppm'], showlegend=False), row=2, col=1)
    fig.update_layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        style='stamen-terrain',
        bearing=0,
        center=dict(
            lat=45,
            lon=-73
        ),
        pitch=0,
        zoom=5
    ))
    fig.update_layout(margin=dict(r=10, t=25, b=40, l=60))
    fig.show()
