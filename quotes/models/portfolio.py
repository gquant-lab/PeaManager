"""
Portfolio-related models: Portfolio, PortfolioEntry, PortfolioInventory
"""
from django.db import models
from datetime import datetime, date
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Self, TYPE_CHECKING

from .account import AccountOwner
from .financial_object import FinancialObject

if TYPE_CHECKING:
    from .order import Order


@dataclass
class PortfolioEntry:
    """
    Object for tracking an item of the portfolio inventory.

    Args:
        id_obj: FinancialObject on which a position is held
        nb: number of stocks in the portfolio
        pru: euro amount at which the stock needs to be for the overall investment to be worth 0
    """
    fin_obj: FinancialObject
    nb: int
    pru: float

    @classmethod
    def from_order(cls, order: "Order") -> Self:
        """
        Create Portfolio Entry from an order
        """
        if not TYPE_CHECKING:
            from .order import Order
        
        return cls(
            fin_obj = order.id_object, 
            nb = order.nb_items, 
            pru = (order.nb_items * order.price + order.total_fee)/order.nb_items
        )

    def update(self, order):
        """
        Update Portfolio Entry attributes with a new order.
        """
        if not TYPE_CHECKING:
            from .order import Order
        
        if order.id_object.id == self.fin_obj.id:
            # We assume the order is on the same Financial Instrument as the PortfolioEntry
            
            if order.direction == Order.OrderDirection.BUY:
                # Update self.nb once pru has been calculated
                self.pru = (self.pru * self.nb + order.nb_items * order.price + order.total_fee)/(self.nb + order.nb_items)
                self.nb += order.nb_items
                
            else:
                if self.nb == order.nb_items:
                    # Sell everything
                    self.nb = 0
                    self.pru = 0
                
                else:
                    self.pru = (self.pru * self.nb - order.nb_items * order.price + order.total_fee)/ (self.nb - order.nb_items)
                    self.nb -= order.nb_items


class PortfolioInventory:
    """
    A list of PortfolioEntry. The class regroups useful methods to easily manipulate underlying FinancialObjects.
    """

    def __init__(self, portfolio_entries: list[PortfolioEntry]):
        """
        Preferred way to build one is from a list of PortfolioEntry
        """
        self.portfolio_entries = portfolio_entries

    @classmethod
    def from_orders(cls, orders):
        """
        Possible to build one from a bunch of orders
        """
        pass
    
    @classmethod
    def from_portfolio(cls, portfolio):
        """
        Possible to build one from a portfolio
        """
        pass

    @property
    def id_objects(self) -> list[str]:
        return [item.fin_obj.id for item in self.portfolio_entries]
    
    @property
    def fin_objs(self) -> list[FinancialObject]:
          return [item.fin_obj for item in self.portfolio_entries]
    
    @property
    def names(self) -> list[str]:
        return [item.fin_obj.name for item in self.portfolio_entries]

    @property
    def nbs (self) -> list[int]:
        return [item.nb for item in self.portfolio_entries]

    @property    
    def prus(self) -> list[float]:
          return [item.pru for item in self.portfolio_entries]

    @property
    def weights(self) -> dict[FinancialObject, float]:
        pass

    def to_df(self) -> pd.DataFrame:
        """
        Inventory to df with columns Id, Name, Number, PRU
        """
        rows = {i: [item.fin_obj.id, item.fin_obj.name, item.nb, item.pru] for i, item in enumerate(self.portfolio_entries)}
        return pd.DataFrame.from_dict(rows, orient='index', columns=["Id", "Name", "Number", "PRU"])

    def __len__(self) -> int:
        return len(self.portfolio_entries)


