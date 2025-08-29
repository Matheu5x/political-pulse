# etl/fetch_reddit.py
import argparse
from datetime import datetime, timedelta
import os
import random
import pandas as pd

try:
    import praw
except Exception as e:
    praw = None

# --- simple keyword-based issue tagger (used only for the 'issue' column) ---
RULES = [
    ("immigration", ["border","migrant","asylum","immigration","deport"]),
    ("economy",     ["inflation","jobs","economy","gdp","wage","growth","unemployment","market"]),
    ("crime",       ["crime","shooting","murder","theft","robbery","police","assault","carjacking"]),
    ("healthcare",  ["healthcare","medicare","medicaid","hospital","drug","insulin","abortion","obamacare"]),
    ("education",   ["school","education","college","student","university","curriculum","k-12","campus"]),
]
def label_issue(title: str) -> str:
    t = (title or "").lower()
    for issue, kws in RULES:
        if any(k in t for k in kws):
            return issue
    return "other"

# --- mock generator for --mock runs ---
def mock_reddit(subreddits, limit_per_sub=30):
    random.seed(7)
    now = datetime.utcnow()
    rows = []
    templates = [
        "Latest {issue} update: {phrase}",
        "{issue} concerns rise: {phrase}",
        "{issue} policy debate: {phrase}",
        "Report: {phrase} affects {issue}",
    ]
    phrases = [
        "new poll shows shifting views",
        "experts warn of long-term impact",
        "local leaders respond",
        "committee schedules hearing",
        "data suggests regional differences"
    ]
    issues = [i for i, _ in RULES] + ["other"]

    for sub in subreddits:
        for i in range(limit_per_sub):
            issue = random.choice(issues)
            title = random.choice(templates).format(issue=issue, phrase=random.choice(phrases))
            ts = (now - timedelta(hours=random.randint(0, 168))).isoformat()
            rows.append({
                "source": "reddit",
                "subreddit": sub,
                "title": title,
                "url": f"https://reddit.com/r/{sub}/comments/mock{i}",
                "created_utc": ts,
                "issue": issue,
            })
    return pd.DataFrame(rows)

def fetch_reddit(subreddits, limit_per_sub, client_id, client_secret, user_agent,
                 username=None, password=None):
    if praw is None:
        raise RuntimeError("praw not available. Install with `pip install praw` or use --mock.")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password,
    )
    reddit.read_only = True

    rows = []
    for sub in subreddits:
        try:
            for post in reddit.subreddit(sub).new(limit=limit_per_sub):
                rows.append({
                    "source": "reddit",
                    "subreddit": sub,
                    "title": getattr(post, "title", ""),
                    "url": "https://reddit.com" + getattr(post, "permalink", f"/r/{sub}/comments/{getattr(post,'id','')}"),
                    "created_utc": datetime.utcfromtimestamp(getattr(post, "created_utc", datetime.utcnow().timestamp())).isoformat(),
                    "issue": label_issue(getattr(post, "title", "")),
                })
        except Exception as e:
            # Keep the pipeline going even if one subreddit fails
            print(f"[reddit] WARNING: failed to fetch r/{sub}: {e}")
            continue

    return pd.DataFrame(rows)

def main(subreddits, limit_per_sub, out_path, mock, client_id, client_secret, user_agent,
         username=None, password=None):
    if mock:
        df = mock_reddit(subreddits, limit_per_sub)
    else:
        df = fetch_reddit(subreddits, limit_per_sub, client_id, client_secret, user_agent, username, password)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    # Ensure required columns exist (downstream scripts expect these)
    need = ["created_utc","title","url","issue","subreddit"]
    for c in need:
        if c not in df.columns:
            df[c] = ""
    df = df[need]
    df.to_csv(out_path, index=False)
    print(f"[reddit] wrote -> {out_path} ({len(df)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subs", nargs="+", required=True)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--client_id")
    ap.add_argument("--client_secret")
    ap.add_argument("--user_agent")
    ap.add_argument("--username")
    ap.add_argument("--password")
    args = ap.parse_args()

    creds = dict(
        client_id=args.client_id,
        client_secret=args.client_secret,
        user_agent=args.user_agent,
        username=args.username,
        password=args.password,
    )
    main(args.subs, args.limit, args.out, args.mock, **creds)
