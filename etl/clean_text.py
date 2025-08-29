# etl/clean_text.py
import argparse, os, pandas as pd

def main(raw_dir, out_path):
    reddit_path = os.path.join(raw_dir, "reddit.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if not os.path.exists(reddit_path):
        print(f"[clean_text] WARNING: {reddit_path} not found; writing empty {out_path}")
        pd.DataFrame(columns=["created_utc","title","url","issue","subreddit"]).to_csv(out_path, index=False)
        return

    df = pd.read_csv(reddit_path)
    for c in ["created_utc","title","url","issue","subreddit"]:
        if c not in df.columns:
            df[c] = ""
    df[["created_utc","title","url","issue","subreddit"]].to_csv(out_path, index=False)
    print(f"[clean_text] wrote -> {out_path} ({len(df)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    main(args.raw_dir, args.out)