class Portfolio(models.Model):
    
    owner = models.ForeignKey(AccountOwner, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, default="")

    ts_ret = None
    ts_val = None
    ts_cumul_ret = None

    def __str__(self):
        return f"{self.owner} - {self.name}"

    @property
    def orders(self) -> models.QuerySet["Order"]:
        """
        Queries the order database and returns all orders associated to Portfolio in date ascending order
        """
        if not TYPE_CHECKING:
            from .order import Order
        return Order.objects.filter(portfolio=self.id).order_by("date")

    def inventory_df(self) -> pd.DataFrame:
          """
          Get current inventory in a dataframe, ordered by descending rows of weight
          """
          return self.get_inventory().to_df()

    def get_inventory(self, date=datetime.today()) -> PortfolioInventory:
        """
        Given a date, return a list of Portfolio Entries with current inventory.
        """        
        all_orders = self.orders.filter(date__lte=date).order_by("date")
        
        curr_inventory: PortfolioInventory = []

        for order in all_orders:
            if curr_inventory and order.id_object.id in [entry.fin_obj.id for entry in curr_inventory]:
                # Inventory not empty and Financial Instrument already in Portfolio
                for entry in curr_inventory:
                    entry.update(order)

            else:
                curr_inventory.append(PortfolioEntry.from_order(order))

        return PortfolioInventory([entry for entry in curr_inventory if entry and entry.nb != 0])

    def get_weights(self) -> dict[str, float]:
        """
        Returns dictionary {FinancialInstrument: weight} for most recent portfolio data
        """
        from .financial_data import FinancialData

        most_recent_date = FinancialData.get_price_most_recent_date()
        
        inventory = self.get_inventory(most_recent_date)
        
        # Get NAV df
        qs = [FinancialData.objects\
                    .filter(id_object=obj, field="NAV", origin="Yahoo Finance", date=most_recent_date)\
                    .values_list("value", flat=True) for obj in inventory.fin_objs]
        
        # Evaluate Query set to only have lists
        qs = [list(q) for q in qs]

        # unlist
        prices = [x for xs in qs for x in xs]
        
        amounts = [price * nb for price, nb in zip(prices, inventory.nbs)]

        return {k: v/sum(amounts) for k,v in zip(inventory.names, amounts)}

    def get_TS(self) -> None:
        """
        Returns the time series of the portfolio since its inception
        """
        from .yahoo_finance import YahooFinanceQuery
        
        # Retrieve all orders
        all_order_dates = set([order.date for order in self.orders.all()])
        all_order_dates = sorted(all_order_dates, reverse=False)

        if len(all_order_dates) == 0:
            raise Exception("No order data.")

        # Add today so that the time series is computed until today
        all_order_dates.append(datetime.today().date())

        ts = []
        ts_ret = []

        for i, order_date in enumerate(all_order_dates):
            if i == 0:
                continue

            start = all_order_dates[i-1]
            inventory = self.get_inventory(start)
            prices_df = YahooFinanceQuery.get_prices_from_inventory(fin_objs = inventory.fin_objs,
                                                                 from_date = start,
                                                                 until_date = order_date)

            # Make inventory a 2d numpy array
            inventory = np.array(inventory.nbs)
            
            ##### Return computation
            # Approximation: change in number of stocks only come into
            # effect at the end of the day when the order was placed.
            
            # Remove rows with NA, compute returns and remove first NA row
            prices_without_na = prices_df.dropna(axis=0, how="any")
            rets = prices_without_na.pct_change()[1:]

            # EUR amount in each stock is stock_price x nb_stock
            # Dimensions: (n_stocks, 1) = (n_dates -1, n_stocks) x (1, n_stocks)
            amount_per_stock = prices_without_na[:-1] * inventory
            

            # div because element-wise division
            weights = amount_per_stock.div(amount_per_stock.sum(axis=1), axis=0)
            
            # Keep rets date index
            ptf_ret = (rets * weights.set_index(rets.index)).sum(axis=1)        

            ts_ret.append(ptf_ret)

            ##### Portfolio TS computation
            # matrix multiplication
            if i == len(all_order_dates) -1:
                # last one
                ts.append(prices_without_na.dot(inventory))
            else:
                ts.append(prices_without_na.dot(inventory).iloc[:-1])
            

        self.ts_ret = pd.concat(ts_ret, axis=0).squeeze()
        self.ts_val = pd.concat(ts, axis=0).squeeze()
        self.ts_cumul_ret = pd.concat([
            self.ts_ret.add(1), 
            pd.Series([1], index=[all_order_dates[0]])
            ])
        self.ts_cumul_ret.sort_index(inplace=True)
        self.ts_cumul_ret = self.ts_cumul_ret.cumprod()

        self.ts_val.to_excel("TS_val.xlsx")
        self.ts_ret.to_excel("TS_ret.xlsx")

    def get_individual_returns(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Lines: All Financial Instruments that have been in the portfolio during the time frame
        Columns: Price contribution, Dividend contribution, Total contribution 
        """
        from .order import Order
        from .yahoo_finance import YahooFinanceQuery
        
        # Retrieve all Financial Instruments that have been in the portfolio during the time frame
        fin_ins = self.get_inventory(start_date).fin_objs
        subsequent_orders = Order.objects.filter(portfolio=self, date__gte=start_date, date__lte=end_date)
        fin_ins.extend([ord.id_object for ord in subsequent_orders])
        all_fin_instr = list(set(fin_ins))

        # Load Time Series during the time frame
        prices = YahooFinanceQuery.get_prices_from_inventory(fin_objs = all_fin_instr, from_date = start_date, until_date = end_date)        
        prices.index = pd.to_datetime(prices.index)
        divs = YahooFinanceQuery.get_divs_from_inventory(fin_objs = all_fin_instr, from_date = start_date, until_date = end_date)
        divs.index = pd.to_datetime(divs.index)

        available_start_date = prices.index[0]
        available_end_date = prices.index[-1]

        rets = dict()

        for fin in all_fin_instr:
            # quantity did not vary during time frame
            price_ret_tf = prices.loc[available_end_date][fin.name] / prices.loc[available_start_date][fin.name] - 1
            div_ret_tf = sum(divs[fin.name]) / prices[fin.name][available_start_date]
            total_ret_tf = price_ret_tf + div_ret_tf
            
            rets[fin.name] = [price_ret_tf, div_ret_tf, total_ret_tf]

        return pd.DataFrame.from_dict(rets, orient="index", columns=["Price", "Dividends", "Total"])
