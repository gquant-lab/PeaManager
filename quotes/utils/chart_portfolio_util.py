import numpy as np
import plotly.graph_objects as go

from quotes.models import Portfolio, FinancialData, Order

def performance_overview(id_portfolio):
    """
    Create the performance overview table showing portfolio positions.
    """
    ptf = Portfolio.objects.get(id=id_portfolio)
    latest_date = FinancialData.get_price_most_recent_date()

    df = ptf.inventory_df()
    df["Amount_Paid"] = df["PRU"] * df["Number"]

    prices = [
        FinancialData.objects
        .filter(id_object=id, field="NAV", origin="Yahoo Finance", date=latest_date)
        .values_list("value", flat=True).first() 
        for id in df["Id"].tolist()
    ]
    
    df["Current_Value"] = np.multiply(df["Number"], np.array(prices))
    df.sort_values(by="Current_Value", ascending=False, inplace=True)

    df["Pnl"] = df["Current_Value"] - df["Amount_Paid"]
    df["Weight"] = df["Current_Value"] / df["Current_Value"].sum()
    df["Weight"] = df["Weight"].map('{:,.1%}'.format)
    
    del df["Id"]

    numeric_cols = ["PRU", "Amount_Paid", "Current_Value", "Pnl"]
    df[numeric_cols] = df[numeric_cols].map('{:,.2f}'.format)

    return df.to_dict(orient="records")


def get_order_history(portfolio_id):
    """
    Get all orders for a portfolio.
    Returns a list of dicts with order details.
    """
    portfolio = Portfolio.objects.get(id=portfolio_id)
    orders = Order.objects.filter(portfolio=portfolio).order_by('-date')

    l_dicts = []
    for order in orders:
        d = {
            'id': order.id,
            'date': order.date,
            'id_object': order.id_object.name,
            'direction': order.direction,
            'nb_items': order.nb_items,
            'price': order.price,
            'total_fee': order.total_fee,
        }
        l_dicts.append(d)
    return l_dicts

def create_allocation_chart(portfolio_id):
    """
    Create a pie chart showing the allocation of the portfolio.
    """
    ptf = Portfolio.objects.get(id=portfolio_id)
    weights = ptf.get_weights()

    # weights is already {name: percentage}
    labels = list(weights.keys())
    values = list(weights.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='label',
        textposition='inside',
        insidetextorientation='radial',
        hovertemplate='<b>%{label}</b><br>Weight: %{percent}<extra></extra>',
        hole=0.3,
        sort=True,  # Already sorted
        direction='clockwise',
    )])

    fig.update_layout(
        title=None, #card header has it
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0)
    )
    
    return fig