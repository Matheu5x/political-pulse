"""
Read processed CSVs and generate a simple PDF report.
"""
import argparse, os, pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def summarize(df):
    # volume by issue
    vol = df['issue_final'].value_counts().rename_axis('issue').reset_index(name='count')
    # sentiment by issue
    sent = df.groupby('issue_final')['sentiment'].mean().reset_index()
    return vol, sent

def table_from_df(df):
    data = [list(df.columns)] + df.values.tolist()
    t = Table(data, hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey),
                           ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                           ('ALIGN',(0,0),(-1,-1),'CENTER'),
                           ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                           ('BOTTOMPADDING', (0,0), (-1,0), 12),
                           ('BACKGROUND',(0,1),(-1,-1),colors.beige)]))
    return t

def main(week_label, processed_csv, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(processed_csv)
    vol, sent = summarize(df)
    pdf_path = os.path.join(out_dir, f"Weekly_Political_Pulse_Report_{week_label}.pdf")
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(f"<b>Weekly Political Pulse Report</b>", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Week of {week_label}", styles['Normal']))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<b>Top Issues (by volume)</b>", styles['Heading2']))
    elements.append(table_from_df(vol))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Average Sentiment by Issue</b>", styles['Heading2']))
    elements.append(table_from_df(sent.round({'sentiment': 3})))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<b>Notes</b>", styles['Heading2']))
    elements.append(Paragraph("Add executive summary and event triggers here.", styles['Normal']))
    doc = SimpleDocTemplate(pdf_path, pagesize=LETTER)
    doc.build(elements)
    print(f"[report] wrote -> {pdf_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", dest="week_label", default="2025-08-10")
    ap.add_argument("--in", dest="processed_csv", default="data/processed/items_enriched.csv")
    ap.add_argument("--out_dir", default="reports")
    args = ap.parse_args()
    main(args.week_label, args.processed_csv, args.out_dir)
