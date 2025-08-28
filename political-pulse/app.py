# """
# Combine raw sources into a single items.csv with harmonized columns.
# Adds simple locality and dedupe heuristics.
# """
# import argparse, os, pandas as pd, hashlib
#
# def hash_row(row):
#     s = f"{row.get('source','')}|{row.get('title','')}|{row.get('date','') or row.get('created_utc','')}"
#     return hashlib.md5(s.encode()).hexdigest()
#
# def main(raw_dir, out_csv):
#     os.makedirs(os.path.dirname(out_csv), exist_ok=True)
#     frames = []
#     # Google Trends
#     gt_path = os.path.join(raw_dir, "google_trends.csv")
#     if os.path.exists(gt_path):
#         g = pd.read_csv(gt_path)
#         g['title'] = g['keyword'].astype(str) + " – interest " + g['value'].astype(str)
#         g['created_utc'] = g['date']
#         g['url'] = ""
#         g['issue'] = g['keyword']
#         frames.append(g[['source','title','url','created_utc','issue']])
#     # Reddit
#     rd_path = os.path.join(raw_dir, "reddit.csv")
#     if os.path.exists(rd_path):
#         r = pd.read_csv(rd_path)
#         frames.append(r[['source','title','url','created_utc','issue']])
#     if not frames:
#         print("No raw files found.")
#         return
#     df = pd.concat(frames, ignore_index=True)
#     df['item_id'] = df.apply(hash_row, axis=1)
#     df = df.drop_duplicates(subset=['item_id'])
#     df.to_csv(out_csv, index=False)
#     print(f"[clean] wrote -> {out_csv} ({len(df)} rows)")
#
# if __name__ == "__main__":
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--raw_dir", default="data/raw")
#     ap.add_argument("--out", default="data/processed/items.csv")
#     args = ap.parse_args()
#     main(args.raw_dir, args.out)
# app.py — Flask UI only
from flask import Flask, render_template_string, jsonify
import pandas as pd
import os

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Political Pulse – Demo</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">

  <style>
    body { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    .card { border-radius: 1rem; box-shadow: 0 6px 20px rgba(0,0,0,.06); }
    .metric { font-size: 1.5rem; font-weight: 600; }
    .subtle { color: #6c757d; }
  </style>
</head>
<body class="bg-light">
<div class="container py-4">

  <h1 class="mb-3">Political Pulse – Interactive Demo</h1>
  <p class="subtle mb-4">Data from Google Trends + Reddit titles. Use filters to explore.</p>

  <div class="card mb-4 p-3">
    <div class="row g-3">
      <div class="col-md-3">
        <label class="form-label">Issue</label>
        <select id="issueFilter" class="form-select">
          <option value="">All</option>
        </select>
      </div>
      <div class="col-md-3">
        <label class="form-label">Subreddit</label>
        <select id="subFilter" class="form-select">
          <option value="">All</option>
        </select>
      </div>
      <div class="col-md-3 align-self-end">
        <button id="resetBtn" class="btn btn-outline-secondary w-100">Reset Filters</button>
      </div>
    </div>
  </div>

  <div class="row g-4 mb-2">
    <div class="col-md-4">
      <div class="card p-3">
        <div class="subtle">Items (last 7 days)</div>
        <div id="metricItems" class="metric">–</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card p-3">
        <div class="subtle">Unique Issues</div>
        <div id="metricIssues" class="metric">–</div>
      </div>
    </div>
    <div class="col-md-4">
      <div class="card p-3">
        <div class="subtle">Avg Sentiment</div>
        <div id="metricSent" class="metric">–</div>
      </div>
    </div>
  </div>

  <div class="row g-4 mb-4">
    <div class="col-lg-6">
      <div class="card p-3">
        <h5 class="mb-3">Top Issues by Volume</h5>
        <canvas id="barIssues"></canvas>
      </div>
    </div>
    <div class="col-lg-6">
      <div class="card p-3">
        <h5 class="mb-3">Avg Sentiment by Issue</h5>
        <canvas id="barSentiment"></canvas>
      </div>
    </div>
  </div>

  <div class="card p-3 mb-4">
    <h5 class="mb-3">Google Trends (last 7 days)</h5>
    <canvas id="lineTrends"></canvas>
  </div>

  <div class="card p-3">
    <h5 class="mb-3">Latest Items</h5>
    <table id="itemsTable" class="table table-striped" style="width:100%">
      <thead>
        <tr>
          <th>Created</th>
          <th>Title</th>
          <th>Issue</th>
          <th>Subreddit</th>
          <th>Sentiment</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>

<script>
let table, chartIssues, chartSent, chartTrends;
let rawData = [], trends = [];
let currentIssue = "", currentSub = "";

async function loadData() {
  const r1 = await fetch('/api/items');
  rawData = await r1.json();
  const r2 = await fetch('/api/trends');
  trends = await r2.json();
  initFilters();
  renderMetrics();
  renderCharts();
  renderTable();
}

function initFilters() {
  const issues = Array.from(new Set(rawData.map(d => d.issue_final).filter(Boolean))).sort();
  const subs = Array.from(new Set(rawData.map(d => d.subreddit || "").filter(Boolean))).sort();
  const issueSel = document.getElementById('issueFilter');
  const subSel = document.getElementById('subFilter');
  for (const it of issues) {
    const o = document.createElement('option'); o.value = it; o.textContent = it;
    issueSel.appendChild(o);
  }
  for (const s of subs) {
    const o = document.createElement('option'); o.value = s; o.textContent = s;
    subSel.appendChild(o);
  }
  issueSel.addEventListener('change', e => { currentIssue = e.target.value; applyFilters(); });
  subSel.addEventListener('change', e => { currentSub = e.target.value; applyFilters(); });
  document.getElementById('resetBtn').addEventListener('click', () => {
    currentIssue = ""; currentSub = "";
    issueSel.value = ""; subSel.value = "";
    applyFilters();
  });
}

function filtered() {
  return rawData.filter(d =>
    (!currentIssue || d.issue_final === currentIssue) &&
    (!currentSub || (d.subreddit || "") === currentSub)
  );
}

function renderMetrics() {
  const rows = filtered();
  document.getElementById('metricItems').textContent = rows.length.toString();
  document.getElementById('metricIssues').textContent =
    new Set(rows.map(d => d.issue_final)).size.toString();
  if (rows.length) {
    const avg = rows.reduce((a,b)=>a + (b.sentiment||0), 0) / rows.length;
    document.getElementById('metricSent').textContent = avg.toFixed(2);
  } else {
    document.getElementById('metricSent').textContent = "–";
  }
}

function renderCharts() {
  const rows = filtered();

  // Top issues by volume
  const counts = {};
  for (const r of rows) counts[r.issue_final] = (counts[r.issue_final]||0)+1;
  const labels1 = Object.keys(counts);
  const data1 = labels1.map(k => counts[k]);
  if (chartIssues) chartIssues.destroy();
  chartIssues = new Chart(document.getElementById('barIssues'), {
    type: 'bar',
    data: { labels: labels1, datasets: [{ label: 'Count', data: data1 }] },
    options: { responsive: true, plugins: { legend: { display: false } } }
  });

  // Avg sentiment by issue
  const sums = {}, nums = {};
  for (const r of rows) {
    sums[r.issue_final] = (sums[r.issue_final]||0) + (r.sentiment||0);
    nums[r.issue_final] = (nums[r.issue_final]||0) + 1;
  }
  const labels2 = Object.keys(nums);
  const data2 = labels2.map(k => (sums[k]/nums[k]).toFixed(3));
  if (chartSent) chartSent.destroy();
  chartSent = new Chart(document.getElementById('barSentiment'), {
    type: 'bar',
    data: { labels: labels2, datasets: [{ label: 'Avg sentiment', data: data2 }] },
    options: { responsive: true, plugins: { legend: { display: false } } }
  });

  // Google Trends line chart
  const byDate = {};
  for (const t of trends) {
    const key = t.date;
    byDate[key] = byDate[key] || {};
    byDate[key][t.keyword] = t.value;
  }
  const dates = Object.keys(byDate).sort();
  const keywords = Array.from(new Set(trends.map(t => t.keyword))).sort();

  const datasets = keywords.map(kw => ({
    label: kw,
    data: dates.map(d => byDate[d][kw] ?? null)
  }));

  if (chartTrends) chartTrends.destroy();
  chartTrends = new Chart(document.getElementById('lineTrends'), {
    type: 'line',
    data: { labels: dates, datasets },
    options: { responsive: true }
  });
}

function renderTable() {
  const rows = filtered();
  const tbody = document.querySelector('#itemsTable tbody');
  tbody.innerHTML = "";
  for (const r of rows.slice(0, 200)) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.created_utc || ""}</td>
      <td>${r.url ? `<a href="${r.url}" target="_blank">${escapeHtml(r.title||"")}</a>` : escapeHtml(r.title||"")}</td>
      <td>${r.issue_final||""}</td>
      <td>${r.subreddit||""}</td>
      <td>${(r.sentiment ?? "").toFixed ? r.sentiment.toFixed(2) : r.sentiment}</td>`;
    tbody.appendChild(tr);
  }
  if (table) { table.clear(); table.destroy(); }
  table = new $.fn.dataTable.Api($('#itemsTable').DataTable({ pageLength: 10 }));
}

function applyFilters() {
  renderMetrics();
  renderCharts();
  renderTable();
}

function escapeHtml(s) {
  return (s||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}

loadData();
</script>

</body>
</html>
"""

def _safe_read_csv(path, required_cols):
    if not os.path.exists(path):
        return pd.DataFrame(columns=required_cols)
    df = pd.read_csv(path)
    for c in required_cols:
        if c not in df.columns:
            df[c] = "" if c != "sentiment" else 0.0
    return df[required_cols]

def read_items():
    # Primary file produced by the ETL pipeline:
    p1 = "data/processed/items_enriched.csv"
    # Fallbacks so the UI can still show *something* during setup:
    p2 = "data/processed/items_with_sentiment.csv"
    p3 = "data/processed/items.csv"

    if os.path.exists(p1):
        df = _safe_read_csv(p1, ["created_utc","title","url","issue_final","subreddit","sentiment"])
    elif os.path.exists(p2):
        df = _safe_read_csv(p2, ["created_utc","title","url","issue_final","subreddit","sentiment"])
        if "issue_final" not in df.columns:
            df["issue_final"] = ""
    else:
        df = _safe_read_csv(p3, ["created_utc","title","url","issue_final","subreddit","sentiment"])
        if "issue_final" not in df.columns:
            df["issue_final"] = ""

    return df.fillna("").to_dict(orient="records")

def read_trends():
    path = "data/raw/google_trends.csv"
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    need = ["keyword","date","value"]
    for c in need:
        if c not in df.columns:
            return []
    return df[need].fillna(0).to_dict(orient="records")

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/items")
def api_items():
    return jsonify(read_items())

@app.route("/api/trends")
def api_trends():
    return jsonify(read_trends())

if __name__ == "__main__":
    # Run from project root so relative paths resolve.
    app.run(debug=True, port=5001)
