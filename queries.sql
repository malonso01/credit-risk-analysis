-- ============================================
-- CREDIT RISK ANALYSIS - Advanced SQL Queries
-- ============================================

-- 1. RISK DISTRIBUTION BY GRADE (CTE + aggregation)
WITH grade_summary AS (
    SELECT
        grade,
        COUNT(*) AS total_loans,
        ROUND(AVG(loan_amnt)::numeric, 2) AS avg_loan_amount,
        ROUND(AVG(int_rate::numeric), 2) AS avg_interest_rate,
        ROUND(AVG(dti::numeric), 2) AS avg_dti,
        COUNT(*) FILTER (WHERE loan_status = 'Charged Off') AS charged_off,
        COUNT(*) FILTER (WHERE loan_status = 'Fully Paid') AS fully_paid
    FROM loans
    WHERE grade IS NOT NULL
    GROUP BY grade
)
SELECT
    grade,
    total_loans,
    avg_loan_amount,
    avg_interest_rate,
    avg_dti,
    charged_off,
    fully_paid,
    ROUND(charged_off * 100.0 / NULLIF(charged_off + fully_paid, 0), 2) AS default_rate_pct
FROM grade_summary
ORDER BY grade;


-- 2. WINDOW FUNCTION: Cumulative loan volume by issue year
SELECT
    LEFT(issue_d, 4) AS year,
    grade,
    COUNT(*) AS loans_issued,
    SUM(loan_amnt) AS total_volume,
    SUM(SUM(loan_amnt)) OVER (
        PARTITION BY grade
        ORDER BY LEFT(issue_d, 4)
    ) AS cumulative_volume_by_grade
FROM loans
WHERE issue_d IS NOT NULL AND grade IS NOT NULL
GROUP BY LEFT(issue_d, 4), grade
ORDER BY year, grade;


-- 3. WINDOW FUNCTION: Ranking states by default rate
WITH state_risk AS (
    SELECT
        addr_state,
        COUNT(*) AS total_loans,
        COUNT(*) FILTER (WHERE loan_status = 'Charged Off') AS defaults,
        ROUND(AVG(int_rate::numeric), 2) AS avg_rate
    FROM loans
    WHERE addr_state IS NOT NULL
    GROUP BY addr_state
    HAVING COUNT(*) > 500
),
ranked AS (
    SELECT
        addr_state,
        total_loans,
        defaults,
        avg_rate,
        ROUND(defaults * 100.0 / total_loans, 2) AS default_rate_pct,
        RANK() OVER (ORDER BY defaults * 100.0 / total_loans DESC) AS risk_rank
    FROM state_risk
)
SELECT * FROM ranked
ORDER BY risk_rank
LIMIT 20;


-- 4. WINDOW FUNCTION: LAG - YoY change in average loan amount
WITH yearly AS (
    SELECT
        LEFT(issue_d, 4) AS year,
        ROUND(AVG(loan_amnt)::numeric, 2) AS avg_loan
    FROM loans
    WHERE issue_d IS NOT NULL
    GROUP BY LEFT(issue_d, 4)
)
SELECT
    year,
    avg_loan,
    LAG(avg_loan) OVER (ORDER BY year) AS prev_year_avg,
    ROUND(avg_loan - LAG(avg_loan) OVER (ORDER BY year), 2) AS yoy_change,
    ROUND(
        (avg_loan - LAG(avg_loan) OVER (ORDER BY year)) * 100.0
        / NULLIF(LAG(avg_loan) OVER (ORDER BY year), 0), 2
    ) AS yoy_pct_change
FROM yearly
ORDER BY year;


-- 5. FICO SCORE SEGMENTATION + default rate (CASE + GROUP BY)
SELECT
    CASE
        WHEN fico_range_low >= 800 THEN '800+ Exceptional'
        WHEN fico_range_low >= 740 THEN '740-799 Very Good'
        WHEN fico_range_low >= 670 THEN '670-739 Good'
        WHEN fico_range_low >= 580 THEN '580-669 Fair'
        ELSE 'Below 580 Poor'
    END AS fico_segment,
    COUNT(*) AS total_loans,
    ROUND(AVG(int_rate::numeric), 2) AS avg_interest_rate,
    ROUND(AVG(loan_amnt)::numeric, 2) AS avg_loan_amount,
    ROUND(
        COUNT(*) FILTER (WHERE loan_status = 'Charged Off') * 100.0 / COUNT(*), 2
    ) AS default_rate_pct
FROM loans
WHERE fico_range_low IS NOT NULL
GROUP BY fico_segment
ORDER BY MIN(fico_range_low) DESC;