# DASH Application to plot choropleth map from NetCDF data

# Imports
import json
import xarray as xr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
import time as tme

# Convert Numpy DT64 to datetime
def npdt64todt(npdt):
    rounded = []
    for d in npdt:
        ts = (d - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')
        dt = datetime.utcfromtimestamp(ts)

        if dt.microsecond / 1000000 > 0.5:
            rounded.append((dt + timedelta(seconds=1)).replace(microsecond=0))
        else:
            rounded.append(dt.replace(microsecond=0))
    return rounded

# Create the Dash app
app = dash.Dash()

# Open the target dataset
nc = xr.open_dataset('temp.nc')

# Read in the cell geometry
with open('cells.geojson') as json_file:
    cells = json.load(json_file)


target='temp'
time='0'
depth='-1'

# Determine the map center and time ranges
df = nc['temp'][0, -1, :, :].to_dataframe()
map_center = {"lat": df['latitude'].median(skipna=True), "lon": df['longitude'].median(skipna=True)}
timerange = npdt64todt(nc['time'].values.flatten())
cellids = ['c' + ('_r'.join(map(str, x))) for x in df.index.values]

# Build the initial map
def make_map(var='temp',t=0,d=-1):
    # Create a temperature map from the surface layer at t0
    df = nc[var][t, d, :, :].to_dataframe()
    varlst = df[var].to_list()
    # Package into a dataframe and calculate the min and max ranges for the colourbar
    df = pd.DataFrame(list(zip(cellids, varlst)), columns=['cellid', target])
    min_range = np.nanpercentile(varlst, 5)
    max_range = np.nanpercentile(varlst, 95)
    # return an initial choropleth map using the loaded geojson and cell values.
    return (go.Choroplethmapbox(geojson=cells, locations=df.cellid, z=df.temp, colorscale="Viridis", zmin=min_range, zmax=max_range, marker_line_width=0.2, visible=True))

# Create an initial layout
layout = go.Layout(mapbox_style="carto-positron",mapbox_zoom=6, mapbox_center = map_center,margin={"r":0,"t":0,"l":0,"b":0})
# Create the figure
fig = go.Figure(data=[make_map()], layout=layout)

# Create a slider for the time values in the NetCDF file
slide = dcc.Slider(id='slide',min=0,max=len(timerange)-1,step=1,value=0,marks={c: '{}'.format(v.strftime("%Y-%m-%dT%H:%M:%S")) for c,v in enumerate(timerange) if ((c % 12) == 0)})

# Create a Dash layout
app.layout = html.Div([dcc.Graph(id="plot",style={'height': '80vh'},figure=fig),slide])

# Create the callback and callback function (update_figure)
@app.callback(Output('plot', 'figure'),
              [Input('slide', 'value')],
              [State('plot','relayoutData'),State('plot', 'figure')])
def update_figure(x,r,f):
    t0 = tme.time()
    f['layout']['mapbox']['center']['lat'] = f['layout']['mapbox']['center']['lat']
    f['layout']['mapbox']['center']['lon'] = f['layout']['mapbox']['center']['lon']
    f['layout']['mapbox']['zoom'] = f['layout']['mapbox']['zoom']

    # If the map window has been panned or zoomed, grab those values for the new figure
    if r is not None:
        if 'mapbox.center' in r:
            f['layout']['mapbox']['center']['lat'] = r['mapbox.center']['lat']
            f['layout']['mapbox']['center']['lon'] = r['mapbox.center']['lon']
            f['layout']['mapbox']['zoom'] = r['mapbox.zoom']

    # Extract the new time values from the NetCDF file
    tmp = nc['temp'][x, -1, :, :].values.flatten()
    # Repace the Z values in the original figure with the updated values, leave everything else (e.g. cell geojson and max/min ranges) as-is
    f['data'][0]['z'] = np.where(np.isnan(tmp), None, tmp).tolist()
    print("update_figure() time: ",tme.time()-t0)
    return f

if __name__ == '__main__':
    app.run_server(debug=True)