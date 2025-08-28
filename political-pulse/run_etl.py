# """
# One-command ETL orchestrator.
# Usage:
#   python run_etl.py          # live mode (requires creds)
#   python run_etl.py --mock   # generates demo data
# """
# import argparse, yaml, os, subprocess, sys
#
# def sh(cmd):
#     print("[cmd]", " ".join(cmd))
#     subprocess.check_call(cmd)
#
# def main(mock=False):
#     with open("config.yaml", "r") as f:
#         cfg = yaml.safe_load(f)
#
#     # Fetch Google Trends
#     gt = cfg.get("google_trends", {})
#     kw = gt.get("kw_list", ["economy","crime","immigration","healthcare","education"])
#     args = ["python","etl/fetch_google_trends.py","--keywords", *kw, "--geo", gt.get("geo","US"),
#             "--timeframe", gt.get("timeframe","now 7-d"), "--out","data/raw/google_trends.csv"]
#     if mock: args.append("--mock")
#     sh(args)
#
#     # Fetch Reddit
#     rd = cfg.get("reddit", {})
#     subs = rd.get("subreddits", ["politics"])
#     args = ["python","etl/fetch_reddit.py","--subs", *subs, "--limit", str(rd.get("limit_per_sub", 50)),
#             "--out","data/raw/reddit.csv"]
#     if not mock:
#         args += ["--client_id", rd.get("client_id",""), "--client_secret", rd.get("client_secret",""),
#                  "--user_agent", rd.get("user_agent","political-pulse/0.1")]
#     else:
#         args.append("--mock")
#     sh(args)
#
#     # Clean
#     sh(["sys.executable","etl/clean_text.py","--raw_dir","data/raw","--out","data/processed/items.csv"])
#
#     # Sentiment
#     sh(["sys.executable","analysis/sentiment_analysis.py","--in","data/processed/items.csv",
#         "--out","data/processed/items_with_sentiment.csv"])
#
#     # Topic classify
#     sh(["sys.executable","analysis/topic_classifier.py","--in","data/processed/items_with_sentiment.csv",
#         "--out","data/processed/items_enriched.csv"])
#
#     print("\nETL complete. Processed file: data/processed/items_enriched.csv")
#
# if __name__ == "__main__":
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--mock", action="store_true")
#     args = ap.parse_args()
#     if not os.path.exists("config.yaml"):
#         print("config.yaml not found. Copy config.example.yaml to config.yaml and edit.")
#         sys.exit(1)
#     main(mock=args.mock)
"""
One-command ETL orchestrator.
Usage:
  python run_etl.py          # live mode (requires creds)
  python run_etl.py --mock   # generates demo data
"""
import argparse, yaml, os, subprocess, sys

def sh(cmd):
    print("[cmd]", " ".join(cmd))
    subprocess.check_call(cmd)

def main(mock=False):
    with open("config.yaml", "r") as f:
        cfg = yaml.safe_load(f)

    # --- Google Trends ---
    gt = cfg.get("google_trends", {})
    kw = gt.get("kw_list", ["economy", "crime", "immigration", "healthcare", "education"])
    args = [sys.executable, "etl/fetch_google_trends.py",
            "--keywords", *kw,
            "--geo", gt.get("geo", "US"),
            "--timeframe", gt.get("timeframe", "now 7-d"),
            "--out", "data/raw/google_trends.csv"]
    if mock: args.append("--mock")
    sh(args)

    # --- Google Trends by region ---
    args = [sys.executable, "etl/fetch_google_trends_regions.py",
            "--keywords", *kw,
            "--out", "data/raw/google_trends_regions.csv"]
    if mock: args.append("--mock")
    sh(args)

    # --- Reddit ---
    rd = cfg.get("reddit", {})
    subs = rd.get("subreddits", ["politics"])
    args = [sys.executable, "etl/fetch_reddit.py",
            "--subs", *subs,
            "--limit", str(rd.get("limit_per_sub", 50)),
            "--out", "data/raw/reddit.csv"]
    if not mock:
        args += ["--client_id", rd.get("client_id", ""),
                 "--client_secret", rd.get("client_secret", ""),
                 "--user_agent", rd.get("user_agent", "political-pulse/0.1")]
    else:
        args.append("--mock")
    sh(args)

    # --- Clean text ---
    sh([sys.executable, "etl/clean_text.py",
        "--raw_dir", "data/raw",
        "--out", "data/processed/items.csv"])

    # --- Sentiment ---
    sh([sys.executable, "analysis/sentiment_analysis.py",
        "--in", "data/processed/items.csv",
        "--out", "data/processed/items_with_sentiment.csv"])

    # --- Topic classification ---
    sh([sys.executable, "analysis/topic_classifier.py",
        "--in", "data/processed/items_with_sentiment.csv",
        "--out", "data/processed/items_enriched.csv"])

    print("\nETL complete. Processed file: data/processed/items_enriched.csv")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    if not os.path.exists("config.yaml"):
        print("config.yaml not found. Copy config.example.yaml to config.yaml and edit.")
        sys.exit(1)
    main(mock=args.mock)
