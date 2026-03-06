# dashboard/app.py
import os
import base64
import pandas as pd
from io import StringIO
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State

# ----------------------
# Initialize app
# ----------------------
app = Dash(__name__)
server = app.server  # WSGI callable for Render

# Sample initial dataset
df = pd.DataFrame({
    'Price': [200000, 250000, 300000, 350000, 400000],
    'Latitude': [34.05, 34.07, 34.06, 34.08, 34.09],
    'Longitude': [-118.25, -118.24, -118.26, -118.23, -118.22],
    'PropertyType': ['House','Condo','House','Condo','House'],
    'Bedrooms': [3,2,4,2,5]
})

# ----------------------
# Layout
# ----------------------
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("AI Real Estate Valuation Dashboard", style={'margin':'0', 'fontSize':'24px'}),
        html.Div([
            html.Label("Theme:"),
            dcc.RadioItems(
                id="theme-radio",
                options=[{"label": "Light", "value": "light"}, {"label": "Dark", "value": "dark"}],
                value="light",
                labelStyle={"display": "inline-block", "margin-right": "10px"}
            )
        ], style={'display':'inline-block', 'margin-left':'20px'}),
        html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div(['Drag and Drop or ', html.A('Select CSV Files')]),
                style={'display':'inline-block','padding':'6px 12px','margin-left':'20px',
                       'borderWidth': '1px','borderStyle': 'dashed','borderRadius': '5px','cursor':'pointer'},
                multiple=True
            )
        ], style={'display':'inline-block', 'margin-left':'20px'}),
        html.Div([
            html.Button("Download Filtered CSV", id="download-btn", n_clicks=0,
                        style={'padding':'6px 12px', 'margin-left':'20px', 'cursor':'pointer'}),
            dcc.Download(id="download-data")
        ], style={'display':'inline-block'})
    ], className='sticky-header'),

    # Main content: filters + dashboard
    html.Div([
        # Filter panel
        html.Div([
            html.H4("Filters", style={'margin-bottom':'10px'}),
            
            html.Label("Price Range"),
            dcc.RangeSlider(id='price-slider', min=df['Price'].min(), max=df['Price'].max(),
                            step=1000, value=[df['Price'].min(), df['Price'].max()],
                            tooltip={"placement": "bottom", "always_visible": True}),
            
            html.Label("Latitude Range", style={'margin-top':'20px'}),
            dcc.RangeSlider(id='lat-slider', min=df['Latitude'].min(), max=df['Latitude'].max(),
                            step=0.001, value=[df['Latitude'].min(), df['Latitude'].max()],
                            tooltip={"placement": "bottom", "always_visible": True}),
            
            html.Label("Longitude Range", style={'margin-top':'20px'}),
            dcc.RangeSlider(id='lon-slider', min=df['Longitude'].min(), max=df['Longitude'].max(),
                            step=0.001, value=[df['Longitude'].min(), df['Longitude'].max()],
                            tooltip={"placement": "bottom", "always_visible": True}),
            
            html.Label("Property Type", style={'margin-top':'20px'}),
            dcc.Dropdown(
                id='property-type-dropdown',
                options=[{'label': t, 'value': t} for t in df['PropertyType'].unique()],
                multi=True,
                placeholder="Select property type"
            ),
            
            html.Label("Bedrooms", style={'margin-top':'20px'}),
            dcc.Dropdown(
                id='bedrooms-dropdown',
                options=[{'label': str(b), 'value': b} for b in sorted(df['Bedrooms'].unique())],
                multi=True,
                placeholder="Select number of bedrooms"
            ),
        ], className='filter-panel'),

        # Dashboard row
        html.Div([
            html.Div(dcc.Graph(id='scatter-plot'), className='dashboard-col'),
            html.Div(dcc.Graph(id='price-histogram'), className='dashboard-col'),
            html.Div([
                html.Div(id='stats-cards', style={'marginBottom':'20px'}),
                html.H3("Prediction History"),
                dcc.Graph(id='prediction-history-graph')
            ], className='dashboard-col')
        ], className='dashboard-row')
    ], className='main-container', style={'display':'flex', 'flexWrap':'wrap', 'gap':'20px'}),

    # Hidden storage for prediction history
    dcc.Store(id='prediction-history', data=[])
])

