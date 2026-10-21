import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sqlalchemy import create_engine

engine = create_engine('postgresql+psycopg2://postgres:Cogolludo01@127.0.0.1/credit_risk')

# --- Query 1: Default rate by grade ---
q1 = """
WITH grade_summary AS (
    SELECT grade,
        COUNT(*) FILTER (WHERE loan_status = 'Charged Off') AS charged_off,
        COUNT(*) FILTER (WHERE loan_status = 'Fully Paid') AS fully_paid,
        ROUND(AVG(int_rate::numeric), 2) AS avg_rate
    FROM loans WHERE grade IS NOT NULL
    GROUP BY grade
)
SELECT grade,
    ROUND(charged_off * 100.0 / NULLIF(charged_off + fully_paid, 0), 2) AS default_rate,
    avg_rate
FROM grade_summary ORDER BY grade;
"""

# --- Query 2: FICO segmentation ---
q2 = """
SELECT
    CASE
        WHEN fico_range_low >= 800 THEN '800+ Exceptional'
        WHEN fico_range_low >= 740 THEN '740-799 Very Good'
        WHEN fico_range_low >= 670 THEN '670-739 Good'
        WHEN fico_range_low >= 580 THEN '580-669 Fair'
        ELSE 'Below 580 Poor'
    END AS fico_segment,
    ROUND(COUNT(*) FILTER (WHERE loan_status = 'Charged Off') * 100.0 / COUNT(*), 2) AS default_rate,
    ROUND(AVG(int_rate::numeric), 2) AS avg_rate,
    COUNT(*) AS total_loans
FROM loans WHERE fico_range_low IS NOT NULL
GROUP BY fico_segment ORDER BY MIN(fico_range_low) DESC;
"""

# --- Query 3: YoY loan volume ---
q3 = """
SELECT RIGHT(issue_d, 4) AS year,
       COUNT(*) AS loans,
       ROUND(SUM(loan_amnt::numeric) / 1000000000.0, 3) AS volume
FROM loans WHERE issue_d IS NOT NULL
GROUP BY RIGHT(issue_d, 4)
HAVING RIGHT(issue_d, 4) ~ '^[0-9]{4}$'
ORDER BY year;
"""

df1 = pd.read_sql(q1, engine)
df2 = pd.read_sql(q2, engine)
df3 = pd.read_sql(q3, engine)

# --- Plot ---
fig = plt.figure(figsize=(16, 12))
fig.suptitle('Lending Club Credit Risk Analysis (2007-2018)\n2.26M Loans',
             fontsize=16, fontweight='bold', y=0.98)

gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

colors_grade = ['#2ecc71', '#27ae60', '#f39c12', '#e67e22', '#e74c3c', '#c0392b', '#8e44ad']

# Chart 1: Default rate by grade
ax1 = fig.add_subplot(gs[0, 0])
bars = ax1.bar(df1['grade'], df1['default_rate'].astype(float), color=colors_grade)
ax1.set_title('Default Rate by Credit Grade', fontweight='bold')
ax1.set_xlabel('Grade')
ax1.set_ylabel('Default Rate (%)')
for bar, val in zip(bars, df1['default_rate'].astype(float)):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
             f'{val}%', ha='center', va='bottom', fontsize=9)

# Chart 2: Interest rate vs default rate
ax2 = fig.add_subplot(gs[0, 1])
ax2.scatter(df1['avg_rate'].astype(float), df1['default_rate'].astype(float),
            color=colors_grade, s=200, zorder=5)
for _, row in df1.iterrows():
    ax2.annotate(row['grade'], (float(row['avg_rate']), float(row['default_rate'])),
                 textcoords='offset points', xytext=(8, 4), fontsize=10, fontweight='bold')
ax2.set_title('Interest Rate vs Default Rate by Grade', fontweight='bold')
ax2.set_xlabel('Avg Interest Rate (%)')
ax2.set_ylabel('Default Rate (%)')
ax2.grid(True, alpha=0.3)

# Chart 3: FICO default rate
ax3 = fig.add_subplot(gs[1, 0])
fico_order = ['800+ Exceptional', '740-799 Very Good', '670-739 Good', '580-669 Fair', 'Below 580 Poor']
df2['fico_segment'] = pd.Categorical(df2['fico_segment'], categories=fico_order, ordered=True)
df2 = df2.sort_values('fico_segment')
colors_fico = ['#2ecc71', '#27ae60', '#f39c12', '#e74c3c', '#8e44ad']
bars3 = ax3.bar(range(len(df2)), df2['default_rate'].astype(float), color=colors_fico)
ax3.set_xticks(range(len(df2)))
ax3.set_xticklabels([s.split(' ')[0] for s in df2['fico_segment']], rotation=15)
ax3.set_title('Default Rate by FICO Score Segment', fontweight='bold')
ax3.set_ylabel('Default Rate (%)')
for bar, val in zip(bars3, df2['default_rate'].astype(float)):
    ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
             f'{val}%', ha='center', va='bottom', fontsize=9)

# Chart 4: Loan volume by year
ax4 = fig.add_subplot(gs[1, 1])
df3_clean = df3.copy()
x_pos = list(range(len(df3_clean)))
y_vals = [float(v) for v in df3_clean['volume'].tolist()]
ax4.bar(x_pos, y_vals, color='#3498db', alpha=0.7)
ax4.plot(x_pos, y_vals, color='#2980b9', linewidth=2, marker='o')
ax4.set_xticks(x_pos)
ax4.set_xticklabels(df3_clean['year'].tolist(), rotation=45)
ax4.set_title('Total Loan Volume by Year ($B)', fontweight='bold')
ax4.set_xlabel('Year')
ax4.set_ylabel('Volume ($ Billions)')
ax4.grid(True, alpha=0.3)

plt.savefig('dashboard.png', dpi=150, bbox_inches='tight')
print("Dashboard guardado: dashboard.png")
plt.show()