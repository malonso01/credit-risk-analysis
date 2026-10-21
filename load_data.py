import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql+psycopg2://postgres:PASSWORD@127.0.0.1/credit_risk')

COLUMNS = [
    'id', 'loan_amnt', 'funded_amnt', 'int_rate', 'installment',
    'grade', 'sub_grade', 'emp_length', 'home_ownership', 'annual_inc',
    'loan_status', 'purpose', 'addr_state', 'dti',
    'fico_range_low', 'fico_range_high', 'open_acc', 'pub_rec',
    'revol_bal', 'revol_util', 'total_acc', 'issue_d', 'term'
]

print("Cargando datos...")
df = pd.read_csv(
    'accepted_2007_to_2018Q4.csv.gz',
    compression='gzip',
    low_memory=False,
    usecols=COLUMNS
)

print(f"Filas: {len(df):,}")
print("Subiendo a PostgreSQL...")

df.to_sql('loans', engine, if_exists='replace', index=False, chunksize=5000)
print("Listo! Tabla 'loans' creada.")