"""
generate_data.py
-----------------
Creates a realistic *simulated* hospital claims dataset for the
Revenue Cycle Denials analysis project.

The data is synthetic (no real patients), but it is modeled on the real
structure of professional/institutional claims and uses real CARC
(Claim Adjustment Reason Codes) denial reasons so the analysis mirrors
what a working revenue cycle analyst actually sees.

Run:  python data/generate_data.py
Out:  data/claims.csv
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)  # fixed seed -> anyone who runs this gets the same data
N = 6000                          # number of claims

# ----------------------------------------------------------------------
# Reference values (weights reflect a typical mid-size hospital payer mix)
# ----------------------------------------------------------------------
payers = ["Medicare", "Medicaid", "BCBS", "UnitedHealthcare", "Aetna", "Cigna", "Self-Pay"]
payer_weights = [0.30, 0.18, 0.16, 0.13, 0.10, 0.08, 0.05]

service_lines = ["Emergency", "Cardiology", "Orthopedics", "Radiology", "Laboratory", "Surgery", "Behavioral Health"]
service_weights = [0.24, 0.14, 0.13, 0.16, 0.12, 0.13, 0.08]

# Real CARC codes -> (description, denial category, is_recoverable)
# Recoverable = often fixable/appealable (soft denial). Hard = usually a write-off.
denial_reasons = {
    "CO-16":  ("Claim lacks information or has billing error", "Missing Information", True),
    "CO-197": ("Precertification/authorization absent",        "Authorization",       True),
    "CO-50":  ("Not deemed medically necessary",               "Medical Necessity",   True),
    "CO-29":  ("Time limit for filing has expired",            "Timely Filing",       False),
    "CO-18":  ("Duplicate claim or service",                   "Duplicate",           False),
    "CO-96":  ("Non-covered charge(s)",                        "Non-Covered",         False),
    "CO-27":  ("Coverage expired / patient ineligible",        "Eligibility",         True),
    "CO-4":   ("Procedure code inconsistent with modifier",    "Coding",              True),
}
reason_codes = list(denial_reasons.keys())
# Frequency weights for which denial reason occurs (Missing Info & Auth dominate in reality)
reason_weights = [0.26, 0.22, 0.14, 0.08, 0.07, 0.09, 0.07, 0.07]

# ----------------------------------------------------------------------
# Build the claims
# ----------------------------------------------------------------------
service_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
    rng.integers(0, 365, size=N), unit="D"
)

payer = rng.choice(payers, size=N, p=payer_weights)
service_line = rng.choice(service_lines, size=N, p=service_weights)

# Billed amount depends on service line (surgery costs more than a lab)
base_by_line = {
    "Emergency": 2400, "Cardiology": 5200, "Orthopedics": 6800, "Radiology": 1300,
    "Laboratory": 350, "Surgery": 9500, "Behavioral Health": 1800,
}
billed = np.array([
    max(40, rng.normal(base_by_line[s], base_by_line[s] * 0.35)) for s in service_line
]).round(2)

# Denial probability varies by payer (Self-Pay & Medicaid deny/adjust more often)
payer_denial_rate = {
    "Medicare": 0.09, "Medicaid": 0.17, "BCBS": 0.11, "UnitedHealthcare": 0.15,
    "Aetna": 0.12, "Cigna": 0.13, "Self-Pay": 0.22,
}
denial_prob = np.array([payer_denial_rate[p] for p in payer])
is_denied = rng.random(N) < denial_prob

# Assign denial details only to denied claims
reason = np.where(
    is_denied,
    rng.choice(reason_codes, size=N, p=reason_weights),
    "",
)

claim_status = np.where(is_denied, "Denied", "Paid")
allowed = np.where(is_denied, 0.0, (billed * rng.uniform(0.45, 0.85, size=N)).round(2))

df = pd.DataFrame({
    "claim_id": [f"CLM{100000 + i}" for i in range(N)],
    "date_of_service": service_dates.strftime("%Y-%m-%d"),
    "payer": payer,
    "service_line": service_line,
    "billed_amount": billed,
    "allowed_amount": allowed,
    "claim_status": claim_status,
    "denial_code": reason,
})

# Expand denial code into description / category / recoverable flag
df["denial_description"] = df["denial_code"].map(lambda c: denial_reasons[c][0] if c else "")
df["denial_category"]    = df["denial_code"].map(lambda c: denial_reasons[c][1] if c else "")
df["recoverable"]        = df["denial_code"].map(lambda c: ("Yes" if denial_reasons[c][2] else "No") if c else "")

df.to_csv("data/claims.csv", index=False)
print(f"Wrote data/claims.csv  ({len(df):,} claims, {is_denied.sum():,} denied)")
