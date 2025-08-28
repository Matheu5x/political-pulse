"""
Fetch Google Trends interest by US state for configured keywords. Supports --mock.
"""
import argparse, os, random
import pandas as pd

try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

US_STATES = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","District of Columbia",
    "Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine",
    "Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
    "New Hampshire","New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma",
    "Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
    "Virginia","Washington","West Virginia","Wisconsin","Wyoming"
]

def mock_regions(keywords):
    random.seed(123)
    rows = []
    for kw in keywords:
        for st in US_STATES:
            val = max(0, min(100, random.randint(20, 80) + (hash(kw + st) % 15 - 7)))
            rows.append({"state": st, "keyword": kw, "value": int(val)})
    return pd.DataFrame(rows)

def fetch_regions(keywords):
    if TrendReq is None:
        raise RuntimeError("pytrends not available. Install or use --mock.")
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='US', gprop='')
    # interest_by_region signature varies by version – safest to omit 'geo' param here:
    df = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=False)
    df = df.reset_index()
    print("[regions] columns after reset_index:", list(df.columns))
    # find the state column robustly
    candidates = ["geoName","region","sub_region","DMA","State","STATE","state","index","GeoName","NAME"]
    state_col = next((c for c in candidates if c in df.columns), None)
    if not state_col:
        raise RuntimeError(f"Could not find state column. Columns: {list(df.columns)}")
    df = df.rename(columns={state_col: "state"})
    rows = []
    for _, row in df.iterrows():
        st = str(row["state"])
        for kw in keywords:
            v = int(row[kw]) if kw in row and pd.notna(row[kw]) else 0
            rows.append({"state": st, "keyword": kw, "value": v})
    return pd.DataFrame(rows)

def main(keywords, out_path, mock=False):
    df = mock_regions(keywords) if mock else fetch_regions(keywords)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"[google_trends_regions] wrote -> {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--keywords", nargs="+", required=True)
    ap.add_argument("--out", default="data/raw/google_trends_regions.csv")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    main(args.keywords, args.out, args.mock)
