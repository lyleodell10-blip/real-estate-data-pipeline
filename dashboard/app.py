# dashboard/app.py

import os
import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import numpy as np
import plotly.express as px
import io, base64

# ---------------------------
# Initialize app
# ---------------------------
app = dash.Dash(__name__)
server = app.server  # <-- Required for Render/Gunicorn

# ---------------------------
# Default sample data
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
# Theme styles
# ---------------------------
THEMES = {
    "light": {
        "background": "#f9f9f9",
        "card_bg": "#ffffff",
        "card_border": "#ccc",
        "text_color": "#000"
    },
    "dark": {
        "background": "#1e1e1e",
        "card_bg": "#2e2e2e",
        "card_border": "#555",
        "text_color": "#f9f9f9"
    }
}

# ---------------------------
# Helper: Parse uploaded CSVs
# ---------------------------
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.csv'):
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        else:
            return None
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None

# ---------------------------
# Layout
# ---------------------------
app.layout = html.Div([
    html.H1("AI Real Estate Valuation Dashboard", style={'textAlign': 'center'}),
    
    # Upload CSVs
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select CSV Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin-bottom': '20px'
        },
        multiple=True
    ),
    dcc.Store(id='uploaded-data', data=[]),

    html.Div([
        # Controls
        html.Div([
            # Theme toggle
            html.Div([
                html.Label("Theme:"),
                dcc.RadioItems(
                    id="theme-radio",
                    options=[
                        {"label": "Light", "value": "light"},
                        {"label": "Dark", "value": "dark"}
                    ],
                    value="light",
                    labelStyle={"display": "inline-block", "margin-right": "10px"}
                )
            ], style={"margin-bottom": "20px"}),

            html.Label("Select Location"),
            dcc.Dropdown(
                id='location-dropdown',
                options=[{"label": loc, "value": loc} for loc in sorted(df["Location"].unique())],
                value="A",
                clearable=False
            ),
            html.Label("Bedrooms"),
            dcc.Slider(id='bed-slider', min=1, max=4, step=1, value=2,
                       marks={i: str(i) for i in range(1,5)}),
            html.Label("Bathrooms"),
            dcc.Slider(id='bath-slider', min=1, max=3, step=1, value=1,
                       marks={i: str(i) for i in range(1,4)}),
            html.Label("Square Feet"),
            dcc.Slider(id='sqft-slider', min=600, max=3000, step=100, value=1500,
                       marks={i: str(i) for i in range(600,3001,500)}),
            html.Button("Download Snapshot", id="download-btn", style={'margin-top':'20px'}),
            dcc.Download(id="download-data")
        ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px', 
                  'borderRadius':'8px', 'boxShadow':'2px 2px 10px #ccc'}),

        # Charts and stats
        html.Div([
            html.Div([
                dcc.Graph(id='scatter-plot', style={'display':'inline-block', 'width':'49%'}),
                dcc.Graph(id='price-histogram', style={'display':'inline-block', 'width':'49%'})
            ], style={'display':'flex', 'flexWrap':'wrap'}),
            html.Div(id='stats-cards', style={'padding': '10px', 'display':'flex', 'flexWrap':'wrap'})
        ], style={'width': '70%', 'display': 'inline-block', 'padding': '20px'})
    ])
], id='main-div')

