"""
Layout components for the Portfolio Dash app.
"""
from datetime import date, datetime
import numpy as np
import pandas as pd
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from quotes.models import Portfolio, FinancialData, FinancialObject, Order
from quotes.dash_apps.portfolio.styles import Colors, CARD_HEADER_STYLE


def order_tab_layout():
    """
    This function returns the layout of the order form when adding a new order. 
    """
    portfolios = Portfolio.objects.all()
    financial_objects = FinancialObject.objects.all()

    # Create options for the select boxes
    portfolio_options = [{'label': str(p), 'value': p.id} for p in portfolios]
    financial_object_options = [{'label': str(o), 'value': o.id} for o in financial_objects]
    direction_options = [
        {'label': 'Buy', 'value': Order.OrderDirection.BUY}, 
        {'label': 'Sell', 'value': Order.OrderDirection.SELL}
    ]

    dropdown_style = {"background-color": Colors.card_dark, "color": "black"}
    input_style = {"background-color": Colors.card_dark, "color": "white"}

    return html.Div(children=[
        dbc.Row([
            dbc.Col(dbc.Label('Portfolio'), width=2),
            dbc.Col(dcc.Dropdown(id='portfolio', options=portfolio_options, style=dropdown_style), width=10)
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Financial Object'), width=2),
            dbc.Col(dcc.Dropdown(id='id_object', options=financial_object_options, style=dropdown_style), width=10)
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Date'), width=2),
            dbc.Col(dcc.Input(id='date', type='date', style=input_style), width=10)
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Direction'), width=2),
            dbc.Col(dcc.Dropdown(id='direction', options=direction_options, style=dropdown_style), width=10)
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Number of Items'), width=2),
            dbc.Col(dcc.Input(id='nb_items', type='number', style=input_style), width=10)
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Price'), width=2),
            dbc.Col(dcc.Input(id='price', type='number', style=input_style), width=10)
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Total Fee'), width=2),
            dbc.Col(dcc.Input(id='total_fee', type='number', style=input_style), width=10)
        ]),
        dbc.Row([
            dbc.Col(dbc.Button('Submit', id='submit-btn', color='primary', n_clicks=0))
        ]),
    ], style={'color': 'white'})


def get_order_history(id_portfolio):
    """
    This function returns a dash table with the order history of the portfolio 
    """
    portfolio = Portfolio.objects.get(id=id_portfolio)
    orders = Order.objects.filter(portfolio=portfolio).order_by('-date')

    dt_columns = [
        {'name': 'Date', 'id': 'date'},
        {'name': 'Instrument Name', 'id': 'id_object'},
        {'name': 'Direction', 'id': 'direction'},
        {'name': 'Number of Items', 'id': 'nb_items'},
        {'name': 'Price', 'id': 'price'},
        {'name': 'Total Fee', 'id': 'total_fee'},
        {'name': '', 'id': 'delete', 'presentation': 'markdown'}
    ] 

    # Display in a dash_table all orders in database associated with portfolio
    return dash_table.DataTable(
        id='order-table',
        columns=dt_columns,
        data=[
            {
                'date': o.date, 
                'id_object': o.id_object.name, 
                'direction': o.direction, 
                'nb_items': o.nb_items, 
                'price': o.price, 
                'total_fee': o.total_fee,
                'delete': f'[🗑️](#)'
            }
            for o in orders
        ],
        style_as_list_view=True,
        style_cell={
            'backgroundColor': '#2d2d2d', 
            'color': 'white', 
            "textAlign": "center", 
            'font-family': 'sans-serif', 
            "lineHeight": "24px"
        },
        style_header={'fontWeight': 'bold', 'border': 'none'},
        filter_action='native',
        sort_action='native',
        page_size=10,
        row_deletable=True,
    )


def get_order_card_body(id_portfolio):
    """
    This function returns the table of previous orders, and a button to add a new one.
    """
    table = get_order_history(id_portfolio)
    button = dbc.Button("Add a new order", id="btn-add-order", color="primary")
    modal = dbc.Modal(
        [
            dbc.ModalHeader("Add a new order", style={"background-color": "#343a40", "color": "white"}),
            dbc.ModalBody(order_tab_layout(), style={"background-color": "#343a40", "color": "white"}),
            dbc.ModalFooter(
                dbc.Button("Close", id="btn-close-modal", className="ml-auto", n_clicks=0),
                style={"background-color": "#343a40", "color": "white"}
            ),
        ],
        id="modal",
        size="lg",
        is_open=False
    )
    return [table, button, modal]


def get_individual_returns(id_portfolio):
    """
    Layout for individual returns analysis tab.
    """
    date_range = dmc.Group(
        spacing="xl",
        children=[
            dmc.DatePicker(
                id="indiv-ret-start-date",
                label="Start Date",
                className="label-class text-white",
            ),
            dmc.DatePicker(
                id="indiv-ret-end-date",
                label="End Date",
                maxDate=date.today()
            ),
        ], 
    )
    
    div_id = html.Div(title=f"{id_portfolio}", id="ptf", hidden=True)
    contrib_graph = dcc.Graph(id='contrib-graph', style={"display": "none"})

    return html.Div(children=[date_range, contrib_graph, div_id])


def performance_overview(id_portfolio):
    """
    Create the performance overview table showing portfolio positions.
    """
    ptf = Portfolio.objects.get(id=id_portfolio)
    latest_date = FinancialData.get_price_most_recent_date()

    df = ptf.inventory_df()
    df["Amount Paid"] = df["PRU"] * df["Number"]

    prices = [
        FinancialData.objects
        .filter(id_object=id, field="NAV", origin="Yahoo Finance", date=latest_date)
        .values_list("value", flat=True).first() 
        for id in df["Id"].tolist()
    ]
    
    df["Current Value"] = np.multiply(df["Number"], np.array(prices))
    df.sort_values(by="Current Value", ascending=False, inplace=True)

    df["+/- Value"] = df["Current Value"] - df["Amount Paid"]
    df["Weight"] = df["Current Value"] / df["Current Value"].sum()
    df["Weight"] = df["Weight"].map('{:,.1%}'.format)
    
    # Formatting
    numeric_cols = ["PRU", "Amount Paid", "Current Value", "+/- Value"]
    df[numeric_cols] = df[numeric_cols].map('{:,.2f}'.format)
    del df["Id"]

    header_style = {"background-color": "#2d2d2d", "color": "white"}
    row_style = {"color": "white", "background-color": "#2d2d2d"}
    
    table_header = [
        html.Thead(html.Tr([html.Th(col, style=header_style) for col in df.columns]))
    ]
    
    rows = []
    for item in df.to_dict(orient="records"):
        rows.append(
            html.Tr([html.Td(item[col], style=row_style) for col in df.columns])
        )
    
    table_body = [html.Tbody(rows)]
    table = dbc.Table(
        table_header + table_body, 
        hover=True, 
        color="dark",
        style={"text-align": "center", "border": "none"},
        id="tb",
        className="custom-table"
    )
    
    return table
