from flask import request
from plotly.graph_objs import YAxis
import datetime as dt
from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from plotly.utils import PlotlyJSONEncoder

from quotes.models import Portfolio, FinancialData, Order, FinancialObject
from quotes.utils.chart_creation import create_portfolio_chart, get_portfolio_performance
from quotes.utils.chart_portfolio_util import performance_overview, get_order_history, create_allocation_chart, create_portfolio_performance_chart
from quotes.utils.date_helpers import prev_business_day, get_first_business_day_of_month
from .forms import OrderForm


def home(request):
    portfolios = Portfolio.objects.all()
    latest_date = FinancialData.get_price_most_recent_date()

    fig = create_portfolio_chart(portfolios, "Returns", "max", None)
    chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # Get performance data for the table
    performance_data = get_portfolio_performance(portfolios, latest_date)
    
    context = {
        'portfolios': portfolios,
        'latest_date': latest_date,
        'chart': chart_json,
        'performance_data': performance_data,
        'timeframes': ["1M", "3M", "6M", "YTD", "1Y"],
    } 

    return render(request, "home.html", context)



def chart_data(request):
    """
    API endpoint that returns updated chart data based on timeframe and mode.
    Called by JavaScript when user clicks timeframe buttons or changes chart mode.
    """
    # Get parameters from request
    time_frame = request.GET.get('timeframe', 'max')
    chart_mode = request.GET.get('mode', 'Returns')
    
    # Fetch portfolios
    portfolios = Portfolio.objects.all()
    
    # Create chart with requested parameters
    fig = create_portfolio_chart(
        portfolios=portfolios,
        chart_mode=chart_mode,
        time_frame=time_frame,
        custom_dates=None
    )
    
    # Return JSON response
    chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    return JsonResponse({
        'chart': json.loads(chart_json)
    })


def about(request):
    return render(request, "about.html", {})


def portfolio(request, pk):
    """
    For a given portfolio, provides the inventory and cumulative amount invested 
    """
    import numpy as np
    
    ptf = Portfolio.objects.get(id=pk)
    latest_date = FinancialData.get_price_most_recent_date()

    inventory = ptf.get_inventory(latest_date)

    if ptf.ts_val is None:
        ptf.get_TS()

    # Portfolio Value
    ptf_value = ptf.ts_val[latest_date]
    
    # Portfolio PnL
    pnl = ptf_value - np.dot(inventory.nbs, inventory.prus)

    # Allocation chart
    allocation_chart = create_allocation_chart(pk)
    allocation_json = json.dumps(allocation_chart, cls=PlotlyJSONEncoder)

    # Performance chart
    performance_chart = create_portfolio_performance_chart(pk)
    performance_json = json.dumps(performance_chart, cls=PlotlyJSONEncoder)

    # inventory table
    inv_df = performance_overview(pk)
    
    # order history
    orders = get_order_history(pk)
    financial_objects = FinancialObject.objects.all()

    form = OrderForm()

    # Send back a string to dash template in the context
    context = {
        'ptf_value': ptf_value,
        'pnl': pnl,
        'latest_date': latest_date,
        'allocation_chart': allocation_json,
        'performance_chart': performance_json,
        'inventory': inv_df,
        'orders': orders,
        'financial_objects': financial_objects,
        'pk': pk,
        'form': form,
    }
    return render(request, "portfolio.html", context)


def portfolio_chart_data(request, pk):
    """
    AJAX endpoint to get portfolio performance chart data for a specific timeframe.
    """
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    year = request.GET.get('year')

    if start_date and end_date:
        chart = create_portfolio_performance_chart(pk, start_date=start_date, end_date=end_date)
        
    elif year:
        start_date = get_first_business_day_of_month(int(year), 1)
        end_date = prev_business_day(get_first_business_day_of_month(int(year)+1, 1))
        chart = create_portfolio_performance_chart(pk, 
                                                   start_date=start_date.strftime('%Y-%m-%d'),
                                                   end_date=end_date.strftime('%Y-%m-%d')
                                                   )
    else:
        timeframe = request.GET.get('timeframe', 'max')
        chart = create_portfolio_performance_chart(pk, timeframe)
    
    # Return as JSON
    return JsonResponse(chart.to_dict(), encoder=PlotlyJSONEncoder)


def delete_order(request, order_id):
    """
    Delete an order and return the updated orders table.
    """
    order = Order.objects.get(id=order_id)
    portfolio_id = order.portfolio.id
    financial_objects = FinancialObject.objects.all()

    # Delete the order
    order.delete()

    # Get updated order history
    orders = get_order_history(portfolio_id)

    # Only return the updated table HTML
    return render(request, "partials/portfolio/row4_orders_tab.html", {'orders': orders, 'pk': portfolio_id, 'financial_objects': financial_objects})

def add_order(request, pk):
    """
    Add a new order and return the updated orders table.
    """
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.portfolio_id = pk
            order.save()
            # Get updated order list and render template
            orders = get_order_history(pk)
            financial_objects = FinancialObject.objects.all()
            return render(request, 'partials/portfolio/row4_orders_tab.html', {
                'orders': orders,
                'pk': pk,
                'financial_objects': financial_objects
            })
        else:
            return render(request, 'template.html', {
                'form': form,
                'orders': orders,
                'pk': pk,
            })


def instrument_comparison(request):
    
    return render(request, "instrument_comparison.html", {})


def databases(request):
    return render(request, "databases.html", {})