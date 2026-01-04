from datetime import datetime, date
import plotly.graph_objects as go
import pandas as pd

from quotes.models import Portfolio
from quotes.utils.date_helpers import prev_business_day, get_first_business_day_of_month


user_colors = {
    "Guillaume": "darkorange",
    "Marie": "darkgreen",
    "Maman": "darkred"
}


def timeframe_to_limit_date(time_frame: str) -> date:
    """
    From the button pressed (ex. 6m), return the associated start_date assuming the end_date is today.
    """
    match time_frame.lower():
        case "1m" | "3m" | "6m":
            nb_months = time_frame[0]
            start_datetime = datetime.today() - pd.tseries.offsets.DateOffset(months=int(nb_months))
            return start_datetime.date()
        
        case "mtd":
            current_year = datetime.today().year
            current_month = datetime.today().month
            return get_first_business_day_of_month(current_year, current_month)
        
        case "lme":
            current_year = datetime.today().year
            current_month = datetime.today().month
            first_day_month = get_first_business_day_of_month(current_year, current_month)            
            return prev_business_day(first_day_month) 

        case "qtd":
            current_month = datetime.today().month
            quarter_start_month = ((current_month - 1) // 3) * 3 + 1
            return get_first_business_day_of_month(datetime.today().year, quarter_start_month)
        
        case "htd":
            current_month = datetime.today().month
            half_start_month = 1 if current_month <= 6 else 7
            return get_first_business_day_of_month(datetime.today().year, half_start_month)

        case "ytd":
            current_year = datetime.today().year
            if prev_business_day(date.today()).year < current_year:
                return get_first_business_day_of_month(current_year - 1, 1)
            else: 
                return get_first_business_day_of_month(current_year, 1)

        case "1y" | "3y":
            nb_years = time_frame[0]
            start_datetime = datetime.today() - pd.tseries.offsets.DateOffset(years=int(nb_years)) 
            return start_datetime.date()

        case "max":
            return date(2000, 1, 1)




def create_portfolio_chart(portfolios: list[Portfolio], chart_mode: str, time_frame: str, custom_dates: list[datetime]) -> go.Figure:
    """
    Depending on the price/return series requested, provide the series to chart on the right time frame.
    """
    if not chart_mode in ["Prices", "Returns"]:
        raise Exception("chart_mode parameter is not right: either prices or returns.")
    
    # Ensure all portfolios have time series data loaded
    for ptf in portfolios:
        if ptf.ts_ret is None:
            ptf.get_TS()
    
    ts_mode = "ts_val" if chart_mode == "Prices" else "ts_cumul_ret"

    # Get relevant series on the adequate time frame
    if time_frame == "custom":
        start, end = [datetime.strptime(date, "%Y-%m-%d") for date in custom_dates]
        l_ts = [
            getattr(ptf, ts_mode)[(start.date() <= getattr(ptf, ts_mode).index) & (getattr(ptf, ts_mode).index <= end.date())]
            for ptf in portfolios]
    
    else:
        limit_date = timeframe_to_limit_date(time_frame)
        l_ts = [
            getattr(ptf, ts_mode)[getattr(ptf, ts_mode).index >= limit_date]
            for ptf in portfolios]

    l_traces = []

    for i, ts in enumerate(l_ts):
        # All start from 0% is returns are requested, else the usual series of prices
        chart = go.Scatter(
            x=list(ts.index),
            y=list(ts.values) if chart_mode == "Prices" else list((ts/ts.iloc[0]).values -1),
            name=portfolios[i].owner.name,
            line = {"color": user_colors[portfolios[i].owner.name], "width": 4}
        )
        l_traces.append(chart)
        
    fig = go.Figure(data=l_traces)
    
    # Customize the charting options
    if chart_mode == "Returns":
        fig.update_layout(yaxis={
                            "side": "right", 
                            "tickformat": ".0%", 
                            "hoverformat": ".2%", 
                            "gridwidth": 1, 
                            "zerolinecolor": "lightgray", 
                            "tickfont": {"color": "white", "size": 14}
                            },
                        xaxis={
                            "dtick": "M1",
                            "tickformat": "%b\n%Y",
                            "hoverformat": "%d/%m/%Y",
                            "ticklabelmode": "period",
                            "showgrid": False, 
                            "tickfont": {"color": "white"},
                            "rangeslider": {"visible": True, "bgcolor": "darkgray"}
                            },
                        legend={
                            "orientation": "h",
                            "yanchor": "bottom",
                            "y": 1.02, 
                            "xanchor": "right", 
                            "x":1, 
                            "font": {"size": 18, "color": "white"}
                            }
                        )
        
    elif chart_mode == "Prices":
        fig.update_layout(yaxis={
                            "side": "right", 
                            "tickformat": ",.0f", 
                            "hoverformat": ",.0f", 
                            "gridwidth": 1, 
                            "zerolinecolor": "lightgray", 
                            "tickfont": {"color": "white", "size": 14}
                            },
                        xaxis={
                            "dtick": "M1",
                            "tickformat": "%b\n%Y",
                            "hoverformat": "%d/%m/%Y",
                            "ticklabelmode": "period",
                            "showgrid": False, 
                            "tickfont": {"color": "white"},
                            "rangeslider": {"visible": True, "bgcolor": "darkgray"}
                            },
                        legend={
                            "orientation": "h",
                            "yanchor": "bottom",
                            "y": 1.02, 
                            "xanchor": "right", 
                            "x":1, 
                            "font": {"size": 18, "color": "white"}
                            }
                        )

    
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')

    return fig


def get_portfolio_performance(portfolios: list[Portfolio], latest_date: date) -> list[dict]:
    """
    Calculate performance for each portfolio across different timeframes.
    Returns a list of dicts with portfolio info and performance data.
    """
    timeframes = ["1M", "3M", "6M", "YTD", "1Y"]
    limit_dates = [timeframe_to_limit_date(tmf) for tmf in timeframes]
    
    # Ensure all portfolios have time series data loaded
    for ptf in portfolios:
        if ptf.ts_ret is None:
            ptf.get_TS()
    
    # Get available dates from first portfolio
    available_dates = list(portfolios[0].ts_val.index)
    
    # Adjust limit dates to closest available date before the target
    for i, limit_date in enumerate(limit_dates):
        if limit_date not in available_dates:
            closest_dates = [d for d in available_dates if d < limit_date]
            if closest_dates:
                limit_dates[i] = max(closest_dates)
    
    # Calculate performance for each portfolio
    performance_data = []
    for ptf in portfolios:
        perf_dict = {
            'portfolio_name': f"{ptf.owner.name} - {ptf.name}",
            'portfolio_id': ptf.id,
            'owner_name': ptf.owner.name,
            'performances': []
        }
        
        for limit_date in limit_dates:
            if limit_date in ptf.ts_cumul_ret.index and latest_date in ptf.ts_cumul_ret.index:
                perf = ptf.ts_cumul_ret[latest_date] / ptf.ts_cumul_ret[limit_date] - 1
                perf_dict['performances'].append(perf)
            else:
                perf_dict['performances'].append(None)
        
        performance_data.append(perf_dict)
    
    return performance_data


