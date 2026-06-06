-- ============================================================
--  Revenue Cycle Denials -- SQL Analysis
--  Each query answers one business question a revenue cycle
--  analyst would be asked in a real job.
--  Table: claims  (one row per submitted claim)
-- ============================================================


-- Q1.  What is our overall denial rate, and how much money is tied up?
--      COUNT(*) counts rows. The CASE WHEN ... counts only denied rows.
--      Multiplying by 100.0 turns the ratio into a percentage.
SELECT
    COUNT(*)                                              AS total_claims,
    SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
    ROUND(
        100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*),
        1
    )                                                     AS denial_rate_pct,
    ROUND(SUM(CASE WHEN claim_status = 'Denied' THEN billed_amount ELSE 0 END), 0)
                                                          AS denied_dollars
FROM claims;


-- Q2.  Which payers deny the most? (Where should we focus payer outreach?)
--      GROUP BY collapses all rows for each payer into one summary row.
--      ORDER BY ... DESC puts the worst offenders on top.
SELECT
    payer,
    COUNT(*)                                              AS claims,
    SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied,
    ROUND(
        100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*),
        1
    )                                                     AS denial_rate_pct
FROM claims
GROUP BY payer
ORDER BY denial_rate_pct DESC;


-- Q3.  What are the top denial reasons by DOLLAR impact?
--      We only look at denied rows (WHERE), group by the reason,
--      and rank by how many dollars each reason represents.
SELECT
    denial_code,
    denial_description,
    denial_category,
    COUNT(*)                          AS times_denied,
    ROUND(SUM(billed_amount), 0)      AS dollars_denied
FROM claims
WHERE claim_status = 'Denied'
GROUP BY denial_code, denial_description, denial_category
ORDER BY dollars_denied DESC;


-- Q4.  Which service lines have the worst denial rates?
SELECT
    service_line,
    COUNT(*)                                              AS claims,
    ROUND(
        100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*),
        1
    )                                                     AS denial_rate_pct
FROM claims
GROUP BY service_line
ORDER BY denial_rate_pct DESC;


-- Q5.  How are denials trending month over month?
--      substr() pulls 'YYYY-MM' out of the date so we can group by month.
SELECT
    substr(date_of_service, 1, 7)                         AS month,
    SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied_claims,
    ROUND(SUM(CASE WHEN claim_status = 'Denied' THEN billed_amount ELSE 0 END), 0)
                                                          AS denied_dollars
FROM claims
GROUP BY month
ORDER BY month;


-- Q6.  How much of the denied money is RECOVERABLE? (the headline finding)
--      Recoverable denials are fixable/appealable -- real money we can win back.
SELECT
    CASE WHEN recoverable = 'Yes' THEN 'Recoverable (appealable)'
         ELSE 'Hard denial (write-off)' END              AS denial_type,
    COUNT(*)                                              AS claims,
    ROUND(SUM(billed_amount), 0)                          AS dollars
FROM claims
WHERE claim_status = 'Denied'
GROUP BY denial_type
ORDER BY dollars DESC;