# ----------------------
# CSV parser
# ----------------------
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.csv'):
            return pd.read_csv(StringIO(decoded.decode('utf-8')))
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return pd.DataFrame()

# ----------------------
# Dashboard callback
# ----------------------
@app.callback(
    Output('scatter-plot', 'figure'),
    Output('price-histogram', 'figure'),
    Output('stats-cards', 'children'),
    Output('prediction-history', 'data'),
    Input('upload-data', 'contents'),
    Input('upload-data', 'filename'),
    Input('theme-radio', 'value'),
    Input('price-slider', 'value'),
    Input('lat-slider', 'value'),
    Input('lon-slider', 'value'),
    Input('property-type-dropdown', 'value'),
    Input('bedrooms-dropdown', 'value'),
    State('prediction-history', 'data')
)
def update_dashboard(contents, filenames, theme, price_range, lat_range, lon_range, property_types, bedrooms, history):
    global df
    # Append uploaded CSVs
    if contents:
        df_list = [parse_contents(c, f) for c, f in zip(contents, filenames)]
        uploaded_df = pd.concat(df_list, ignore_index=True)
        df = pd.concat([df, uploaded_df], ignore_index=True)

    # Filter dataset
    filtered_df = df[
        (df['Price'] >= price_range[0]) & (df['Price'] <= price_range[1]) &
        (df['Latitude'] >= lat_range[0]) & (df['Latitude'] <= lat_range[1]) &
        (df['Longitude'] >= lon_range[0]) & (df['Longitude'] <= lon_range[1])
    ]
    if property_types:
        filtered_df = filtered_df[filtered_df['PropertyType'].isin(property_types)]
    if bedrooms:
        filtered_df = filtered_df[filtered_df['Bedrooms'].isin(bedrooms)]

    # Dummy prediction
    predicted_price = int(filtered_df['Price'].mean()) if not filtered_df.empty else 0
    avg_price = int(filtered_df['Price'].mean()) if not filtered_df.empty else 0
    max_price = int(filtered_df['Price'].max()) if not filtered_df.empty else 0
    min_price = int(filtered_df['Price'].min()) if not filtered_df.empty else 0

    # Update prediction history
    history.append({'time': str(pd.Timestamp.now()), 'price': predicted_price})
    if len(history) > 10:
        history = history[-10:]

    # Stats cards
    cards = html.Div([
        html.Div(f"Predicted Price: ${predicted_price:,}", className="stat-card"),
        html.Div(f"Avg Price: ${avg_price:,}", className="stat-card"),
        html.Div(f"Max Price: ${max_price:,}", className="stat-card"),
        html.Div(f"Min Price: ${min_price:,}", className="stat-card")
    ], style={'display':'flex','flexWrap':'wrap','gap':'10px'})

    # Scatter plot with map overlay
    scatter_fig = go.Figure(go.Scattermapbox(
        lat=filtered_df['Latitude'],
        lon=filtered_df['Longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(size=12, color='blue'),
        text=filtered_df.apply(lambda r: f"Price: ${r['Price']}\nBedrooms: {r['Bedrooms']}\nType: {r['PropertyType']}", axis=1)
    ))
    scatter_fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=10,
        mapbox_center={"lat": filtered_df['Latitude'].mean() if not filtered_df.empty else 34.05,
                       "lon": filtered_df['Longitude'].mean() if not filtered_df.empty else -118.25},
        margin={"l":0,"r":0,"t":30,"b":0},
        title="Property Locations (Map Overlay)"
    )

    # Histogram
    hist_fig = go.Figure(go.Histogram(x=filtered_df['Price'], nbinsx=20, name='Price'))
    hist_fig.add_trace(go.Scatter(
        x=[predicted_price, predicted_price],
        y=[0, filtered_df['Price'].value_counts().max() if not filtered_df.empty else 0],
        mode='lines', line=dict(color='red', width=2), name='Predicted Price'
    ))
    hist_fig.update_layout(title="Price Distribution", transition={'duration':500,'easing':'cubic-in-out'})

    return scatter_fig, hist_fig, cards, history

# ----------------------
# Download callback
# ----------------------
@app.callback(
    Output("download-data", "data"),
    Input("download-btn", "n_clicks"),
    prevent_initial_call=True
)
def download_filtered(n_clicks):
    global df
    return dcc.send_data_frame(df.to_csv, "filtered_real_estate_data.csv", index=False)

# ----------------------
# Run server
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=True)