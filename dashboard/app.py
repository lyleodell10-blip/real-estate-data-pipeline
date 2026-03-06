import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np

# ------------------------------
# Sample data (replace with your real dataset)
# ------------------------------
df = pd.DataFrame({
    'latitude': [34.05, 34.10, 34.12, 34.07],
    'longitude': [-118.25, -118.28, -118.30, -118.27],
    'price': [500000, 650000, 700000, 550000],
    'bedrooms': [2, 3, 4, 3],
    'bathrooms': [1, 2, 3, 2],
    'sqft': [1200, 1600, 2000, 1500],
    'property_type': ['House', 'Condo', 'House', 'Condo']
})

# Predicted price function (replace with your AI model)
def predict_price(lat, lon, bedrooms=None, bathrooms=None, sqft=None, property_type=None):
    # Dummy example: base mean price adjusted by features
    price = df['price'].mean()
    if bedrooms: price += bedrooms * 20000
    if bathrooms: price += bathrooms * 15000
    if sqft: price += (sqft - 1500) * 50
    return price

# ------------------------------
# Initialize Dash app
# ------------------------------
app = dash.Dash(__name__)
app.title = "Interactive AI Valuation Dashboard"

# ------------------------------
# Layout
# ------------------------------
app.layout = html.Div([
    html.H2("AI Real Estate Valuation Dashboard", style={'textAlign': 'center'}),
    
    # Controls
    html.Div([
        html.Div([
            html.Label("Latitude"),
            dcc.Slider(
                id='lat-slider', min=df['latitude'].min(), max=df['latitude'].max(),
                step=0.01, value=df['latitude'].mean(),
                marks={round(lat,2): str(round(lat,2)) for lat in df['latitude']}
            ),
        ], style={'marginBottom':'10px'}),
        
        html.Div([
            html.Label("Longitude"),
            dcc.Slider(
                id='lon-slider', min=df['longitude'].min(), max=df['longitude'].max(),
                step=0.01, value=df['longitude'].mean(),
                marks={round(lon,2): str(round(lon,2)) for lon in df['longitude']}
            ),
        ], style={'marginBottom':'10px'}),
        
        html.Div([
            html.Label("Bedrooms"),
            dcc.Dropdown(
                id='bedrooms-dropdown',
                options=[{'label': b, 'value': b} for b in sorted(df['bedrooms'].unique())],
                value=3
            ),
        ], style={'width':'30%', 'display':'inline-block', 'marginRight':'10px'}),
        
        html.Div([
            html.Label("Bathrooms"),
            dcc.Dropdown(
                id='bathrooms-dropdown',
                options=[{'label': b, 'value': b} for b in sorted(df['bathrooms'].unique())],
                value=2
            ),
        ], style={'width':'30%', 'display':'inline-block', 'marginRight':'10px'}),
        
        html.Div([
            html.Label("Property Type"),
            dcc.Dropdown(
                id='type-dropdown',
                options=[{'label': t, 'value': t} for t in df['property_type'].unique()],
                value='House'
            ),
        ], style={'width':'30%', 'display':'inline-block'}),
        
    ], style={'width':'80%', 'margin':'auto'}),
    
    # Charts row
    html.Div([
        dcc.Graph(id='scatter-plot', style={'width':'48%', 'display':'inline-block'}),
        dcc.Graph(id='price-histogram', style={'width':'48%', 'display':'inline-block'}),
    ], style={'display':'flex', 'justifyContent':'space-between'}),
    
    # Stats cards
    html.Div([
        html.Div(id='pred-price-card', style={'width':'30%', 'display':'inline-block', 'padding':'10px', 'border':'1px solid black', 'marginRight':'10px'}),
        html.Div(id='avg-price-card', style={'width':'30%', 'display':'inline-block', 'padding':'10px', 'border':'1px solid black', 'marginRight':'10px'}),
        html.Div(id='percentile-card', style={'width':'30%', 'display':'inline-block', 'padding':'10px', 'border':'1px solid black'}),
    ], style={'width':'80%', 'margin':'20px auto', 'textAlign':'center'}),
    
    # Download button
    html.Div([
        html.Button("Download Charts Snapshot", id="download-btn"),
        dcc.Download(id="download-charts")
    ], style={'width':'80%', 'margin':'auto', 'textAlign':'center', 'paddingTop':'10px'})
    
], style={'fontFamily':'Arial'})

# ------------------------------
# Callbacks
# ------------------------------
@app.callback(
    Output('scatter-plot', 'figure'),
    Output('price-histogram', 'figure'),
    Output('pred-price-card', 'children'),
    Output('avg-price-card', 'children'),
    Output('percentile-card', 'children'),
    Input('lat-slider', 'value'),
    Input('lon-slider', 'value'),
    Input('bedrooms-dropdown', 'value'),
    Input('bathrooms-dropdown', 'value'),
    Input('type-dropdown', 'value')
)
def update_charts(lat, lon, bedrooms, bathrooms, property_type):
    # Predicted price
    pred_price = predict_price(lat, lon, bedrooms, bathrooms, property_type)
    
    # Filtered df
    filtered_df = df[(df['property_type'] == property_type)]
    
    # Scatter plot
    scatter_fig = px.scatter(
        filtered_df, x='longitude', y='latitude', size='price', color='price',
        hover_data=['price','bedrooms','bathrooms','sqft','property_type'],
        title="Property Locations"
    )
    scatter_fig.add_scatter(
        x=[lon], y=[lat],
        mode='markers', marker=dict(color='red', size=15),
        name='Selected Property'
    )
    
    # Histogram
    hist_fig = px.histogram(filtered_df, x='price', nbins=10, title="Price Distribution")
    hist_fig.add_vline(x=pred_price, line_dash='dash', line_color='red', annotation_text='Predicted', annotation_position="top")
    
    # Stats cards
    avg_price = filtered_df['price'].mean()
    percentile = np.sum(filtered_df['price'] <= pred_price)/len(filtered_df)*100
    
    pred_card = f"Predicted Price: ${pred_price:,.0f}"
    avg_card = f"Neighborhood Avg: ${avg_price:,.0f}"
    perc_card = f"Percentile Rank: {percentile:.1f}%"
    
    return scatter_fig, hist_fig, pred_card, avg_card, perc_card

# ------------------------------
# Download callback
# ------------------------------
@app.callback(
    Output("download-charts", "data"),
    Input("download-btn", "n_clicks"),
    State("scatter-plot", "figure"),
    State("price-histogram", "figure"),
    prevent_initial_call=True
)
def download_charts(n_clicks, scatter_fig, hist_fig):
    combined_html = f"""
    <html>
    <head><title>Dashboard Snapshot</title></head>
    <body>
    <h2>Scatter Plot</h2>
    {pio.to_html(scatter_fig, full_html=False, include_plotlyjs='cdn')}
    <h2>Price Distribution Histogram</h2>
    {pio.to_html(hist_fig, full_html=False, include_plotlyjs=False)}
    </body>
    </html>
    """
    return dcc.send_string(combined_html, filename="dashboard_snapshot.html")

# ------------------------------
# Run server (Render-ready)
# ------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))  # Render assigns the port
    app.run_server(host="0.0.0.0", port=port, debug=True)