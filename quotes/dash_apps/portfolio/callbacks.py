"""
Callbacks for the Portfolio Dash app.
"""
import numpy as np
import dash
import plotly.graph_objects as go
from django.core.exceptions import ObjectDoesNotExist

from quotes.models import Portfolio, FinancialData, FinancialObject, Order
from quotes.forms import OrderForm
from quotes.dash_apps.portfolio.components import performance_overview, get_order_card_body, get_individual_returns


def register_callbacks(app):
    """
    Register all callbacks for the Portfolio app.
    """
    
    @app.callback(
        dash.dependencies.Output('order_details', 'children'),
        dash.dependencies.Input('tabs', 'active_tab'),
        dash.dependencies.State('pk', 'title')
    )
    def display_tab_in_cardbody(active_tab, pk):
        """
        Display the content of the active tab in the card body.
        """
        if active_tab == "overview":
            return performance_overview(pk)
        elif active_tab == "orders":
            return get_order_card_body(pk)
        elif active_tab == "constituent":
            return get_individual_returns(pk)

    @app.callback(
        dash.dependencies.Output("modal", "is_open"),
        [dash.dependencies.Input("btn-add-order", "n_clicks"),
         dash.dependencies.Input("btn-close-modal", "n_clicks")],
        [dash.dependencies.State("modal", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        """
        Toggle modal with the button to add a new order.
        """
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        dash.dependencies.Output('submit-btn', 'n_clicks'),
        [dash.dependencies.Input('portfolio', 'value'),
         dash.dependencies.Input('id_object', 'value'),
         dash.dependencies.Input('date', 'value'),
         dash.dependencies.Input('direction', 'value'),
         dash.dependencies.Input('nb_items', 'value'),
         dash.dependencies.Input('price', 'value'),
         dash.dependencies.Input('total_fee', 'value'),
         dash.dependencies.Input('submit-btn', 'n_clicks')]
    )
    def submit_form(portfolio_id, id_object_id, date, direction, nb_items, price, total_fee, n_clicks):
        """
        Callback to submit a new order in the Orders tab.
        """
        if n_clicks and n_clicks > 0:
            try:
                portfolio = Portfolio.objects.get(id=portfolio_id)
                id_object = FinancialObject.objects.get(id=id_object_id)
            except ObjectDoesNotExist:
                return 'Invalid portfolio or financial object ID'

            form = OrderForm({
                'portfolio': portfolio,
                'id_object': id_object,
                'date': date,
                'direction': direction,
                'nb_items': nb_items,
                'price': price,
                'total_fee': total_fee,
            })
            if form.is_valid():
                form.save()

    @app.callback(
        dash.dependencies.Output('contrib-graph', 'figure'),
        dash.dependencies.Output('contrib-graph', 'style'),
        dash.dependencies.Input('indiv-ret-start-date', 'value'),
        dash.dependencies.Input('indiv-ret-end-date', 'value'),
        dash.dependencies.State('ptf', 'title')
    )
    def update_graph(start_date, end_date, id_portfolio):
        """
        Update the contribution graph based on selected date range.
        """
        if start_date and end_date:
            ptf = Portfolio.objects.get(id=id_portfolio)
            contributions = ptf.get_individual_returns(start_date, end_date)

            # Create a figure from the contributions
            figure = go.Figure(
                data=[go.Bar(x=contributions["Total"], y=contributions.index, orientation="h")]
            )

            figure.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font={"color": "white", "size": 14},
                xaxis={
                    "title": "weights",
                    "categoryorder": "category ascending",
                    "tickformat": ".0%", 
                    "hoverformat": ".1%",
                },
                yaxis={
                    "title": "Instrument",
                },
                showlegend=False
            )
            
            return figure, {"display": "block"}
        return go.Figure(data=[]), {"display": "none"}

    @app.callback(
        dash.dependencies.Output('card-ptf-value', 'children'),
        dash.dependencies.Output('card-ptf-pnl', 'children'),
        dash.dependencies.Output('card-last-updated', 'children'),
        dash.dependencies.Input('pk', 'title'),
    )
    def update_cards(id_portfolio: int):
        """
        Callback to update the 3 cards with the portfolio value, pnl and last updated date at the
        top of the page.
        """
        ptf = Portfolio.objects.get(id=id_portfolio)
        latest_date = FinancialData.get_price_most_recent_date()
        inventory = ptf.get_inventory(latest_date)

        if ptf.ts_val is None:
            ptf.get_TS()

        # Portfolio Value
        ptf_value = ptf.ts_val[latest_date]
        
        # Portfolio PnL
        pnl = ptf_value - np.dot(inventory.nbs, inventory.prus) 

        return f"{ptf_value:,.2f}€", f"{pnl:,.2f}€", latest_date

    @app.callback(
        dash.dependencies.Output('db-price-date', 'children'),
        dash.dependencies.Input('order-table', 'data_previous'),
        dash.dependencies.State('order-table', 'data')
    )
    def remove_table_row_and_corresponding_object(data_previous, data):
        """
        Handle row deletion from order table.
        """
        pass
