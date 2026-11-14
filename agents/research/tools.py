# agents/researcher/tools.py
import yfinance as yf
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import os

@tool
def get_stock_price(ticker: str) -> str:
    """Get the current stock price for a ticker symbol."""
    try:
        price = yf.Ticker(ticker).fast_info["last_price"] # fetches the latest price for the given ticker symbol
        return f"{ticker} current price: ${price:.2f}"
    except Exception as e:
        return f"Could not fetch price for {ticker}: {e}"

@tool
def calculate_gain(buy_price: float, sell_price: float) -> str:
    """Calculate percentage gain or loss between two prices."""
    if buy_price <= 0:
        return "Buy price must be greater than zero."
    gain = ((sell_price - buy_price) / buy_price) * 100
    return f"Gain/Loss: {gain:+.2f}%" # returns the percentage gain or loss between the buy price and sell price.

# Tavily search tool (max 3 results for better coverage)
search_tool = TavilySearch(
    max_results=3,
    api_key=os.getenv("TAVILY_API_KEY")
)

ALL_TOOLS = [search_tool, get_stock_price, calculate_gain]