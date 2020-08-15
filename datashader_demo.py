import xarray as xr
import json
import geopandas as gpd
import spatialpandas as spd
from colorcet import fire
import datashader.transfer_functions as tf

'''Simple DataShader Projection Issue Example'''

# Set whether to reproject the data to web mercator (from EPSG:4326) before running datashader:
reprojectToWebMercator = False

# Set whether to generate datashader polygons. If false, generates points instead:
datashaderPolygons = True

# Set whether to overlay Mapbox Choropleth alongside Datashader result. If false, renders Mapbox Scatter alongside instead:
mapboxChoropleth = False

# Read the target dataset
nc = xr.open_dataset('temp.nc')
df = nc['temp'][0, -1, 1:-1, 1:-1].to_dataframe()
df.index = ['c' + ('_r'.join(map(str, tuple(v+1 for v in x)))) for x in df.index.values]

# Read in polygon boundaries:
with open('cells.geojson') as json_file:
    cells = json.load(json_file)
gdf = gpd.read_file('cells.geojson')

if reprojectToWebMercator:
    gdf = gdf.to_crs(epsg=3857)
gdf.set_index('id',inplace=True)

# Merge with data values from NetCDF DF based on index:
gdf = gdf.join(df)

# Create datashader polygons:
import datashader as ds
cvs = ds.Canvas(plot_width=2000, plot_height=2000)
if datashaderPolygons:
    agg = cvs.polygons(spd.GeoDataFrame(gdf), geometry='geometry',agg=ds.mean('temp'))
    coords_lat, coords_lon = agg.coords['y'].values, agg.coords['x'].values
else:
    agg = cvs.points(df, x='longitude', y='latitude',agg=ds.mean('temp'))
    coords_lat, coords_lon = agg.coords['latitude'].values, agg.coords['longitude'].values

# Corners of the image, which need to be passed to mapbox
coordinates = [[coords_lon[0], coords_lat[0]],
               [coords_lon[-1], coords_lat[0]],
               [coords_lon[-1], coords_lat[-1]],
               [coords_lon[0], coords_lat[-1]]]

img = tf.shade(agg, cmap=fire)[::-1].to_pil()

if mapboxChoropleth:
    import plotly.graph_objects as go
    fig = go.Figure(go.Choroplethmapbox(geojson=cells, locations=df.cellid))
else:
    import plotly.express as px
    fig = px.scatter_mapbox(df.dropna(), lat='latitude', lon='longitude')

# Add the datashader image as a mapbox layer image
fig.update_layout(mapbox_style="carto-darkmatter",
                 mapbox_layers = [
                {
                    "sourcetype": "image",
                    "source": img,
                    "below": 'traces',
                    "coordinates": coordinates,
                    "opacity": 0.5
                }]
                  )
fig.write_html('datashader_demo.html', auto_open=True)