from django import forms
from .models import Order, FinancialObject

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['id_object', 'date', 'direction', 'nb_items', 'price', 'total_fee']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control bg-dark text-white'}),
            'id_object': forms.Select(attrs={'class': 'form-select bg-dark text-white'}),
            'direction': forms.Select(attrs={'class': 'form-select bg-dark text-white'}),
            'nb_items': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control bg-dark text-white'}),
            'price': forms.NumberInput(attrs={'step': '0.001', 'class': 'form-control bg-dark text-white'}),
            'total_fee': forms.NumberInput(attrs={'step': '0.001', 'class': 'form-control bg-dark text-white'}),
        }