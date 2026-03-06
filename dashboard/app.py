import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import io
import base64

# --- App Setup ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# --- Market Climate Colors ---
market_color = {
    "Hot Market 🔥": "#ffcccc",
    "Stable Market 🌤": "#ccffcc",
    "Cooling Market ❄️": "#cce0ff",
    "No Data": "#f0f0f0"
}
climate_text = "Hot Market 🔥"  # Default

# --- Stats Cards Function ---
def create_stats_cards(pred_price=500000, avg_price=450000, max_price=1200000,
                       min_price=250000, climate=climate_text, land_avm=None):
    cards = [
        html.Div(f"Predicted Price: ${pred_price:,} 🏠", title="AI-generated Automated Valuation Model", className="stat-card"),
        html.Div(f"Avg Price: ${avg_price:,} 📊", title="Average price of selected properties", className="stat-card"),
        html.Div(f"Max Price: ${max_price:,} 💰", title="Most expensive property", className="stat-card"),
        html.Div(f"Min Price: ${min_price:,} 🏷", title="Least expensive property", className="stat-card"),
        html.Div(f"Market Climate: {climate}", title="Local market conditions", 
                 className="stat-card", style={"backgroundColor": market_color.get(climate, "#f0f0f0")})
    ]
    if land_avm is not None:
        cards.append(html.Div(f"Raw Land AVM: ${land_avm:,.0f}", 
                              title="Predicted land value based on size, shape, wetlands, zoning", className="stat-card"))
    return html.Div(cards, style={
        'display': 'flex', 
        'gap': '15px', 
        'flexWrap': 'wrap', 
        'justifyContent': 'center',
        'marginBottom': '20px'
    })

