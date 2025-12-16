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

from quotes.models import Portfolio, FinancialData
from quotes.utils.chart_creation import create_portfolio_chart, get_portfolio_performance



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
	# Send back a string to dash template in the context
	context = {
		"dash_context": {"pk": {"title": pk}}
			   }
	return render(request, "portfolio.html", context)


def instrument_comparison(request):
	
    return render(request, "instrument_comparison.html", {})


def databases(request):
	return render(request, "databases.html", {})