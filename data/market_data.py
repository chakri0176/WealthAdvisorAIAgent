#in data/market_data.py
import yfinance as yf
import pandas as pd
from typing import Optional

def resolve_ticker(ticker: str) -> str:
    """Auto-add .NS suffix for Indian NSE stocks."""
    ticker = ticker.strip().upper()
    if ticker.endswith(".NS") or ticker.endswith(".BO"):
        return ticker
    return f"{ticker}.NS"

def get_key_metrics(ticker: str) -> dict:
    ticker = resolve_ticker(ticker)
    stock = yf.Ticker(ticker)
    dat = stock.info
    return {
        "ticker": ticker,
        "company_name": dat.get("longName", "N/A"),
        "sector": dat.get("sector", "N/A"),
        "market_cap": dat.get("marketCap", 0),
        "beta": dat.get("beta", None),
        "current_price": dat.get("currentPrice", None),
        "currency": dat.get("currency", "INR"),
        "exchange": dat.get("exchange", "NSE"),
    }
    
def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    ticker = resolve_ticker(ticker)
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    df = df.dropna()
    return df

def calculate_portfolio_metrics(holdings: list)->dict:
    results = []
    for holding in holdings:
        metrics = get_key_metrics(holding["ticker"])
        results.append(metrics)
    return {
        "holdings": results,
        "num_positions": len(holdings)
    }