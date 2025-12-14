"""
Django forms for the quotes app.
"""
from django import forms
from quotes.models import Order


class OrderForm(forms.ModelForm):
    """
    Form for creating and editing Order objects.
    """
    class Meta:
        model = Order
        fields = ['portfolio', 'id_object', 'date', 'direction', 'nb_items', 'price', 'total_fee']
