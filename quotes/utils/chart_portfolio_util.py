import numpy as np

from quotes.models import Portfolio, FinancialData

def performance_overview(id_portfolio):
    """
    Create the performance overview table showing portfolio positions.
    """
    ptf = Portfolio.objects.get(id=id_portfolio)
    latest_date = FinancialData.get_price_most_recent_date()

    df = ptf.inventory_df()
    df["Amount_Paid"] = df["PRU"] * df["Number"]

    prices = [
        FinancialData.objects
        .filter(id_object=id, field="NAV", origin="Yahoo Finance", date=latest_date)
        .values_list("value", flat=True).first() 
        for id in df["Id"].tolist()
    ]
    
    df["Current_Value"] = np.multiply(df["Number"], np.array(prices))
    df.sort_values(by="Current_Value", ascending=False, inplace=True)

    df["Pnl"] = df["Current_Value"] - df["Amount_Paid"]
    df["Weight"] = df["Current_Value"] / df["Current_Value"].sum()
    df["Weight"] = df["Weight"].map('{:,.1%}'.format)
    
    del df["Id"]

    numeric_cols = ["PRU", "Amount_Paid", "Current_Value", "Pnl"]
    df[numeric_cols] = df[numeric_cols].map('{:,.2f}'.format)

    return df.to_dict(orient="records")