"""
analysis.py
-----------
Loads the claims CSV into an in-memory SQLite database, runs the queries
from sql/analysis.sql, prints the results, and saves three charts.

This shows two skills at once: SQL (the queries) and Python (orchestrating
the analysis and visualizing it) -- exactly the combo revenue cycle /
healthcare data analyst roles ask for.

Run:  python analysis.py
"""

import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # render charts to file without a display
import matplotlib.pyplot as plt

# Simple, clean chart styling
plt.rcParams.update({
    "figure.dpi": 130, "font.size": 11, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
})
TEAL, CORAL = "#0E7C7B", "#E8615D"

# 1. Load the data into SQLite so we can query it with real SQL
df = pd.read_csv("data/claims.csv")
conn = sqlite3.connect(":memory:")
df.to_sql("claims", conn, index=False, if_exists="replace")


def run(sql):
    """Run a SQL string and return the result as a DataFrame."""
    return pd.read_sql_query(sql, conn)


# ---- Q1: headline numbers -------------------------------------------------
overall = run("""
    SELECT COUNT(*) AS total_claims,
           SUM(claim_status='Denied') AS denied_claims,
           ROUND(100.0*SUM(claim_status='Denied')/COUNT(*),1) AS denial_rate_pct,
           ROUND(SUM(CASE WHEN claim_status='Denied' THEN billed_amount END),0) AS denied_dollars
    FROM claims;
""")
print("\n=== Headline ===")
print(overall.to_string(index=False))

# ---- Q2: denial rate by payer --------------------------------------------
by_payer = run("""
    SELECT payer,
           ROUND(100.0*SUM(claim_status='Denied')/COUNT(*),1) AS denial_rate_pct
    FROM claims GROUP BY payer ORDER BY denial_rate_pct DESC;
""")
print("\n=== Denial rate by payer ===")
print(by_payer.to_string(index=False))

# ---- Q3: top denial reasons by dollars -----------------------------------
by_reason = run("""
    SELECT denial_code || ' - ' || denial_description AS reason,
           ROUND(SUM(billed_amount),0) AS dollars_denied
    FROM claims WHERE claim_status='Denied'
    GROUP BY reason ORDER BY dollars_denied DESC;
""")

# ---- Q5: monthly trend ----------------------------------------------------
trend = run("""
    SELECT substr(date_of_service,1,7) AS month,
           ROUND(SUM(CASE WHEN claim_status='Denied' THEN billed_amount END),0) AS denied_dollars
    FROM claims GROUP BY month ORDER BY month;
""")

# ---- Q6: recoverable vs hard ---------------------------------------------
recover = run("""
    SELECT CASE WHEN recoverable='Yes' THEN 'Recoverable' ELSE 'Hard denial' END AS denial_type,
           ROUND(SUM(billed_amount),0) AS dollars
    FROM claims WHERE claim_status='Denied' GROUP BY denial_type ORDER BY dollars DESC;
""")
print("\n=== Recoverable opportunity ===")
print(recover.to_string(index=False))

# ==========================================================================
# Charts
# ==========================================================================
# Chart 1: denial rate by payer
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(by_payer["payer"], by_payer["denial_rate_pct"], color=TEAL)
ax.set_title("Denial Rate by Payer")
ax.set_ylabel("Denial rate (%)")
plt.xticks(rotation=30, ha="right")
plt.tight_layout(); plt.savefig("charts/denial_rate_by_payer.png"); plt.close()

# Chart 2: top denial reasons by dollars
fig, ax = plt.subplots(figsize=(7, 4))
top = by_reason.head(6).iloc[::-1]
ax.barh(top["reason"], top["dollars_denied"], color=CORAL)
ax.set_title("Top Denial Reasons by Dollars Denied")
ax.set_xlabel("Dollars denied ($)")
plt.tight_layout(); plt.savefig("charts/top_denial_reasons.png"); plt.close()

# Chart 3: monthly denied-dollar trend
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(trend["month"], trend["denied_dollars"], marker="o", color=TEAL)
ax.set_title("Denied Dollars by Month")
ax.set_ylabel("Dollars denied ($)")
plt.xticks(rotation=45, ha="right")
plt.tight_layout(); plt.savefig("charts/monthly_trend.png"); plt.close()

print("\nSaved 3 charts to charts/")
conn.close()