# ---------------------------
# Callbacks
# ---------------------------
@app.callback(
    Output('uploaded-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('uploaded-data', 'data'),
    prevent_initial_call=True
)
def update_uploaded_data(contents_list, filenames, existing_data):
    if contents_list is None:
        return existing_data
    for contents, filename in zip(contents_list, filenames):
        df_uploaded = parse_contents(contents, filename)
        if df_uploaded is not None:
            existing_data.append(df_uploaded.to_dict('records'))
    return existing_data

@app.callback(
    Output('scatter-plot', 'figure'),
    Output('price-histogram', 'figure'),
    Output('stats-cards', 'children'),
    Output('main-div', 'style'),
    Input('location-dropdown', 'value'),
    Input('bed-slider', 'value'),
    Input('bath-slider', 'value'),
    Input('sqft-slider', 'value'),
    Input('uploaded-data', 'data'),
    Input('theme-radio', 'value')
)
def update_dashboard(location, beds, baths, sqft, uploaded_data, theme):
    # Merge default df with uploaded data
    combined_df = df.copy()
    if uploaded_data:
        for data in uploaded_data:
            combined_df = pd.concat([combined_df, pd.DataFrame(data)], ignore_index=True)

    # Filter
    filtered = combined_df[
        (combined_df["Location"] == location) &
        (combined_df["Bedrooms"] == beds) &
        (combined_df["Bathrooms"] == baths)
    ]

    # Mock predicted price
    predicted_price = int(200_000 + beds*50_000 + baths*30_000 + sqft*100)

    # Scatter plot
    scatter_fig = px.scatter(
        filtered, x="SquareFeet", y="Price",
        color="Bedrooms", size="Bathrooms",
        title=f"Scatter Plot for {location}"
    )
    scatter_fig.add_hline(y=predicted_price, line_dash="dash", line_color="red",
                          annotation_text="Predicted Price", annotation_position="top left")
    scatter_fig.update_layout(plot_bgcolor=THEMES[theme]['background'], paper_bgcolor=THEMES[theme]['background'],
                              font_color=THEMES[theme]['text_color'])

    # Histogram
    hist_fig = px.histogram(filtered, x="Price", nbins=20, title="Price Distribution")
    hist_fig.add_vline(x=predicted_price, line_dash="dash", line_color="red",
                       annotation_text="Predicted Price", annotation_position="top left")
    hist_fig.update_layout(plot_bgcolor=THEMES[theme]['background'], paper_bgcolor=THEMES[theme]['background'],
                           font_color=THEMES[theme]['text_color'])

    # Stats cards
    avg_price = filtered["Price"].mean() if not filtered.empty else 0
    max_price = filtered["Price"].max() if not filtered.empty else 0
    min_price = filtered["Price"].min() if not filtered.empty else 0

    style = THEMES[theme]
    cards = html.Div([
        html.Div(f"Predicted Price: ${predicted_price:,}", 
                 style={'padding':'15px','border':'1px solid '+style['card_border'],
                        'margin':'5px','borderRadius':'8px','backgroundColor':style['card_bg'],
                        'color': style['text_color'],'transition':'0.3s', 'cursor':'pointer'}),
        html.Div(f"Avg Price: ${avg_price:,.0f}", 
                 style={'padding':'15px','border':'1px solid '+style['card_border'],
                        'margin':'5px','borderRadius':'8px','backgroundColor':style['card_bg'],
                        'color': style['text_color'],'transition':'0.3s', 'cursor':'pointer'}),
        html.Div(f"Max Price: ${max_price:,}", 
                 style={'padding':'15px','border':'1px solid '+style['card_border'],
                        'margin':'5px','borderRadius':'8px','backgroundColor':style['card_bg'],
                        'color': style['text_color'],'transition':'0.3s', 'cursor':'pointer'}),
        html.Div(f"Min Price: ${min_price:,}", 
                 style={'padding':'15px','border':'1px solid '+style['card_border'],
                        'margin':'5px','borderRadius':'8px','backgroundColor':style['card_bg'],
                        'color': style['text_color'],'transition':'0.3s', 'cursor':'pointer'}),
    ], style={'display':'flex','flexWrap':'wrap'})

    # Apply background color to main div
    main_style = {'backgroundColor': style['background'], 'minHeight': '100vh', 'padding':'10px'}

    return scatter_fig, hist_fig, cards, main_style

# ---------------------------
# Download CSV callback
# ---------------------------
@app.callback(
    Output("download-data", "data"),
    Input("download-btn", "n_clicks"),
    State('location-dropdown', 'value'),
    State('bed-slider', 'value'),
    State('bath-slider', 'value'),
    State('sqft-slider', 'value'),
    State('uploaded-data', 'data'),
    prevent_initial_call=True
)
def download_snapshot(n_clicks, location, beds, baths, sqft, uploaded_data):
    combined_df = df.copy()
    if uploaded_data:
        for data in uploaded_data:
            combined_df = pd.concat([combined_df, pd.DataFrame(data)], ignore_index=True)
    filtered = combined_df[
        (combined_df["Location"] == location) &
        (combined_df["Bedrooms"] == beds) &
        (combined_df["Bathrooms"] == baths)
    ]
    return dcc.send_data_frame(filtered.to_csv, f"{location}_snapshot.csv")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=True)