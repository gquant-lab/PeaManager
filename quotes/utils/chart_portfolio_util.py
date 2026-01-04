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

def create_portfolio_performance_chart(portfolio_id, time_frame='max'):
    """
    Create a time series chart showing portfolio performance over time.
    Single portfolio version - no legend needed.
    
    Args:
        portfolio_id: Portfolio primary key
        time_frame: '1m', '3m', '6m', 'ytd', '1y', '3y', 'max'
    
    Returns:
        Plotly Figure
    """
    from quotes.utils.chart_creation import timeframe_to_limit_date
    
    ptf = Portfolio.objects.get(id=portfolio_id)
    
    # Ensure time series is loaded
    if ptf.ts_cumul_ret is None:
        ptf.get_TS()
    
    # Filter by timeframe
    limit_date = timeframe_to_limit_date(time_frame)
    ts = ptf.ts_cumul_ret[ptf.ts_cumul_ret.index >= limit_date]
    
    # Normalize to start at 0% for returns view
    ts_normalized = (ts / ts.iloc[0]) - 1
    
    # Create trace (single line, no need for legend)
    trace = go.Scatter(
        x=list(ts.index),
        y=list(ts_normalized.values),
        line={'color': 'darkorange', 'width': 3},
        hovertemplate='%{x|%d/%m/%Y}<br>Return: %{y:.2%}<extra></extra>'
    )
    
    fig = go.Figure(data=[trace])
    
    # Styling (dark theme, no legend)
    fig.update_layout(
        yaxis={
            'side': 'right',
            'tickformat': '.0%',
            'hoverformat': '.2%',
            'gridwidth': 1,
            'zerolinecolor': 'lightgray',
            'tickfont': {'color': 'white', 'size': 14}
        },
        xaxis={
            'dtick': 'M1',
            'tickformat': '%b\n%Y',
            'ticklabelmode': 'period',
            'showgrid': False,
            'tickfont': {'color': 'white'}
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(t=20, b=40, l=40, r=60),
        hovermode='x unified'
    )
    
    return fig