import datashader as ds, xarray as xr
from datashader import transfer_functions as tf
import plotly.express as px

nc = xr.open_dataset('temp.nc')
Z = nc['temp'][0, -1, :,:].values
Qy = nc['latitude'][:,:].values
Qx = nc['longitude'][:,:].values

df = nc['temp'][0, -1,:,:].to_dataframe()
df.index = ['c' + ('_r'.join(map(str, tuple(v+1 for v in x)))) for x in df.index.values]

coordinates = [[min(df['longitude']), min(df['latitude'])],
               [max(df['longitude']), min(df['latitude'])],
               [max(df['longitude']), max(df['latitude'])],
               [min(df['longitude']), max(df['latitude'])]]

print(coordinates)

da = xr.DataArray(Z, name='Z', dims = ['y', 'x'],coords={'Qy': (['y', 'x'], Qy),'Qx': (['y', 'x'], Qx)})

canvas = ds.Canvas(plot_width=2000,plot_height=2000)
img = tf.shade(canvas.quadmesh(da, x='Qx', y='Qy'))[::-1].to_pil()
#dsutil.export_image(img=img,filename='Oct2431doshade.png', fmt=".png", background=None)

fig = px.scatter_mapbox(df.dropna(), lat='latitude', lon='longitude')
fig.update_layout(mapbox_style="carto-darkmatter",mapbox_layers=[{"sourcetype": "image", "source": img, "below": 'traces', "coordinates": coordinates, "opacity": 0.5}])
fig.write_html('quadmesh_demo.html', auto_open=True)