import requests
import time
from config.settings import get_settings
import json

settings = get_settings()

def get_cik(ticker: str)->str:
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": settings.sec_user_agent}
    response = requests.get(url,headers=headers)
    data = response.json()
    for entry in data.values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    return None

def get_recent_filings(ticker: str,form_type: str="10-K",count: int = 3)->list:
    cik = get_cik(ticker)
    filings = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": settings.sec_user_agent}
    response = requests.get(filings,headers=headers)
    data = response.json()
    results = []
    cnt = 0
    for form, acc, date in zip(data["filings"]["recent"]["form"],data["filings"]["recent"]["accessionNumber"],data["filings"]["recent"]["filingDate"]):
        if form == form_type:
            results.append({
                "ticker": ticker,
                "form": form,
                "accessionNumber": acc,
                "filingDate": date
            })
            cnt+=1
            if cnt == count:
                break
    time.sleep(0.1)
    return results
        

def fetch_filing_text(accession_number: str,ticker: str,max_chars: int = 50000)->str:
    cik = get_cik(ticker)
    acc_clean = accession_number.replace("-","")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/{accession_number}.txt"
    headers = {"User-Agent": settings.sec_user_agent}
    response = requests.get(url,headers=headers)
    return response.text[:max_chars]
    