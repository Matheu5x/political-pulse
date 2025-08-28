"""
Very simple rule-based issue classification (placeholder for LLM).
Adds 'issue_final' column using keywords + fallback to existing 'issue'.
"""
import argparse, pandas as pd, os, re

RULES = {
    "economy": r"\b(inflation|jobs?|wages?|gdp|economy|cost of living)\b",
    "crime": r"\b(crime|police|violence|theft|carjacking|safety)\b",
    "immigration": r"\b(immigration|border|asylum|migrants?|visa)\b",
    "healthcare": r"\b(healthcare|medicare|insurance|drug prices?|hospitals?)\b",
    "education": r"\b(schools?|curriculum|teachers?|students?|education)\b",
}

def label(text, existing_issue):
    t = str(text).lower()
    for issue, pat in RULES.items():
        if re.search(pat, t):
            return issue
    return existing_issue or "other"

def main(in_csv, out_csv):
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df = pd.read_csv(in_csv)
    df['issue_final'] = [label(t, i) for t, i in zip(df['title'], df.get('issue', 'other'))]
    df.to_csv(out_csv, index=False)
    print(f"[classifier] wrote -> {out_csv}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", default="data/processed/items_with_sentiment.csv")
    ap.add_argument("--out", dest="out_csv", default="data/processed/items_enriched.csv")
    args = ap.parse_args()
    main(args.in_csv, args.out_csv)
