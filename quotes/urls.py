from django.urls import path, include
from quotes import views

urlpatterns = [
	path('', views.home, name="home"),
    path('api/chart-data', views.chart_data, name="chart_data"),
	path('about.html', views.about, name="about"),
	path("portfolio/<str:pk>/", views.portfolio, name="portfolio"),
    path("portfolio/<str:pk>/chart/", views.portfolio_chart_data, name="portfolio_chart_data"),
    path("instrument-comparison", views.instrument_comparison, name="instrument_comparison"),
    path('api/delete-order/<int:order_id>/', views.delete_order, name="delete_order"),
    path('api/add-order/<str:pk>/', views.add_order, name="add_order"),
    path("portfolio/<str:pk>/orders/", views.portfolio_orders, name="portfolio_orders"),
    path("order_form/<str:pk>/", views.order_form, name="order_form"),
    path("order/<int:order_id>/edit/", views.edit_order, name="edit_order"),
]