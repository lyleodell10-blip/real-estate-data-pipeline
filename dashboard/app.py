# dashboard/app.py

import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np

# ---------------------------
# Initialize app
# ---------------------------
app = dash.Dash(__name__)
server = app.server  # <<--- Required for Render/Gunicorn

# ---------------------------
# Sample data (replace with your real dataset)
# ---------------------------
np.random.seed(42)
df = pd.DataFrame({
    "Location": np.random.choice(["A", "B", "C", "D"], size=200),
    "Price": np.random.normal(300_000, 50_000, size=200).astype(int),
    "Bedrooms": np.random.randint(1, 5, size=200),
    "Bathrooms": np.random.randint(1, 4, size=200),
    "SquareFeet": np.random.randint(600, 3000, size=200)
})

# ---------------------------
# Layout
# ---------------------------
app.layout = html.Div([
    html.H1("AI Real Estate Valuation Dashboard"),

    html.Div([
        html.Label("Select Location"),
        dcc.Dropdown(
            id='location-dropdown',
            options=[{"label": loc, "value": loc} for loc in sorted(df["Location"].unique())],
            value="A"
        ),
        html.Label("Bedrooms"),
        dcc.Slider(id='bed-slider', min=1, max=4, step=1, value=2,
                   marks={i: str(i) for i in range(1,5)}),
        html.Label("Bathrooms"),
        dcc.Slider(id='bath-slider', min=1, max=3, step=1, value=1,
                   marks={i: str(i) for i in range(1,4)}),
        html.Label("Square Feet"),
        dcc.Slider(id='sqft-slider', min=600, max=3000, step=100, value=1500,
                   marks={i: str(i) for i in range(600,3001,500)})
    ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'}),

    html.Div([
        dcc.Graph(id='scatter-plot'),
        dcc.Graph(id='price-histogram')
    ], style={'width': '70%', 'display': 'inline-block', 'padding': '20px'}),

    html.Div(id='stats-cards', style={'padding': '20px'}),

    html.Button("Download Snapshot", id="download-btn"),
    dcc.Download(id="download-data")
])

# ---------------------------
# Callbacks
# ---------------------------
@app.callback(
    Output('scatter-plot', 'figure'),
    Output('price-histogram', 'figure'),
    Output('stats-cards', 'children'),
    Input('location-dropdown', 'value'),
    Input('bed-slider', 'value'),
    Input('bath-slider', 'value'),
    Input('sqft-slider', 'value')
)
def update_charts(location, beds, baths, sqft):
    # Filter dataset
    filtered = df[
        (df["Location"] == location) &
        (df["Bedrooms"] == beds) &
        (df["Bathrooms"] == baths)
    ]

    # Mock AI price prediction
    predicted_price = int(200_000 + beds*50_000 + baths*30_000 + sqft*100)

    # Scatter plot
    scatter_fig = px.scatter(
        filtered, x="SquareFeet", y="Price",
        color="Bedrooms", size="Bathrooms",
        title=f"Scatter Plot for {location}"
    )
    scatter_fig.add_hline(y=predicted_price, line_dash="dash", line_color="red",
                          annotation_text="Predicted Price", annotation_position="top left")

    # Histogram
    hist_fig = px.histogram(filtered, x="Price", nbins=20, title="Price Distribution")
    hist_fig.add_vline(x=predicted_price, line_dash="dash", line_color="red",
                       annotation_text="Predicted Price", annotation_position="top left")

    # Stats cards
    avg_price = filtered["Price"].mean() if not filtered.empty else 0
    max_price = filtered["Price"].max() if not filtered.empty else 0
    min_price = filtered["Price"].min() if not filtered.empty else 0

    cards = html.Div([
        html.Div(f"Predicted Price: ${predicted_price:,}", style={'padding': '10px', 'border': '1px solid black', 'margin': '5px'}),
        html.Div(f"Avg Price: ${avg_price:,.0f}", style={'padding': '10px', 'border': '1px solid black', 'margin': '5px'}),
        html.Div(f"Max Price: ${max_price:,}", style={'padding': '10px', 'border': '1px solid black', 'margin': '5px'}),
        html.Div(f"Min Price: ${min_price:,}", style={'padding': '10px', 'border': '1px solid black', 'margin': '5px'}),
    ], style={'display': 'flex', 'flexWrap': 'wrap'})

    return scatter_fig, hist_fig, cards

# ---------------------------
# Download snapshot callback
# ---------------------------
@app.callback(
    Output("download-data", "data"),
    Input("download-btn", "n_clicks"),
    State('location-dropdown', 'value'),
    State('bed-slider', 'value'),
    State('bath-slider', 'value'),
    State('sqft-slider', 'value'),
    prevent_initial_call=True
)
def download_snapshot(n_clicks, location, beds, baths, sqft):
    filtered = df[
        (df["Location"] == location) &
        (df["Bedrooms"] == beds) &
        (df["Bathrooms"] == baths)
    ]
    return dcc.send_data_frame(filtered.to_csv, f"{location}_snapshot.csv")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=True)