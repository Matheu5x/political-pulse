"""
Apply VADER sentiment to items.csv and write items_with_sentiment.csv
"""
import argparse, pandas as pd, os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def main(in_csv, out_csv):
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df = pd.read_csv(in_csv)
    analyzer = SentimentIntensityAnalyzer()
    scores = df['title'].fillna("").apply(lambda t: analyzer.polarity_scores(str(t))['compound'])
    df['sentiment'] = scores
    df.to_csv(out_csv, index=False)
    print(f"[sentiment] wrote -> {out_csv}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", default="data/processed/items.csv")
    ap.add_argument("--out", dest="out_csv", default="data/processed/items_with_sentiment.csv")
    args = ap.parse_args()
    main(args.in_csv, args.out_csv)
