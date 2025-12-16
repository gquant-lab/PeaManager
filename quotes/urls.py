from django.urls import path, include
from quotes import views, dash_instrument_comparison
from quotes.dash_apps.portfolio import app as dash_app_portfolio

urlpatterns = [
	path('', views.home, name="home"),
    path('api/chart-data', views.chart_data, name="chart_data"),
	path('about.html', views.about, name="about"),
	path("portfolio/<str:pk>/", views.portfolio, name="portfolio"),
    path("portfolio-native/<str:pk>/", views.portfolio_native, name="portfolio_native"),
    path("instrument-comparison", views.instrument_comparison, name="instrument_comparison"),
]