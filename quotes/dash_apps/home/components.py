import dash_bootstrap_components as dbc
from dash import dcc, html

from quotes.models import Portfolio, FinancialData
from quotes.dash_apps.home.utils import timeframe_to_limit_date


def get_performance_table() -> dbc.Table:

    portfolios = Portfolio.objects.all()
    for ptf in portfolios:
        if ptf.ts_ret is None:
            ptf.get_TS()
    latest_date = FinancialData.get_price_most_recent_date()

    columns = ["Portfolio", "1M", "3M", "6M", "YTD", "1Y"]
    header_style = {"background-color": "transparent", "color": "light-blue"}
    
    table_header = [
        html.Thead(html.Tr(
            [html.Th(col, style=header_style) for col in columns]
        ))
    ]

    limit_dates = [timeframe_to_limit_date(tmf) for tmf in columns[1:]]
    
    #intersect dates of all portfolios
    available_dates = list(portfolios[0].ts_val.index)
    
    for i, date in enumerate(limit_dates):
        if not date in available_dates:
            # Take the closest one before
            limit_dates[i] = max(d for d in available_dates if d < date)

    rows = []

    # Row headers: hyperlinks to the portfolio
    row_headers = [html.A(f"{ptf.owner.name} - {ptf.name}", href=f"/portfolio/{ptf.id}") for ptf in portfolios]
    perfs = [
        [ptf.ts_cumul_ret[latest_date] / ptf.ts_cumul_ret[limit_date] -1 for limit_date in limit_dates] for ptf in portfolios]
    
    for row_header, perf_ptf in zip(row_headers, perfs):
        rows.append(
            html.Tr([
                html.Td(row_header, style={}),
                *[html.Td("{:.2%}".format(perf), style={}) for perf in perf_ptf]
            ])
        ) 
    
    table_body = [html.Tbody(rows)]

    return dbc.Table(table_header + table_body, 
                      hover=True, 
                      color="dark",
                      style={"text-align": "center", "border": "none", "background-color": "transparent"},
                     )
