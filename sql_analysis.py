# real_estate_dashboard.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load your dataset
df = pd.read_csv('real_estate_data.csv')  # Replace with your CSV path

# Precompute some custom metrics
df['Price_per_Sqft'] = df['SalePrice'] / df['GrLivArea']
avg_price_per_neighborhood = df.groupby('Neighborhood')['Price_per_Sqft'].mean().reset_index()
avg_price_per_zoning = df.groupby('MSZoning')['Price_per_Sqft'].mean().reset_index()

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Real Estate Dashboard"

# Layout
app.layout = html.Div([
    html.H1("Real Estate Data Dashboard", style={'textAlign': 'center'}),
    
    # Histogram of Sale Prices
    html.Div([
        html.H2("Distribution of Sale Prices"),
        dcc.Graph(
            id='saleprice_histogram',
            figure=px.histogram(df, x='SalePrice', nbins=50, title="Sale Price Distribution")
        )
    ], style={'padding': '20px'}),
    
    # Histogram / Density Plot of LotArea
    html.Div([
        html.H2("Lot Area Distribution"),
        dcc.Graph(
            id='lotarea_histogram',
            figure=px.histogram(df, x='LotArea', nbins=50, title="Lot Area Distribution", marginal="box")
        )
    ], style={'padding': '20px'}),
    
    # Map of properties (if Latitude and Longitude exist)
    html.Div([
        html.H2("Property Locations"),
        dcc.Graph(
            id='property_map',
            figure=px.scatter_mapbox(
                df, lat='Latitude', lon='Longitude',
                hover_name='Neighborhood',
                hover_data={'SalePrice': True, 'GrLivArea': True},
                color='SalePrice',
                size='GrLivArea',
                zoom=10,
                mapbox_style="open-street-map",
                title="Properties Map"
            )
        )
    ], style={'padding': '20px'}),
    
    # Correlation Heatmap
    html.Div([
        html.H2("Correlation Heatmap"),
        dcc.Graph(
            id='correlation_heatmap',
            figure=px.imshow(
                df[['SalePrice', 'LotArea', 'GrLivArea', 'BedroomAbvGr', 'FullBath', 'HalfBath']].corr(),
                text_auto=True,
                color_continuous_scale='RdBu_r',
                title="Feature Correlations"
            )
        )
    ], style={'padding': '20px'}),
    
    # Time Trends: Sales by Year and Month
    html.Div([
        html.H2("Sales Over Time"),
        dcc.Graph(
            id='sales_trend',
            figure=px.line(
                df.groupby('YrSold')['SalePrice'].mean().reset_index(),
                x='YrSold', y='SalePrice', title='Average Sale Price by Year'
            )
        ),
        dcc.Graph(
            id='monthly_sales_trend',
            figure=px.line(
                df.groupby('MoSold')['SalePrice'].mean().reset_index(),
                x='MoSold', y='SalePrice', title='Average Sale Price by Month'
            )
        )
    ], style={'padding': '20px'}),
    
    # Custom Metrics: Price per Sqft by Neighborhood and Zoning
    html.Div([
        html.H2("Average Price per Sqft"),
        dcc.Graph(
            id='price_per_sqft_neighborhood',
            figure=px.bar(avg_price_per_neighborhood, x='Neighborhood', y='Price_per_Sqft', title="Price per Sqft by Neighborhood")
        ),
        dcc.Graph(
            id='price_per_sqft_zoning',
            figure=px.bar(avg_price_per_zoning, x='MSZoning', y='Price_per_Sqft', title="Price per Sqft by Zoning")
        )
    ], style={'padding': '20px'}),
])

# Run server
if __name__ == '__main__':
    app.run_server(debug=True)