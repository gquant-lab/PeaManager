from django.urls import path, include
from quotes import views, dash_instrument_comparison
from quotes.dash_apps.home import app as dash_app
from quotes.dash_apps.portfolio import app as dash_app_portfolio

urlpatterns = [
	path('', views.home, name="home"),
	path('about.html', views.about, name="about"),
	path("portfolio/<str:pk>/", views.portfolio, name="portfolio"),
    path("instrument-comparison", views.instrument_comparison, name="instrument_comparison"),
]