import dash
from dash import dcc, html

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from django_plotly_dash import DjangoDash
from quotes.models import Portfolio, FinancialData

from datetime import date, datetime, timedelta
import pandas as pd

from quotes.dash_apps.home.components import get_performance_table
from pea_project.quotes.dash_apps.home.callbacks import register_callbacks


## import data (to be fixed with internal Django mechanics)
portfolios = Portfolio.objects.all()

for ptf in portfolios:
    if ptf.ts_ret is None:
        ptf.get_TS()



latest_date = FinancialData.get_price_most_recent_date()


# TO DO:
# 5. Fill table with performance
# 6. A few benchmarks should be available for charting: MSCI France, CAC40, DAX, SP500, Nasdaq100, MSCI World, MSCI China
# 7. Background color could change between chart and table (cf. https://github.com/alfonsrv/crypto-tracker)

app = DjangoDash('Dashboard', 
                 external_stylesheets=["static/assets/buttons.css"]
                 )   # replaces dash.Dash

app.layout = html.Div(children=[
    # DB 
    dbc.Container([
        
        html.H1("Portfolio performance comparison", style={"color": "white"}),
        html.Hr(),

        html.P(f"Most recent nav from Yahoo Finance is {latest_date.strftime('%d/%m/%Y')}", className="lead", style={"color": "white"}),

        html.Div([
            # Price / Return mode
            dbc.RadioItems(
                id="radio-chart-mode", 
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-secondary",
                labelCheckedClassName="active",
                options=[
                        {"label": "Prices", "value": "Prices"},
                        {"label": "Returns", "value": "Returns"},
                    ],
                value="Returns",
            )], className="radio-group"),

            # Dates button (left) + DateRangePicker (right)
            html.Div([
                # Buttons for dates
                html.Div([
                    dbc.Button(id='btn-horizon-1m', children="1m", color="secondary"),
                    dbc.Button(id='btn-horizon-3m', children="3m", color="secondary"),
                    dbc.Button(id='btn-horizon-6m', children="6m", color="secondary"),
                    dbc.Button(id='btn-horizon-ytd', children="YTD", color="secondary"),
                    dbc.Button(id='btn-horizon-1y', children="1Y", color="secondary"),
                    dbc.Button(id='btn-horizon-3y', children="3Y", color="secondary"),
                    dbc.Button(id='btn-horizon-max', children="Max", color="secondary"),
                ], style={"float": "left"}),

                # DateRangePicker
                html.Div([
                    dmc.DatePicker(
                        id="date-range-picker",
                        minDate=date(2020, 5, 8),
                        maxDate=datetime.now().date(),
                        value=[datetime.now().date()+ timedelta(days=-5), datetime.now().date()],
                        style={"width": 300, "right":0, "display": "inline-block"},
                        styles={"color": 'white'}
                    ),
                ], style={"float": "right"}),
                ], 
                style={
                    "display": "flex",
                    "align-items": "flex-start",
                    "justify-content": "space-between"
                }
            ),

        # The Time Series chart
        dcc.Graph(id='graph-ts', style={'height': '700px', 'width': '100%'}),
        get_performance_table()
    ], fluid=True)
    ], className="bg-dark")

# Register all callbacks
register_callbacks(app)