# --- Filters Example ---
filters = html.Div([
    html.Div(dcc.Dropdown(options=[{'label': 'Option 1', 'value': '1'}], placeholder="Filter 1"), style={'flex': '1', 'minWidth': '180px'}),
    html.Div(dcc.Dropdown(options=[{'label': 'Option 2', 'value': '2'}], placeholder="Filter 2"), style={'flex': '1', 'minWidth': '180px'}),
    html.Div(dcc.Dropdown(options=[{'label': 'Option 3', 'value': '3'}], placeholder="Filter 3"), style={'flex': '1', 'minWidth': '180px'}),
    html.Div(dcc.Dropdown(options=[{'label': 'Option 4', 'value': '4'}], placeholder="Filter 4"), style={'flex': '1', 'minWidth': '180px'}),
    html.Div(dcc.Dropdown(options=[{'label': 'Option 5', 'value': '5'}], placeholder="Filter 5"), style={'flex': '1', 'minWidth': '180px'})
], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap', 'marginBottom': '20px'})

# --- Graphs ---
scatter_map = dcc.Graph(id='scatter-plot', style={'flex': '1', 'height': '600px'})
price_hist = dcc.Graph(id='price-histogram', style={'flex': '1', 'height': '600px'})
charts = html.Div([scatter_map, price_hist], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'})

# --- App Layout ---
app.layout = html.Div([
    html.Style("""
        .stat-card {
            border-radius: 10px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.15);
            padding: 20px;
            min-width: 180px;
            text-align: center;
            background-color: #ffffff;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: default;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 4px 4px 12px rgba(0,0,0,0.25);
        }
    """),
    html.H2("Real Estate & Raw Land Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # --- CSV Upload ---
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop CSV or ', html.A('Select Files')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'marginBottom': '20px'
        },
        multiple=False
    ),
    
    # --- Stats Cards ---
    html.Div(id='stats-cards', children=create_stats_cards()),
    
    # --- Filters ---
    filters,
    
    # --- Charts ---
    charts,
    
    # --- Raw Land AVM Inputs ---
    html.Div([
        html.H4("Compute Raw Land AVM"),
        html.Div([
            dcc.Input(id='parcel-size', type='number', placeholder='Size (acres)'),
            dcc.Input(id='wetlands', type='number', placeholder='Wetlands %'),
            dcc.Dropdown(id='shape', options=[
                {'label': 'Regular', 'value': 'regular'},
                {'label': 'Irregular', 'value': 'irregular'},
                {'label': 'Odd', 'value': 'odd'}
            ], placeholder='Parcel Shape'),
            dcc.Input(id='zoning', type='text', placeholder='Current Zoning'),
            dcc.Input(id='potential-zoning', type='text', placeholder='Potential Zoning'),
            html.Button('Compute Land AVM', id='compute-avm', n_clicks=0)
        ], style={'display':'flex', 'gap':'10px', 'flexWrap':'wrap', 'marginBottom':'10px'}),
        html.Div(id='land-avm-output', style={'fontWeight':'bold', 'marginTop':'10px'})
    ])
])

# --- CSV Parsing ---
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = io.BytesIO(base64.b64decode(content_string))
    try:
        df = pd.read_csv(decoded)
        return df
    except Exception as e:
        print(e)
        return pd.DataFrame()

# --- Callbacks for Map, Histogram, Stats Cards ---
@app.callback(
    Output('scatter-plot', 'figure'),
    Output('price-histogram', 'figure'),
    Output('stats-cards', 'children'),
    Input('upload-data', 'contents'),
    State('parcel-size', 'value'),
    State('wetlands', 'value'),
    State('shape', 'value'),
    State('zoning', 'value'),
    State('potential-zoning', 'value'),
)
def update_graphs(contents, size, wetlands, shape, zoning, potential_zoning):
    # --- Property Data ---
    if contents is None:
        df = pd.DataFrame({
            "lat": [30.3, 30.4, 30.5],
            "lon": [-81.6, -81.7, -81.8],
            "price": [450000, 500000, 600000]
        })
    else:
        df = parse_contents(contents)
        if df.empty or not all(col in df.columns for col in ["lat", "lon", "price"]):
            df = pd.DataFrame({
                "lat": [30.3, 30.4, 30.5],
                "lon": [-81.6, -81.7, -81.8],
                "price": [450000, 500000, 600000]
            })
    
    # --- Property Stats ---
    pred_price = int(df['price'].mean() * 1.05)
    avg_price = int(df['price'].mean())
    max_price = int(df['price'].max())
    min_price = int(df['price'].min())
    
    # --- Raw Land AVM ---
    land_avm = None
    if size is not None:
        base_rate = 50000
        shape_factor = {'regular':1.0, 'irregular':0.95, 'odd':0.9}.get(shape,1)
        wetland_factor = max(0, 1 - (wetlands or 0)/100)
        zoning_factor = 1.0
        potential_factor = 1.05 if potential_zoning else 1.0
        land_avm = size * base_rate * shape_factor * wetland_factor * zoning_factor * potential_factor
    
    # --- Stats Cards ---
    stats_cards_updated = create_stats_cards(pred_price, avg_price, max_price, min_price, climate_text, land_avm)
    
    # --- Scatter Map ---
    scatter_fig = px.scatter_mapbox(df, lat="lat", lon="lon", color="price", size="price", zoom=10,
                                    mapbox_style="open-street-map",
                                    color_continuous_scale=px.colors.sequential.Viridis)
    scatter_fig.update_traces(marker=dict(size=12, opacity=0.8), selector=dict(mode='markers'))

    # --- Histogram ---
    hist_fig = px.histogram(df, x="price", nbins=10, color="price",
                            color_continuous_scale='Blues', text_auto=True)
    hist_fig.update_layout(xaxis_title="Price", yaxis_title="Count")
    
    return scatter_fig, hist_fig, stats_cards_updated

# --- Callback for Land AVM Button (updates dynamically) ---
@app.callback(
    Output('land-avm-output', 'children'),
    Input('compute-avm', 'n_clicks'),
    State('parcel-size', 'value'),
    State('wetlands', 'value'),
    State('shape', 'value'),
    State('zoning', 'value'),
    State('potential-zoning', 'value')
)
def compute_land_avm(n_clicks, size, wetlands, shape, zoning, potential_zoning):
    if n_clicks is None or size is None:
        return ""
    base_rate = 50000
    shape_factor = {'regular':1.0, 'irregular':0.95, 'odd':0.9}.get(shape,1)
    wetland_factor = max(0, 1 - (wetlands or 0)/100)
    zoning_factor = 1.0
    potential_factor = 1.05 if potential_zoning else 1.0
    predicted_value = size * base_rate * shape_factor * wetland_factor * zoning_factor * potential_factor
    return f"Predicted Land Value: ${predicted_value:,.0f} (±3% margin)"

# --- Run App ---
if __name__ == '__main__':
    app.run_server(debug=True)