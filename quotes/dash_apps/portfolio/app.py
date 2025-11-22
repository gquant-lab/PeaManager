"""
Portfolio Dashboard - Main Dash App

This module defines the main layout and registers the Portfolio dashboard.
Components and callbacks are defined in separate modules for better organization.
"""
from datetime import date, datetime, timedelta
from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from django_plotly_dash import DjangoDash

from quotes.dash_apps.portfolio.styles import CARD_STYLE, CARD_HEADER_STYLE, CARD_BODY_COMPACT_STYLE
from quotes.dash_apps.portfolio.callbacks import register_callbacks

# Initialize the Dash app
app = DjangoDash(
    'Portfolio', 
    add_bootstrap_links=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# Define the main layout
app.layout = html.Div(
    children=[
        html.Div(id='pk', title="na"),
        html.H1("Portfolio characteristics", style={"color": "white"}),
        html.Hr(className="my-2", style={"color": "white"}),
        html.P(
            "The following tabs provide various tools to dive in the portfolio details.",
            className="lead", 
            style={"color": "white"}
        ),
        html.Div(id='db-price-date', className="lead", style={"color": "white"}),
        
        # Summary cards row
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Current Portfolio Value", style=CARD_HEADER_STYLE), 
                    dbc.CardBody(id="card-ptf-value", style=CARD_BODY_COMPACT_STYLE)
                ], style=CARD_STYLE),
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("+/- Values", style=CARD_HEADER_STYLE),
                    dbc.CardBody(id="card-ptf-pnl", style=CARD_BODY_COMPACT_STYLE)
                ], style=CARD_STYLE),
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Last Updated", style=CARD_HEADER_STYLE),
                    dbc.CardBody(id="card-last-updated", style=CARD_BODY_COMPACT_STYLE)
                ], style=CARD_STYLE),
            ),
        ], id="row-card-override"),

        # Main content card with tabs
        dbc.Card([
            dbc.CardHeader(
                dbc.Tabs([
                    dbc.Tab(label="Overview", tab_id="overview"),
                    dbc.Tab(label="Order History", tab_id="orders"),
                    #dbc.Tab(label="Constituent Analysis", tab_id="constituent"),
                ], 
                id="tabs", 
                active_tab="overview"
                ),
                style=CARD_HEADER_STYLE
            ),
            dbc.CardBody(id="order_details")
        ], 
        id="card-tabs", 
        style=CARD_STYLE
        ),        
                
        # Constituent Performance card
        dbc.Card([
            dbc.CardHeader("Constituent Performance", style=CARD_HEADER_STYLE),
            dbc.CardBody(children=[
                # Date controls
                html.Div([
                    # Buttons for date ranges
                    html.Div([
                        dbc.Button(id='btn-horizon-1m', children="1m", color="secondary", size="sm"),
                        dbc.Button(id='btn-horizon-3m', children="3m", color="secondary", size="sm"),
                        dbc.Button(id='btn-horizon-6m', children="6m", color="secondary", size="sm"),
                        dbc.Button(id='btn-horizon-ytd', children="YTD", color="secondary", size="sm"),
                        dbc.Button(id='btn-horizon-1y', children="1Y", color="secondary", size="sm"),
                        dbc.Button(id='btn-horizon-3y', children="3Y", color="secondary", size="sm"),
                        dbc.Button(id='btn-horizon-max', children="Max", color="secondary", size="sm"),
                    ], style={"float": "left"}),

                    # DateRangePicker
                    html.Div([
                        dmc.DatePicker(
                            id="date-range-picker",
                            minDate=date(2020, 5, 8),
                            maxDate=datetime.now().date(),
                            value=[datetime.now().date() + timedelta(days=-5), datetime.now().date()],
                            style={"width": 300, "right": 0, "display": "inline-block"},
                            styles={"color": 'white'}
                        ),
                    ], style={"float": "right"}),
                ], 
                style={
                    "display": "flex",
                    "align-items": "flex-start",
                    "justify-content": "space-between"
                }),

                # Chart for Individual Returns
                dcc.Graph(id='contrib-graph', style={"height": "350px"}),
            ],
        )],
        style=CARD_STYLE
        ),

        # Dividends card
        dbc.Card(children=[
            dbc.CardHeader("Dividends", style=CARD_HEADER_STYLE),
            dbc.CardBody(
                dcc.Graph(id="dividends", style={"height": "350px"})
            ),
        ],
        style=CARD_STYLE
        ),

    ],
    className="bg-dark",
    style={
        "background": "#2d2d2d",
        "height": "100vh",
        "width": "100vw",
        "padding": "0",
        "margin": "0",
        "overflowX": "hidden",
        "display": "flex",
        "flexDirection": "column"
    }
)

# Register all callbacks
register_callbacks(app)
