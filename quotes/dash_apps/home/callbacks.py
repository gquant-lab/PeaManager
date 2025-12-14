import dash
from datetime import datetime, date
import plotly.graph_objects as go
import pandas as pd

from quotes.models import Portfolio
from quotes.dash_apps.home.styles import user_colors
from quotes.dash_apps.home.utils import timeframe_to_limit_date


portfolios = Portfolio.objects.all()


def register_callbacks(app: dash.Dash):
    """
    Register all callbacks for the home dash app.
    """
    ##### CALLBACKS
    # Price/Return callback
    @app.callback(
        dash.dependencies.Output('graph-ts', 'figure'),
        dash.dependencies.Input('radio-chart-mode', 'value'),
        dash.dependencies.Input('btn-horizon-1m', 'n_clicks'),
        dash.dependencies.Input('btn-horizon-3m', 'n_clicks'),
        dash.dependencies.Input('btn-horizon-6m', 'n_clicks'),
        dash.dependencies.Input('btn-horizon-ytd', 'n_clicks'),
        dash.dependencies.Input('btn-horizon-1y', 'n_clicks'),
        dash.dependencies.Input('btn-horizon-3y', 'n_clicks'),
        dash.dependencies.Input('btn-horizon-max', 'n_clicks'),
        dash.dependencies.Input('date-range-picker', 'value')
    )
    def update_the_graph(chart_mode: str, btn_1m, btn_3m, btn_6m, btn_ytd, btn_1y, btn_3y, btn_max, date_range, callback_context):
        """
        Update the chart when either the buttons, or the daterangepicker is modified.
        """
        
        last_modif = None

        # Find the last item changed (either new time or new radio item)
        if len(callback_context.triggered):
            last_modif = callback_context.triggered[0]["prop_id"].split(".")[0]

        if last_modif is None:
            # First callback: return right series on max time
            time_frame = 'max'

        elif last_modif in ["date-range-picker", "radio-chart-mode"]:
            # Prices/returns modif or change of date
            time_frame = "custom"
        
        else:
            # Change was on time frame (buttons of second row pressed)
            # Find requested time frame
            time_frame = last_modif.split("-")[-1]

        chart = get_traces(portfolios=portfolios,
                        series_mode=chart_mode,
                        time_frame=time_frame,
                        custom_dates=date_range)

        return chart


    def get_traces(portfolios: list[Portfolio], series_mode: str, time_frame: str, custom_dates: list[datetime]) -> go.Figure:
        """
        Depending on the price/return series requested, provide the series to chart on the right time frame.
        """
        if not series_mode in ["Prices", "Returns"]:
            raise Exception("Series_mode parameter is not right: either prices or returns.")
        
        # Ensure all portfolios have time series data loaded
        for ptf in portfolios:
            if ptf.ts_ret is None:
                ptf.get_TS()
        
        ts_mode = "ts_val" if series_mode == "Prices" else "ts_cumul_ret"

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
                y=list(ts.values) if series_mode == "Prices" else list((ts/ts.iloc[0]).values -1),
                name=portfolios[i].owner.name,
                line = {"color": user_colors[portfolios[i].owner.name], "width": 4}
            )
            l_traces.append(chart)
            
        fig = go.Figure(data=l_traces)
        
        # Customize the charting options
        if series_mode == "Returns":
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
            
        elif series_mode == "Prices":
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

        
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)')

        return fig


    @app.callback(
        dash.dependencies.Output('date-range-picker', 'value'),
        dash.dependencies.Input('graph-ts', 'figure'),
        prevent_initial_call=True
    )
    def update_date_range_picker(fig: go.Figure):
        """
        Whenever the figure changes (i.e. whenever a button is pressed), adjust the values
        in the date picker.
        """
        min_dates = [fig["data"][i]["x"][0] for i in range(0, len(fig["data"]))]
        min_dates = [datetime.strptime(date, "%Y-%m-%d") for date in min_dates]

        max_dates = [fig["data"][i]["x"][-1] for i in range(0, len(fig["data"]))]
        max_dates = [datetime.strptime(date, "%Y-%m-%d") for date in max_dates]

        return (min(min_dates).date(), max(max_dates).date())