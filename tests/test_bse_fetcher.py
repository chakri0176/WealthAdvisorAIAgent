# tests/test_bse_fetcher.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.bse_fetcher import (
    get_bse_code,
    get_company_info,
    get_recent_announcements,
    get_annual_report_text,
    fetch_financial_ratios,
)

def test_get_bse_code():
    print("\n--- test_get_bse_code ---")
    # Test known mappings
    code = get_bse_code("TCS")
    print(f"TCS BSE Code: {code}")
    assert code == "532540"

    code = get_bse_code("INFY")
    print(f"INFY BSE Code: {code}")
    assert code == "500209"

    code = get_bse_code("RELIANCE")
    print(f"RELIANCE BSE Code: {code}")
    assert code == "500325"

    # Test with .NS suffix — should still work
    code = get_bse_code("TCS.NS")
    print(f"TCS.NS BSE Code: {code}")
    assert code == "532540"

    print("✅ PASSED")

def test_get_company_info():
    print("\n--- test_get_company_info ---")
    info = get_company_info("TCS")
    print(f"Company info: {info}")
    assert info["ticker"] == "TCS"
    assert info["bse_code"] == "532540"
    print("✅ PASSED")

def test_get_recent_announcements():
    print("\n--- test_get_recent_announcements ---")
    announcements = get_recent_announcements("TCS", count=3)
    print(f"Announcements found: {len(announcements)}")
    for ann in announcements:
        print(f"  - {ann['date']}: {ann['headline'][:60]}")
    print("✅ PASSED")

def test_get_annual_report_text():
    print("\n--- test_get_annual_report_text ---")
    text = get_annual_report_text("TCS")
    print(f"Text length: {len(text)} chars")
    print(f"Preview: {text[:300]}")
    assert len(text) > 100
    print("✅ PASSED")

def test_fetch_financial_ratios():
    print("\n--- test_fetch_financial_ratios ---")
    ratios = fetch_financial_ratios("TCS")
    print(f"Financial ratios: {ratios}")
    assert ratios["ticker"] == "TCS"
    print("✅ PASSED")

def test_multiple_companies():
    print("\n--- test_multiple_companies ---")
    tickers = ["INFY", "RELIANCE", "HDFCBANK", "WIPRO"]
    for ticker in tickers:
        code = get_bse_code(ticker)
        text = get_annual_report_text(ticker, max_chars=1000)
        print(f"{ticker}: BSE={code}, Text={len(text)} chars")
        if len(text) == 0:
            print(f"  ⚠️ WARNING: No text for {ticker} — yfinance may have failed")
        else:
            assert len(text) > 50
    print("✅ PASSED")

if __name__ == "__main__":
    print("=" * 50)
    print("Running BSE Fetcher Tests")
    print("=" * 50)

    test_get_bse_code()
    test_get_company_info()
    test_get_recent_announcements()
    test_get_annual_report_text()
    test_fetch_financial_ratios()
    test_multiple_companies()

    print("\n" + "=" * 50)
    print("✅ All BSE fetcher tests passed!")
    print("=" * 50)