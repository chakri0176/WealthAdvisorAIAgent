#in data/market_data.py
import yfinance as yf

def get_key_metrics(ticker: str)->dict:
    stock = yf.Ticker(ticker)
    dat = stock.info
    return {
        "ticker": ticker,
        "company_name": dat.get("longName","N/A"),
        "sector": dat.get("sector","N/A"),
        "market_cap": dat.get("marketCap","0"),
        "beta": dat.get("beta", None),
        "current_price": dat.get("currentPrice", None)
    }
    
def get_price_history(ticker: str, period: str = "1y" )->str:
    stock = yf.Ticker(ticker)
    return stock.history(period)

def calculate_portfolio_metrics(holdings: list)->dict:
    results = []
    for holding in holdings:
        metrics = get_key_metrics(holding["ticker"])
        results.append(metrics)
    return {
        "holdings": results,
        "num_positions": len(holdings)
    }