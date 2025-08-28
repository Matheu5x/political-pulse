"""
Fetch Google Trends interest for configured keywords.
Supports --mock to generate deterministic demo data.
"""
import argparse, random, time, json, os
from datetime import datetime, timedelta
import pandas as pd
try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

def mock_trends(keywords):
    today = datetime.utcnow().date()
    dates = [today - timedelta(days=i) for i in range(7)]
    rows = []
    random.seed(42)
    for kw in keywords:
        base = random.randint(20, 60)
        for d in dates:
            val = max(0, min(100, base + random.randint(-10, 15)))
            rows.append({"source":"google_trends","keyword":kw,"date":str(d),"value":val})
    return pd.DataFrame(rows)

def fetch_trends(keywords, geo="US", timeframe="now 7-d"):
    if TrendReq is None:
        raise RuntimeError("pytrends not available. Install or use --mock.")
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop='')
    df = pytrends.interest_over_time().reset_index()
    rows = []
    for _, row in df.iterrows():
        for kw in keywords:
            rows.append({"source":"google_trends","keyword":kw,"date":str(row['date'].date()),"value":int(row[kw])})
    return pd.DataFrame(rows)

def main(keywords, geo, timeframe, out_path, mock=False):
    df = mock_trends(keywords) if mock else fetch_trends(keywords, geo, timeframe)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path.replace("items.csv", "google_trends.csv"), index=False)
    print(f"[google_trends] wrote -> {out_path.replace('items.csv', 'google_trends.csv')}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--keywords", nargs="+", required=True)
    ap.add_argument("--geo", default="US")
    ap.add_argument("--timeframe", default="now 7-d")
    ap.add_argument("--out", default="data/raw/google_trends.csv")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    main(args.keywords, args.geo, args.timeframe, args.out, args.mock)
